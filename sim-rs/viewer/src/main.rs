//! TrackAI en Rust : regarder le bot (`--model`, `--follow`) ou conduire (`--play`), affichage fluide
//! (physique à 50 Hz, image à la fréquence de l'écran, voiture interpolée entre deux pas).
mod art;
mod policy;

use macroquad::prelude::*;
use policy::Policy;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::mpsc;
use std::time::SystemTime;
use trackai_core::consts::{BOT_DECISION_FRAMES, FPS, H, MAX_SPEED, W};
use trackai_core::env::Sim;
use trackai_core::gym::action_set;

const DT: f64 = 1.0 / FPS;
const SIDE: f32 = 340.0; // largeur du panneau de gauche (px logiques)

#[derive(Default)]
struct Args {
    model: Option<String>,
    follow: Option<String>,
    play: bool,
    laps: usize,
    track_seed: Option<u64>,
    hard: Option<String>,
    hard_file: String,
    speed: f64,
    screenshot: Option<String>,
    shot_at: u64,
    root: PathBuf,
}

fn parse_args() -> Args {
    let mut a = Args { laps: 3, speed: 1.0, shot_at: 300, hard_file: "data/hard_tracks/hard_tracks.json".into(), ..Default::default() };
    a.root = std::env::var("TRACKAI_ROOT").map(PathBuf::from).unwrap_or_else(|_| std::env::current_dir().unwrap());
    let v: Vec<String> = std::env::args().skip(1).collect();
    let mut i = 0;
    while i < v.len() {
        let next = |i: &mut usize| -> String {
            *i += 1;
            v.get(*i).cloned().unwrap_or_default()
        };
        match v[i].as_str() {
            "--model" => a.model = Some(next(&mut i)),
            "--follow" => a.follow = Some(next(&mut i)),
            "--play" => a.play = true,
            "--laps" => a.laps = next(&mut i).parse().unwrap_or(3),
            "--track-seed" => a.track_seed = next(&mut i).parse().ok(),
            "--hard" => {
                let nx = v.get(i + 1).cloned().unwrap_or_default();
                if ["train", "val", "all"].contains(&nx.as_str()) {
                    a.hard = Some(nx);
                    i += 1;
                } else {
                    a.hard = Some("train".into());
                }
            }
            "--hard-file" => a.hard_file = next(&mut i),
            "--speed" => a.speed = next(&mut i).parse().unwrap_or(1.0),
            "--screenshot" => a.screenshot = Some(next(&mut i)),
            "--shot-at" => a.shot_at = next(&mut i).parse().unwrap_or(300),
            "-h" | "--help" => {
                println!("trackai [--play | --model M.zip|M.json | --follow DOSSIER] [--laps N] [--hard [train|val|all]] [--track-seed S] [--speed X]");
                std::process::exit(0);
            }
            other => eprintln!("option inconnue : {other}"),
        }
        i += 1;
    }
    a
}

fn hard_seeds(which: &str, path: &Path) -> Vec<u64> {
    let Ok(txt) = std::fs::read_to_string(path) else {
        eprintln!("circuits durs introuvables : {}", path.display());
        return vec![];
    };
    let v: serde_json::Value = serde_json::from_str(&txt).unwrap_or_default();
    let get = |k: &str| -> Vec<u64> { v[k].as_array().map(|a| a.iter().filter_map(|x| x.as_u64()).collect()).unwrap_or_default() };
    match which {
        "all" => {
            let (t, va) = (get("train"), get("val"));
            let mut out = vec![];
            for i in 0..t.len().max(va.len()) {
                out.extend(t.get(i));
                out.extend(va.get(i));
            }
            out
        }
        w => get(w),
    }
}

/// Exporte un .zip SB3 en JSON (via le Python du projet), en cache dans data/viewer_cache/.
fn export_policy(root: &Path, model: &Path) -> Result<PathBuf, String> {
    if model.extension().map_or(false, |e| e == "json") {
        return Ok(model.to_path_buf());
    }
    let cache = root.join("data/viewer_cache");
    std::fs::create_dir_all(&cache).map_err(|e| e.to_string())?;
    let mtime = std::fs::metadata(model).and_then(|m| m.modified()).map_err(|e| format!("{} : {e}", model.display()))?;
    let stamp = mtime.duration_since(SystemTime::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    let name = model.to_string_lossy().replace(['/', '\\', '.'], "_");
    let out = cache.join(format!("{name}_{stamp}.json"));
    if out.exists() {
        return Ok(out);
    }
    let py = root.join(".venv/bin/python");
    let st = Command::new(&py)
        .arg(root.join("scripts/export_policy.py"))
        .arg(model)
        .arg(&out)
        .status()
        .map_err(|e| format!("{} : {e}", py.display()))?;
    if !st.success() {
        return Err(format!("export impossible pour {}", model.display()));
    }
    Ok(out)
}

fn latest_gen(dir: &Path) -> Option<PathBuf> {
    let mut gens: Vec<PathBuf> = std::fs::read_dir(dir)
        .ok()?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| {
            let n = p.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
            n.starts_with("gen_") && n.ends_with(".zip")
        })
        .collect();
    gens.sort();
    gens.pop()
}

fn gen_label(p: &Path) -> String {
    let n = p.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
    match n.strip_prefix("gen_").and_then(|g| g.parse::<u32>().ok()) {
        Some(g) => format!("Génération {g}"),
        None => n,
    }
}

fn fmt_time(t: f64) -> String {
    let ms = (t * 1000.0).round() as u64;
    format!("{:02}:{:02}.{:03}", ms / 60000, (ms / 1000) % 60, ms % 1000)
}

struct Bonk {
    pos: [f64; 2],
    lap: usize,
    at: f64,
}

fn window_conf() -> Conf {
    Conf {
        window_title: "TrackAI".into(),
        window_width: 1400,
        window_height: 850,
        high_dpi: true,
        sample_count: 4,
        window_resizable: true,
        ..Default::default()
    }
}

fn draw_car(pos: Vec2, heading: f32, body: Color, alpha: f32) {
    let (c, s) = (heading.cos(), heading.sin());
    let fwd = vec2(c, s);
    let side = vec2(-s, c);
    let rect = |center: Vec2, w: f32, h: f32, col: Color| {
        draw_rectangle_ex(center.x, center.y, w, h, DrawRectangleParams { offset: vec2(0.5, 0.5), rotation: heading, color: col });
    };
    let tyre = Color::new(0.08, 0.08, 0.1, alpha);
    for (f, sd) in [(9.0, 8.0), (9.0, -8.0), (-10.0, 8.5), (-10.0, -8.5)] {
        rect(pos + fwd * f + side * sd, 7.0, 4.5, tyre);
    }
    rect(pos, 30.0, 10.0, body);
    rect(pos + fwd * 16.0, 4.0, 20.0, body);
    rect(pos - fwd * 15.0, 4.0, 18.0, body);
    rect(pos + fwd * 2.0, 8.0, 5.0, Color::new(0.1, 0.1, 0.12, alpha));
    rect(pos + fwd * 8.0, 10.0, 2.0, Color::new(1.0, 1.0, 1.0, alpha * 0.9));
}

#[macroquad::main(window_conf)]
async fn main() {
    let a = parse_args();
    let root = a.root.clone();
    let hard = a.hard.as_ref().map(|w| hard_seeds(w, &root.join(&a.hard_file))).unwrap_or_default();
    if !hard.is_empty() {
        println!("{} circuits durs, du plus dur au plus facile : {:?}...", hard.len(), &hard[..hard.len().min(10)]);
    }
    let mut hard_i = 0usize;
    let mut rng_seed: u64 = SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).map(|d| d.as_nanos() as u64).unwrap_or(1);
    let mut next_seed = |hard_i: &mut usize| -> u64 {
        if let Some(s) = a.track_seed {
            return s;
        }
        if !hard.is_empty() {
            let s = hard[*hard_i % hard.len()];
            *hard_i += 1;
            return s;
        }
        rng_seed ^= rng_seed << 13;
        rng_seed ^= rng_seed >> 7;
        rng_seed ^= rng_seed << 17;
        1000 + rng_seed % 1_000_000_000
    };

    // politique du bot
    let mut policy: Option<Policy> = None;
    let mut label = String::new();
    let mut loaded_from: Option<PathBuf> = None;
    let follow_dir = a.follow.as_ref().map(|d| root.join(d));
    let load = |p: &Path| -> Result<Policy, String> { Policy::load(export_policy(&root, p)?.to_str().unwrap()) };
    if !a.play {
        let first = match (&a.model, &follow_dir) {
            (Some(m), _) => Some(root.join(m)),
            (None, Some(d)) => latest_gen(d),
            _ => None,
        };
        match first {
            Some(p) => match load(&p) {
                Ok(pl) => {
                    label = gen_label(&p);
                    loaded_from = Some(p);
                    policy = Some(pl);
                }
                Err(e) => eprintln!("{e}"),
            },
            None => eprintln!("aucun modèle : --model, --follow ou --play"),
        }
    }
    // rechargement en arrière-plan (--follow)
    let (tx, rx) = mpsc::channel::<(PathBuf, Result<Policy, String>)>();
    let mut pending = false;
    let mut last_check = 0.0f64;

    let obs_version = policy.as_ref().map_or(3, |p| p.obs_version);
    let actions = action_set(policy.as_ref().map_or(2, |p| p.action_set));
    let mut sim = Sim::new(next_seed(&mut hard_i), a.laps).expect("circuit");
    let mut tex = art::track_texture(&sim.track);
    let mut obs = Vec::with_capacity(64);
    let mut action = 0usize;
    let mut frame: u64 = 0;
    let mut acc = 0.0f64;
    let mut prev = (sim.car.pos, sim.car.heading);
    let mut bonks: Vec<Bonk> = vec![];
    let mut seen_hits = 0u64;
    let mut stuck = 0u32;
    let mut pause_until: Option<f64> = None;
    let mut paused = false;
    let mut speed = a.speed;
    let mut drawn: u64 = 0;
    let mut record: Option<f64> = None;

    loop {
        let now = get_time();
        if is_key_pressed(KeyCode::Escape) || is_key_pressed(KeyCode::Q) && !a.play {
            break;
        }
        if is_key_pressed(KeyCode::Space) {
            paused = !paused;
        }
        if is_key_pressed(KeyCode::Equal) || is_key_pressed(KeyCode::KpAdd) {
            speed = (speed * 2.0).min(8.0);
        }
        if is_key_pressed(KeyCode::Minus) || is_key_pressed(KeyCode::KpSubtract) {
            speed = (speed / 2.0).max(0.25);
        }
        let mut new_race = is_key_pressed(KeyCode::N);
        if is_key_pressed(KeyCode::R) {
            sim.restart();
            bonks.clear();
            seen_hits = 0;
            frame = 0;
            prev = (sim.car.pos, sim.car.heading);
        }

        // nouvelle génération ?
        if let Some(d) = &follow_dir {
            if !pending && now - last_check > 2.0 {
                last_check = now;
                if let Some(g) = latest_gen(d) {
                    if loaded_from.as_ref() != Some(&g) {
                        pending = true;
                        let (tx, root) = (tx.clone(), root.clone());
                        std::thread::spawn(move || {
                            std::thread::sleep(std::time::Duration::from_millis(1500)); // laisse l'entraînement finir d'écrire
                            let r = export_policy(&root, &g).and_then(|p| Policy::load(p.to_str().unwrap()));
                            let _ = tx.send((g, r));
                        });
                    }
                }
            }
        }

        // physique à pas fixe
        if !paused && pause_until.is_none() {
            acc += (get_frame_time() as f64 * speed).min(0.25);
            while acc >= DT {
                acc -= DT;
                prev = (sim.car.pos, sim.car.heading);
                let (steer, accel, brake) = if a.play {
                    let left = is_key_down(KeyCode::Left) || is_key_down(KeyCode::A);
                    let right = is_key_down(KeyCode::Right) || is_key_down(KeyCode::D);
                    let up = is_key_down(KeyCode::Up) || is_key_down(KeyCode::W) || is_key_down(KeyCode::Z);
                    let down = is_key_down(KeyCode::Down) || is_key_down(KeyCode::S);
                    let left = left || is_key_down(KeyCode::Q);
                    ((right as i32 - left as i32) as f64, up as i32 as f64, down as i32 as f64)
                } else if let Some(p) = &policy {
                    if frame % BOT_DECISION_FRAMES as u64 == 0 {
                        sim.obs(obs_version, &mut obs);
                        action = p.act(&obs);
                    }
                    actions[action]
                } else {
                    (0.0, 0.0, 0.0)
                };
                sim.step(steer, accel, brake);
                frame += 1;
                if sim.wall_hits > seen_hits {
                    for _ in seen_hits..sim.wall_hits {
                        bonks.push(Bonk { pos: sim.car.pos, lap: sim.lap_count, at: now });
                    }
                    seen_hits = sim.wall_hits;
                }
                stuck = if sim.car.speed.max(0.0) / MAX_SPEED < 0.05 { stuck + 1 } else { 0 };
                let timeout = frame >= 2000 * a.laps as u64 * if a.play { 10 } else { 1 };
                if sim.done || timeout || (!a.play && stuck >= 150) {
                    if sim.done {
                        let total: f64 = sim.lap_times.iter().sum();
                        record = Some(record.map_or(total, |r: f64| r.min(total)));
                    }
                    pause_until = Some(now + 1.5);
                    break;
                }
            }
        }
        if let Some(t) = pause_until {
            if now >= t {
                pause_until = None;
                new_race = true;
            }
        }
        if new_race {
            if let Ok((g, r)) = rx.try_recv() {
                pending = false;
                match r {
                    Ok(p) => {
                        label = gen_label(&g);
                        loaded_from = Some(g);
                        policy = Some(p);
                    }
                    Err(e) => eprintln!("{e}"),
                }
            }
            let seed = next_seed(&mut hard_i);
            let same = seed == sim.track.seed;
            sim.reset(seed).expect("circuit");
            if !same {
                tex = art::track_texture(&sim.track);
                record = None;
            }
            bonks.clear();
            seen_hits = 0;
            stuck = 0;
            frame = 0;
            acc = 0.0;
            prev = (sim.car.pos, sim.car.heading);
        }

        // --- dessin ---
        clear_background(Color::from_rgba(18, 20, 26, 255));
        let (sw, sh) = (screen_width(), screen_height());
        let side = SIDE.min(sw * 0.3);
        let scale = ((sw - side) / W as f32).min(sh / H as f32);
        let cam = Camera2D {
            // le circuit occupe la droite de la fenêtre, le panneau la colonne de gauche
            target: vec2(W as f32 / 2.0 - side / (2.0 * scale), H as f32 / 2.0),
            zoom: vec2(2.0 * scale / sw, 2.0 * scale / sh),
            ..Default::default()
        };
        set_camera(&cam);
        draw_texture_ex(&tex, 0.0, 0.0, WHITE, DrawTextureParams { dest_size: Some(vec2(W as f32, H as f32)), ..Default::default() });

        // portes de checkpoint et arrivée
        let half = (sim.track.half_width + 10.0) as f32;
        let next = sim.next_cp();
        for (i, c) in sim.track.checkpoints.iter().enumerate() {
            let (cx, cy, ang) = (c[0] as f32, c[1] as f32, c[2] as f32);
            let d = vec2(ang.cos(), ang.sin()) * half;
            let col = if Some(i) == next {
                Color::new(0.35, 0.85, 1.0, 0.9)
            } else if sim.cp_visited[i] {
                Color::new(0.35, 0.85, 1.0, 0.18)
            } else {
                Color::new(1.0, 1.0, 1.0, 0.25)
            };
            draw_line(cx - d.x, cy - d.y, cx + d.x, cy + d.y, if Some(i) == next { 5.0 } else { 3.0 }, col);
        }
        {
            let [fx, fy, fa] = sim.track.finish;
            let (fx, fy, fa) = (fx as f32, fy as f32, fa as f32);
            let across = vec2(fa.cos(), fa.sin());
            let along = vec2(fa.sin(), -fa.cos());
            let n = (2.0 * half / 10.0) as i32;
            for k in 0..n {
                for row in 0..2 {
                    let p = vec2(fx, fy) + across * (-half + 5.0 + k as f32 * 10.0) + along * (row as f32 * 10.0 - 5.0);
                    let col = if (k + row) % 2 == 0 { WHITE } else { Color::new(0.08, 0.08, 0.1, 1.0) };
                    draw_rectangle_ex(p.x, p.y, 10.0, 10.0, DrawRectangleParams { offset: vec2(0.5, 0.5), rotation: fa, color: col });
                }
            }
        }

        // marques de choc
        for b in &bonks {
            let (x, y) = (b.pos[0] as f32, b.pos[1] as f32);
            let col = if b.lap == sim.lap_count { Color::new(1.0, 0.16, 0.16, 0.95) } else { Color::new(0.6, 0.25, 0.25, 0.7) };
            draw_circle(x, y, 10.0, Color::new(0.25, 0.05, 0.05, 0.6));
            draw_line(x - 7.0, y - 7.0, x + 7.0, y + 7.0, 4.0, col);
            draw_line(x - 7.0, y + 7.0, x + 7.0, y - 7.0, 4.0, col);
        }

        // voiture interpolée
        let alpha = (acc / DT).clamp(0.0, 1.0);
        let lerp = |p: f64, c: f64| (p + (c - p) * alpha) as f32;
        let pos = vec2(lerp(prev.0[0], sim.car.pos[0]), lerp(prev.0[1], sim.car.pos[1]));
        let heading = lerp(prev.1, sim.car.heading);
        if !a.play && obs.len() >= 44 {
            for k in 0..9 {
                let ang = heading + (-std::f32::consts::FRAC_PI_2 + k as f32 * std::f32::consts::PI / 8.0);
                let d = obs[35 + k] * 400.0;
                let end = pos + vec2(ang.cos(), ang.sin()) * d;
                let col = if obs[35 + k] < 0.15 { Color::new(1.0, 0.3, 0.2, 0.55) } else { Color::new(0.4, 1.0, 0.4, 0.25) };
                draw_line(pos.x, pos.y, end.x, end.y, 1.5, col);
            }
        }
        draw_car(pos, heading, Color::new(0.12, 0.35, 0.85, 1.0), 1.0);

        // anneaux « BONK ! »
        for b in &bonks {
            let age = (now - b.at) as f32;
            if age < 0.8 {
                let k = age / 0.8;
                let (x, y) = (b.pos[0] as f32, b.pos[1] as f32);
                draw_circle_lines(x, y, 14.0 + 46.0 * k, 4.0, Color::new(1.0, 0.24, 0.16, 1.0 - k));
                let t = "BONK !";
                let dim = measure_text(t, None, 30, 1.0);
                draw_text(t, x - dim.width / 2.0, y - 40.0 - 30.0 * k, 30.0, Color::new(1.0, 0.27, 0.2, 1.0 - k));
            }
        }

        // --- panneau ---
        set_default_camera();
        draw_rectangle(0.0, 0.0, side, sh, Color::from_rgba(18, 20, 26, 255));
        let lap_t = if sim.lap_count < sim.laps { sim.t - sim.lap_start_t } else { 0.0 };
        let mut lines: Vec<(String, f32, Color)> = vec![];
        if !label.is_empty() {
            lines.push((label.clone(), 26.0, WHITE));
        }
        if a.play {
            lines.push(("Mode pilote".into(), 26.0, WHITE));
        }
        lines.push((format!("Circuit #{}  ·  tour {}/{}", sim.track.seed, (sim.lap_count + 1).min(sim.laps), sim.laps), 20.0, Color::from_rgba(190, 196, 210, 255)));
        lines.push((fmt_time(lap_t), 44.0, WHITE));
        let len = sim.track.length();
        for (i, t) in sim.lap_times.iter().enumerate() {
            let v = len / t / (MAX_SPEED * FPS) * 100.0;
            lines.push((format!("T{}  {}  {:.1} %", i + 1, fmt_time(*t), v), 20.0, WHITE));
        }
        if let Some(r) = record {
            lines.push((format!("Meilleure course ici  {}", fmt_time(r)), 20.0, Color::from_rgba(230, 200, 120, 255)));
        }
        let lap_hits = bonks.iter().filter(|b| b.lap == sim.lap_count).count();
        lines.push((format!("Chocs  {}   (ce tour : {})", sim.wall_hits, lap_hits), 20.0, Color::from_rgba(255, 90, 80, 255)));
        lines.push((format!("{:.0} px/s", sim.car.speed.max(0.0) * FPS), 20.0, Color::from_rgba(150, 220, 160, 255)));
        lines.push((format!("{} fps  ·  physique 50 Hz  ·  x{}", get_fps(), speed), 18.0, Color::from_rgba(150, 156, 170, 255)));
        let hgt: f32 = lines.iter().map(|l| l.1 + 6.0).sum::<f32>() + 20.0;
        draw_rectangle(12.0, 12.0, side - 24.0, hgt, Color::from_rgba(30, 33, 42, 255));
        let mut y = 22.0;
        for (t, s, c) in &lines {
            y += s;
            draw_text(t, 26.0, y, *s, *c);
            y += 6.0;
        }
        let keys: &[&str] = if a.play {
            &["Flèches, ZQSD ou WASD : conduire", "R : recommencer   N : autre circuit", "Espace : pause   Échap : quitter"]
        } else {
            &["N : circuit suivant   R : recommencer", "Espace : pause   +/- : vitesse", "Échap : quitter"]
        };
        for (k, t) in keys.iter().enumerate() {
            draw_text(t, 22.0, sh - 18.0 - 22.0 * (keys.len() - 1 - k) as f32, 18.0, Color::from_rgba(150, 156, 170, 255));
        }
        if paused {
            draw_text("PAUSE", side + (sw - side) / 2.0 - 50.0, 40.0, 40.0, WHITE);
        }

        drawn += 1;
        if let Some(path) = &a.screenshot {
            if drawn == a.shot_at {
                get_screen_data().export_png(path);
                break;
            }
        }
        next_frame().await;
    }
}
