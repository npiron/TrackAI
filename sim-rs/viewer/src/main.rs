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
    ghost: Option<String>,
    no_ghost: bool,
    menu: bool,
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
            "--ghost" => a.ghost = Some(next(&mut i)),
            "--no-ghost" => a.no_ghost = true,
            "--menu" => a.menu = true,
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

/// Dernière génération du dossier, ou le modèle de départ d'une reprise tant qu'il n'y en a pas.
fn latest_gen(dir: &Path) -> Option<PathBuf> {
    latest_gen_only(dir).or_else(|| {
        let cfg: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(dir.join("config.json")).ok()?).ok()?;
        let init = PathBuf::from(cfg["init"].as_str()?);
        let init = if init.is_absolute() { init } else { dir.parent()?.parent()?.parent()?.join(init) };
        init.is_file().then_some(init)
    })
}

fn latest_gen_only(dir: &Path) -> Option<PathBuf> {
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

/// Génération qui précède `cur` dans `dir` (ou le modèle de départ d'une reprise, lu dans config.json).
fn previous_model(dir: &Path, cur: &Path) -> Option<PathBuf> {
    let mut gens: Vec<PathBuf> = std::fs::read_dir(dir)
        .ok()?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| {
            let n = p.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
            n.starts_with("gen_") && n.ends_with(".zip")
        })
        .collect();
    gens.sort();
    if let Some(i) = gens.iter().position(|g| g == cur) {
        if i > 0 {
            return Some(gens[i - 1].clone());
        }
    }
    let cfg: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(dir.join("config.json")).ok()?).ok()?;
    let init = PathBuf::from(cfg["init"].as_str()?);
    (init.is_file() && init != cur).then_some(init)
}

fn gen_number(p: &Path) -> Option<u64> {
    p.file_stem()?.to_string_lossy().strip_prefix("gen_")?.parse().ok()
}

fn gen_label(p: &Path) -> String {
    let n = p.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
    match n.strip_prefix("gen_").and_then(|g| g.parse::<u32>().ok()) {
        Some(g) => format!("Génération {g}"),
        None => {
            let run = p.parent().and_then(|d| d.file_name()).map(|d| d.to_string_lossy().to_string()).unwrap_or_default();
            if run.is_empty() { n } else { format!("{run} · {n}") }
        }
    }
}

/// Un circuit qui a un WR (écran de choix).
struct MenuItem {
    seed: u64,
    laps: usize,
    wr: f64,
    gen: Option<u64>,
    ghost: bool,
}

fn wr_circuits(root: &Path, records: &serde_json::Value) -> Vec<MenuItem> {
    let mut v: Vec<MenuItem> = records
        .as_object()
        .map(|o| {
            o.iter()
                .filter_map(|(k, e)| {
                    let (s, l) = k.split_once('-')?;
                    Some(MenuItem {
                        seed: s.parse().ok()?,
                        laps: l.parse().ok()?,
                        wr: e["lap"].as_f64()?,
                        gen: e["lap_gen"].as_u64(),
                        ghost: wr_ghost_path(root, k).exists(),
                    })
                })
                .collect()
        })
        .unwrap_or_default();
    // circuits qui ont un fantôme doré mais plus de ligne dans bot_records.json
    if let Ok(rd) = std::fs::read_dir(root.join("data/bot_ghosts")) {
        for e in rd.flatten() {
            let p = e.path();
            let Some(k) = p.file_stem().map(|s| s.to_string_lossy().to_string()) else { continue };
            let Some((sd, l)) = k.split_once('-') else { continue };
            let (Ok(seed), Ok(laps)) = (sd.parse::<u64>(), l.parse::<usize>()) else { continue };
            if v.iter().any(|m| m.seed == seed && m.laps == laps) {
                continue;
            }
            if let Some(g) = load_wr_ghost(root, &k) {
                v.push(MenuItem { seed, laps, wr: g.lap, gen: g.gen, ghost: true });
            }
        }
    }
    v.sort_by(|a, b| (b.ghost, a.seed, a.laps).cmp(&(a.ghost, b.seed, b.laps)));
    v
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

const MENU_ROW: f32 = 34.0;
const MENU_TOP: f32 = 110.0;

/// Géométrie de la liste : (x, largeur, nombre de lignes visibles, première ligne affichée).
fn menu_layout(sel: usize, n: usize) -> (f32, f32, usize, usize) {
    let (sw, sh) = (screen_width(), screen_height());
    let side = SIDE.min(sw * 0.3);
    let x = side + 40.0;
    let w = (sw - side - 80.0).min(760.0);
    let rows = (((sh - MENU_TOP - 60.0) / MENU_ROW) as usize).max(1);
    let first = if sel >= rows { sel + 1 - rows } else { 0 }.min(n.saturating_sub(rows));
    (x, w, rows, first)
}

fn menu_hit((mx, my): (f32, f32), sel: usize, n: usize) -> Option<usize> {
    let (x, w, rows, first) = menu_layout(sel, n);
    if mx < x || mx > x + w || my < MENU_TOP {
        return None;
    }
    let r = ((my - MENU_TOP) / MENU_ROW) as usize;
    (r < rows && first + r < n).then_some(first + r)
}

fn draw_menu(items: &[MenuItem], sel: usize, cur_seed: u64, cur_laps: usize) {
    let (sw, sh) = (screen_width(), screen_height());
    let side = SIDE.min(sw * 0.3);
    draw_rectangle(side, 0.0, sw - side, sh, Color::new(0.05, 0.06, 0.08, 0.82));
    let (x, w, rows, first) = menu_layout(sel, items.len());
    draw_text("Circuits avec un WR", x, 60.0, 40.0, WHITE);
    draw_text(&format!("{} circuits  ·  flèches ou molette, Entrée ou clic pour courir, Échap pour fermer", items.len()), x, 90.0, 18.0, Color::from_rgba(150, 156, 170, 255));
    if items.is_empty() {
        draw_text("Aucun WR pour l'instant : laisse le bot boucler quelques tours.", x, MENU_TOP + 30.0, 22.0, WHITE);
        return;
    }
    for (r, it) in items.iter().enumerate().skip(first).take(rows) {
        let y = MENU_TOP + (r - first) as f32 * MENU_ROW;
        if r == sel {
            draw_rectangle(x - 10.0, y, w, MENU_ROW - 4.0, Color::new(0.3, 0.75, 1.0, 0.25));
        }
        let col = if it.seed == cur_seed && it.laps == cur_laps { Color::from_rgba(120, 220, 255, 255) } else { WHITE };
        let ty = y + 23.0;
        draw_text(&format!("#{}", it.seed), x, ty, 24.0, col);
        draw_text(&format!("{} tours", it.laps), x + 150.0, ty, 22.0, Color::from_rgba(190, 196, 210, 255));
        draw_text(&format!("WR {}", fmt_time(it.wr)), x + 270.0, ty, 22.0, Color::from_rgba(230, 200, 120, 255));
        if let Some(g) = it.gen {
            draw_text(&format!("gén. {g}"), x + 460.0, ty, 20.0, Color::from_rgba(150, 156, 170, 255));
        }
        if it.ghost {
            draw_text("fantôme doré", x + 560.0, ty, 20.0, Color::from_rgba(255, 210, 60, 255));
        }
    }
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

/// Une voiture qui roule (le bot, son fantôme ou le joueur).
struct Driver {
    sim: Sim,
    frame: u64,
    action: usize,
    obs: Vec<f32>,
    prev: ([f64; 2], f64),
    stuck: u32,
    over: bool,
}

impl Driver {
    fn new(seed: u64, laps: usize) -> Driver {
        let sim = Sim::new(seed, laps).expect("circuit");
        let prev = (sim.car.pos, sim.car.heading);
        Driver { sim, frame: 0, action: 0, obs: Vec::with_capacity(64), prev, stuck: 0, over: false }
    }

    fn reset(&mut self, seed: u64) {
        self.sim.reset(seed).expect("circuit");
        self.restart();
    }

    fn restart(&mut self) {
        self.sim.restart();
        self.frame = 0;
        self.stuck = 0;
        self.over = false;
        self.prev = (self.sim.car.pos, self.sim.car.heading);
    }

    /// Une image ; renvoie true quand la course est finie (arrivée, temps écoulé ou bloqué).
    fn tick(&mut self, input: Option<(f64, f64, f64)>, policy: Option<&Policy>, actions: &[(f64, f64, f64)], timeout: u64) -> bool {
        if self.over {
            self.prev = (self.sim.car.pos, self.sim.car.heading);
            return true;
        }
        self.prev = (self.sim.car.pos, self.sim.car.heading);
        let (steer, accel, brake) = match (input, policy) {
            (Some(i), _) => i,
            (None, Some(p)) => {
                if self.frame % BOT_DECISION_FRAMES as u64 == 0 {
                    self.sim.obs(p.obs_version, &mut self.obs);
                    self.action = p.act(&self.obs);
                }
                actions[self.action]
            }
            _ => (0.0, 0.0, 0.0),
        };
        self.sim.step(steer, accel, brake);
        self.frame += 1;
        self.stuck = if self.sim.car.speed.max(0.0) / MAX_SPEED < 0.05 { self.stuck + 1 } else { 0 };
        if self.sim.done || self.frame >= timeout || (input.is_none() && self.stuck >= 150) {
            self.over = true;
        }
        self.over
    }

    fn pose(&self, alpha: f64) -> (Vec2, f32) {
        let l = |p: f64, c: f64| (p + (c - p) * alpha) as f32;
        (vec2(l(self.prev.0[0], self.sim.car.pos[0]), l(self.prev.0[1], self.sim.car.pos[1])), l(self.prev.1, self.sim.car.heading))
    }
}

/// Records du bot, dans les mêmes fichiers que la version Pygame :
/// data/bot_records.json (WR du tour par circuit : "graine-tours" -> {lap, lap_gen, splits}) et
/// data/bot_speed_record.json (meilleure vitesse moyenne sur un tour, tous circuits).
struct Records {
    laps_path: PathBuf,
    speed_path: PathBuf,
    laps: serde_json::Value,
    speed: serde_json::Value,
}

impl Records {
    fn load(root: &Path) -> Records {
        let read = |p: &Path| -> serde_json::Value {
            std::fs::read_to_string(p).ok().and_then(|t| serde_json::from_str(&t).ok()).unwrap_or(serde_json::json!({}))
        };
        let laps_path = root.join("data/bot_records.json");
        let speed_path = root.join("data/bot_speed_record.json");
        Records { laps: read(&laps_path), speed: read(&speed_path), laps_path, speed_path }
    }

    fn save(path: &Path, v: &serde_json::Value) {
        if let Ok(t) = serde_json::to_string_pretty(v) {
            let tmp = path.with_extension("json.tmp");
            if std::fs::write(&tmp, t).is_ok() {
                let _ = std::fs::rename(&tmp, path);
            }
        }
    }

    /// (temps, génération, temps intermédiaires) du WR de ce circuit.
    fn wr(&self, key: &str) -> Option<(f64, Option<u64>, Vec<f64>)> {
        let e = &self.laps[key];
        let lap = e["lap"].as_f64()?;
        let splits = e["splits"].as_array().map(|a| a.iter().map(|x| x.as_f64().unwrap_or(f64::NAN)).collect()).unwrap_or_default();
        Some((lap, e["lap_gen"].as_u64(), splits))
    }

    /// Relit les fichiers (un autre viewer a pu y écrire entre-temps) avant d'y ajouter quelque chose.
    fn refresh(&mut self) {
        if let Some(v) = std::fs::read_to_string(&self.laps_path).ok().and_then(|t| serde_json::from_str::<serde_json::Value>(&t).ok()) {
            if v.is_object() {
                self.laps = v;
            }
        }
        if let Some(v) = std::fs::read_to_string(&self.speed_path).ok().and_then(|t| serde_json::from_str::<serde_json::Value>(&t).ok()) {
            if v.is_object() {
                self.speed = v;
            }
        }
    }

    fn set_wr(&mut self, key: &str, lap: f64, gen: Option<u64>, splits: &[f64]) {
        self.refresh();
        if self.laps[key]["lap"].as_f64().map_or(false, |old| old <= lap) {
            return; // battu entre-temps par un autre viewer
        }
        self.laps[key] = serde_json::json!({ "lap": (lap * 1000.0).round() / 1000.0, "lap_gen": gen, "splits": splits });
        Self::save(&self.laps_path, &self.laps);
    }

    fn speed_record(&self) -> Option<(f64, Option<u64>)> {
        Some((self.speed["speed"].as_f64()?, self.speed["gen"].as_u64()))
    }

    fn set_speed(&mut self, v: f64, gen: Option<u64>, seed: u64, run: &str) {
        self.refresh();
        if self.speed["speed"].as_f64().map_or(false, |old| old >= v) {
            return;
        }
        self.speed = serde_json::json!({ "speed": (v * 10000.0).round() / 10000.0, "gen": gen, "seed": seed, "run": run });
        Self::save(&self.speed_path, &self.speed);
    }
}

/// Fantôme du WR d'un circuit : la trajectoire du tour record, image par image (x, y, cap).
struct WrGhost {
    lap: f64,
    gen: Option<u64>,
    frames: Vec<[f32; 3]>,
}

fn wr_ghost_path(root: &Path, key: &str) -> PathBuf {
    root.join("data/bot_ghosts").join(format!("{key}.json"))
}

fn load_wr_ghost(root: &Path, key: &str) -> Option<WrGhost> {
    let v: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(wr_ghost_path(root, key)).ok()?).ok()?;
    let frames = v["frames"]
        .as_array()?
        .iter()
        .filter_map(|f| {
            let f = f.as_array()?;
            Some([f.first()?.as_f64()? as f32, f.get(1)?.as_f64()? as f32, f.get(2)?.as_f64()? as f32])
        })
        .collect::<Vec<_>>();
    (!frames.is_empty()).then(|| WrGhost { lap: v["lap"].as_f64().unwrap_or(0.0), gen: v["gen"].as_u64(), frames })
}

fn save_wr_ghost(root: &Path, key: &str, g: &WrGhost) {
    let dir = root.join("data/bot_ghosts");
    let _ = std::fs::create_dir_all(&dir);
    let frames: Vec<[f64; 3]> = g.frames.iter().map(|f| [(f[0] as f64 * 100.0).round() / 100.0, (f[1] as f64 * 100.0).round() / 100.0, (f[2] as f64 * 10000.0).round() / 10000.0]).collect();
    let v = serde_json::json!({ "lap": g.lap, "gen": g.gen, "frames": frames });
    let path = wr_ghost_path(root, key);
    let tmp = path.with_extension("json.tmp");
    if std::fs::write(&tmp, v.to_string()).is_ok() {
        let _ = std::fs::rename(&tmp, &path);
    }
}

/// Bulle de temps intermédiaire (au-dessus d'une porte ou de la ligne).
struct Split {
    #[allow(dead_code)]
    pos: Vec2,
    time: f64,
    delta: Option<f64>,
    at: f64,
    ghost: Option<f64>,
}

/// Traces de pneus : une suite de positions des deux roues arrière tant que la voiture glisse ou freine.
struct Skid {
    left: Vec<Vec2>,
    right: Vec<Vec2>,
}

type Loaded = (PathBuf, Result<Policy, String>, Option<(PathBuf, Result<Policy, String>)>);

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

    // politique du bot et de son fantôme
    let follow_dir = a.follow.as_ref().map(|d| root.join(d));
    let run_name = follow_dir.as_ref().and_then(|d| d.file_name()).map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
    let load = |p: &Path| -> Result<Policy, String> { Policy::load(export_policy(&root, p)?.to_str().unwrap()) };
    let mut policy: Option<Policy> = None;
    let mut ghost_policy: Option<Policy> = None;
    let mut label = String::new();
    let mut ghost_label = String::new();
    let mut gen: Option<u64> = None;
    let mut loaded_from: Option<PathBuf> = None;
    if !a.play {
        let first = match (&a.model, &follow_dir) {
            (Some(m), _) => Some(root.join(m)),
            (None, Some(d)) => latest_gen(d),
            _ => None,
        };
        match &first {
            Some(p) => match load(p) {
                Ok(pl) => {
                    label = gen_label(p);
                    gen = gen_number(p);
                    loaded_from = Some(p.clone());
                    policy = Some(pl);
                }
                Err(e) => eprintln!("{e}"),
            },
            None => eprintln!("aucun modèle : --model, --follow ou --play"),
        }
        if !a.no_ghost {
            let g = match (&a.ghost, &follow_dir, &first) {
                (Some(g), _, _) => Some(root.join(g)),
                (None, Some(d), Some(cur)) => previous_model(d, cur),
                _ => None,
            };
            if let Some(g) = g {
                match load(&g) {
                    Ok(p) => {
                        ghost_label = gen_label(&g);
                        ghost_policy = Some(p);
                    }
                    Err(e) => eprintln!("fantôme : {e}"),
                }
            }
        }
    }
    // rechargement en arrière-plan (--follow) : nouvelle génération + la précédente en fantôme
    let (tx, rx) = mpsc::channel::<Loaded>();
    let mut pending = false;
    let mut last_check = 0.0f64;

    let actions = action_set(policy.as_ref().map_or(2, |p| p.action_set));
    let mut laps = a.laps;
    let timeout_for = |l: usize| 2000 * l as u64 * if a.play { 10 } else { 1 };
    let mut me = Driver::new(next_seed(&mut hard_i), laps);
    let mut ghost = ghost_policy.as_ref().map(|_| Driver::new(me.sim.track.seed, laps));
    let mut tex = art::track_texture(&me.sim.track);
    let mut records = Records::load(&root);
    let mut acc = 0.0f64;
    let mut bonks: Vec<Bonk> = vec![];
    let mut seen_hits = 0u64;
    let mut seen_laps = 0usize;
    let mut seen_cps = 0usize;
    let mut splits_now: Vec<f64> = vec![];
    let mut session_best: Option<(f64, Vec<f64>)> = None; // meilleur tour de la session sur ce circuit
    let mut pb_speed: Option<f64> = None; // meilleure vitesse de la génération courante
    let mut bubbles: Vec<Split> = vec![];
    let mut skids: Vec<Skid> = vec![];
    let mut skidding = false;
    // fantôme WR : trajectoire du tour en cours (sauvée si elle bat le WR) et fantôme du WR de ce circuit
    let mut lap_traj: Vec<[f32; 3]> = vec![];
    let mut lap_start_frame: u64 = 0;
    let mut wr_ghost: Option<WrGhost> = load_wr_ghost(&root, &format!("{}-{}", me.sim.track.seed, laps));
    // écran de choix des circuits avec un WR (touche C) et circuit choisi (gardé jusqu'à N)
    let mut menu: Option<(Vec<MenuItem>, usize)> = None;
    let mut pinned: Option<u64> = None;
    if a.menu {
        let items = wr_circuits(&root, &records.laps);
        menu = Some((items, 0));
    }
    // passages du fantôme : (tour, porte) -> temps de course ; porte = nb de portes pour la ligne d'arrivée
    let mut ghost_marks: std::collections::HashMap<(usize, usize), f64> = std::collections::HashMap::new();
    let (mut ghost_seen_cps, mut ghost_seen_laps) = (0usize, 0usize);
    let mut ghost_delta: Option<f64> = None; // écart avec le fantôme au dernier passage (négatif : devant)
    let mut show_lidar = false;
    let mut show_help = false;
    let mut pause_until: Option<f64> = None;
    let mut paused = false;
    let mut speed = a.speed;
    let mut drawn: u64 = 0;
    let record_key = |seed: u64, laps: usize| format!("{seed}-{laps}");

    loop {
        let now = get_time();
        let mut chosen: Option<(u64, usize)> = None;
        if let Some((items, sel)) = menu.as_mut() {
            let n = items.len();
            if is_key_pressed(KeyCode::Escape) || is_key_pressed(KeyCode::C) {
                menu = None;
            } else if n > 0 {
                if is_key_pressed(KeyCode::Down) { *sel = (*sel + 1).min(n - 1); }
                if is_key_pressed(KeyCode::Up) { *sel = sel.saturating_sub(1); }
                if is_key_pressed(KeyCode::PageDown) { *sel = (*sel + 15).min(n - 1); }
                if is_key_pressed(KeyCode::PageUp) { *sel = sel.saturating_sub(15); }
                let wheel = mouse_wheel().1;
                if wheel < 0.0 { *sel = (*sel + 1).min(n - 1); }
                if wheel > 0.0 { *sel = sel.saturating_sub(1); }
                if is_key_pressed(KeyCode::Enter) || is_key_pressed(KeyCode::KpEnter) {
                    chosen = Some((items[*sel].seed, items[*sel].laps));
                }
                if is_mouse_button_pressed(MouseButton::Left) {
                    if let Some(i) = menu_hit(mouse_position(), *sel, n) {
                        chosen = Some((items[i].seed, items[i].laps));
                    }
                }
            }
        } else {
            if is_key_pressed(KeyCode::Escape) || is_key_pressed(KeyCode::Q) && !a.play {
                break;
            }
            if is_key_pressed(KeyCode::C) {
                records.refresh();
                let items = wr_circuits(&root, &records.laps);
                let sel = items.iter().position(|m| m.seed == me.sim.track.seed && m.laps == laps).unwrap_or(0);
                menu = Some((items, sel));
            }
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
        let mut new_race = menu.is_none() && is_key_pressed(KeyCode::N);
        if new_race {
            pinned = None; // N : on repart sur la liste habituelle
        }
        if let Some((seed, l)) = chosen {
            pinned = Some(seed);
            laps = l;
            me.sim.laps = l;
            menu = None;
            new_race = true;
            pause_until = None;
        }
        let mut restart = is_key_pressed(KeyCode::R);
        if is_key_pressed(KeyCode::L) {
            show_lidar = !show_lidar;
        }
        if is_key_pressed(KeyCode::H) {
            show_help = !show_help;
        }

        // nouvelle génération ?
        if let Some(d) = &follow_dir {
            if !pending && now - last_check > 2.0 {
                last_check = now;
                if let Some(g) = latest_gen(d) {
                    if loaded_from.as_ref() != Some(&g) {
                        pending = true;
                        let (tx, root, d, no_ghost) = (tx.clone(), root.clone(), d.clone(), a.no_ghost);
                        std::thread::spawn(move || {
                            std::thread::sleep(std::time::Duration::from_millis(1500)); // laisse l'entraînement finir d'écrire
                            let ld = |p: &Path| export_policy(&root, p).and_then(|j| Policy::load(j.to_str().unwrap()));
                            let r = ld(&g);
                            let gh = if no_ghost { None } else { previous_model(&d, &g).map(|p| { let r = ld(&p); (p, r) }) };
                            let _ = tx.send((g, r, gh));
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
                let input = if a.play {
                    let left = is_key_down(KeyCode::Left) || is_key_down(KeyCode::A) || is_key_down(KeyCode::Q);
                    let right = is_key_down(KeyCode::Right) || is_key_down(KeyCode::D);
                    let up = is_key_down(KeyCode::Up) || is_key_down(KeyCode::W) || is_key_down(KeyCode::Z);
                    let down = is_key_down(KeyCode::Down) || is_key_down(KeyCode::S);
                    Some(((right as i32 - left as i32) as f64, up as i32 as f64, down as i32 as f64))
                } else {
                    None
                };
                let ended = me.tick(input, policy.as_ref(), &actions, timeout_for(laps));
                if !me.sim.done || lap_traj.is_empty() {
                    lap_traj.push([me.sim.car.pos[0] as f32, me.sim.car.pos[1] as f32, me.sim.car.heading as f32]);
                }
                if let (Some(g), Some(gp)) = (ghost.as_mut(), ghost_policy.as_ref()) {
                    g.tick(None, Some(gp), &actions, timeout_for(laps));
                    let gs = &g.sim;
                    let n_cp = gs.track.checkpoints.len();
                    if gs.lap_times.len() > ghost_seen_laps {
                        ghost_marks.insert((ghost_seen_laps, n_cp), gs.t);
                        ghost_seen_laps = gs.lap_times.len();
                        ghost_seen_cps = gs.cp_visited.iter().filter(|v| **v).count();
                    }
                    let c = gs.cp_visited.iter().filter(|v| **v).count();
                    for i in ghost_seen_cps..c {
                        ghost_marks.insert((gs.lap_count, i), gs.t);
                    }
                    ghost_seen_cps = c;
                }
                let s = &me.sim;
                // chocs
                if s.wall_hits > seen_hits {
                    for _ in seen_hits..s.wall_hits {
                        bonks.push(Bonk { pos: s.car.pos, lap: s.lap_count, at: now });
                    }
                    seen_hits = s.wall_hits;
                }
                // traces de pneus
                let skid_now = (s.car.is_drifting || s.car.braking) && s.car.speed.abs() > 2.0;
                if skid_now {
                    let (h, p) = (s.car.heading as f32, vec2(s.car.pos[0] as f32, s.car.pos[1] as f32));
                    let (fwd, side) = (vec2(h.cos(), h.sin()), vec2(-h.sin(), h.cos()));
                    if !skidding {
                        skids.push(Skid { left: vec![], right: vec![] });
                        if skids.len() > 400 {
                            skids.remove(0);
                        }
                    }
                    let k = skids.last_mut().unwrap();
                    k.left.push(p - fwd * 10.0 + side * 8.5);
                    k.right.push(p - fwd * 10.0 - side * 8.5);
                }
                skidding = skid_now;
                // tours bouclés : PB, records, écart au WR sur la ligne
                let key = record_key(s.track.seed, laps);
                if s.lap_times.len() > seen_laps {
                    for li in seen_laps..s.lap_times.len() {
                        let t = s.lap_times[li];
                        let v = s.track.length() / t / (MAX_SPEED * FPS);
                        let wr = records.wr(&key);
                        let reference = wr.as_ref().map(|w| w.0).or(session_best.as_ref().map(|b| b.0));
                        let [fx, fy, _] = s.track.finish;
                        let n_cp = s.track.checkpoints.len();
                        ghost_delta = match ghost_marks.get(&(li, n_cp)) {
                            Some(gt) => Some(s.t - gt),
                            None if ghost_policy.is_some() => Some(-0.0001), // le fantôme n'y est pas encore : devant
                            None => None,
                        };
                        bubbles.push(Split { pos: vec2(fx as f32, fy as f32), time: t, delta: reference.map(|r| t - r), at: now, ghost: ghost_delta });
                        if session_best.as_ref().map_or(true, |b| t < b.0) {
                            session_best = Some((t, splits_now.clone()));
                        }
                        if !a.play {
                            pb_speed = Some(pb_speed.map_or(v, |p| p.max(v)));
                            if records.speed_record().map_or(true, |r| v > r.0) {
                                records.set_speed(v, gen, s.track.seed, &run_name);
                            }
                            if wr.map_or(true, |w| t < w.0) {
                                records.set_wr(&key, t, gen, &splits_now);
                                let g = WrGhost { lap: t, gen, frames: std::mem::take(&mut lap_traj) };
                                save_wr_ghost(&root, &key, &g);
                                wr_ghost = Some(g);
                            }
                        }
                        splits_now.clear();
                    }
                    lap_traj.clear();
                    lap_start_frame = me.frame;
                    seen_laps = s.lap_times.len();
                    seen_cps = s.cp_visited.iter().filter(|v| **v).count();
                }
                // portes franchies : temps intermédiaire et écart
                let cps = s.cp_visited.iter().filter(|v| **v).count();
                if cps > seen_cps {
                    let t = s.t + DT - s.lap_start_t;
                    for i in seen_cps..cps {
                        if splits_now.len() <= i {
                            splits_now.resize(i + 1, f64::NAN);
                        }
                        splits_now[i] = t;
                        if i == 0 {
                            continue; // la première porte est sur la ligne de départ
                        }
                        let reference = records.wr(&key).map(|w| w.2).filter(|v| v.len() > i).or(session_best.as_ref().map(|b| b.1.clone()));
                        let delta = reference.and_then(|r| r.get(i).copied()).filter(|x| x.is_finite()).map(|r| t - r);
                        let c = s.track.checkpoints[i];
                        ghost_delta = match ghost_marks.get(&(s.lap_count, i)) {
                            Some(gt) => Some(s.t + DT - gt),
                            None if ghost_policy.is_some() => Some(-0.0001),
                            None => None,
                        };
                        bubbles.push(Split { pos: vec2(c[0] as f32, c[1] as f32), time: t, delta, at: now, ghost: ghost_delta });
                    }
                }
                seen_cps = cps;
                if ended {
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
            if let Ok((g, r, gh)) = rx.try_recv() {
                pending = false;
                match r {
                    Ok(p) => {
                        label = gen_label(&g);
                        gen = gen_number(&g);
                        loaded_from = Some(g);
                        policy = Some(p);
                        pb_speed = None;
                    }
                    Err(e) => eprintln!("{e}"),
                }
                if let Some((gp, Ok(p))) = gh {
                    ghost_label = gen_label(&gp);
                    ghost_policy = Some(p);
                }
            }
            let seed = pinned.unwrap_or_else(|| next_seed(&mut hard_i));
            if seed != me.sim.track.seed {
                me.reset(seed);
                tex = art::track_texture(&me.sim.track);
                session_best = None;
            } else {
                me.restart();
            }
            restart = true;
        }
        if restart {
            me.restart();
            if ghost_policy.is_some() {
                let g = ghost.get_or_insert_with(|| Driver::new(me.sim.track.seed, laps));
                g.sim.laps = laps;
                if g.sim.track.seed != me.sim.track.seed {
                    g.reset(me.sim.track.seed);
                } else {
                    g.restart();
                }
            }
            lap_traj.clear();
            lap_start_frame = 0;
            wr_ghost = load_wr_ghost(&root, &record_key(me.sim.track.seed, laps));
            bonks.clear();
            skids.clear();
            bubbles.clear();
            ghost_marks.clear();
            ghost_seen_cps = 0;
            ghost_seen_laps = 0;
            ghost_delta = None;
            splits_now.clear();
            seen_hits = 0;
            seen_laps = 0;
            seen_cps = 0;
            skidding = false;
            acc = 0.0;
        }

        // --- dessin ---
        let s = &me.sim;
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

        // traces de pneus
        let skid_col = Color::new(0.08, 0.08, 0.09, 0.42);
        for k in &skids {
            for pts in [&k.left, &k.right] {
                for w in pts.windows(2) {
                    draw_line(w[0].x, w[0].y, w[1].x, w[1].y, 3.5, skid_col);
                }
            }
        }

        // portes de checkpoint et arrivée
        let half = (s.track.half_width + 10.0) as f32;
        let next = s.next_cp();
        for (i, c) in s.track.checkpoints.iter().enumerate() {
            let (cx, cy, ang) = (c[0] as f32, c[1] as f32, c[2] as f32);
            let d = vec2(ang.cos(), ang.sin()) * half;
            if Some(i) == next {
                draw_line(cx - d.x, cy - d.y, cx + d.x, cy + d.y, 12.0, Color::new(0.3, 0.85, 1.0, 0.25));
                draw_line(cx - d.x, cy - d.y, cx + d.x, cy + d.y, 5.0, Color::new(0.35, 0.9, 1.0, 1.0));
            } else {
                let col = if s.cp_visited[i] { Color::new(1.0, 1.0, 1.0, 0.15) } else { Color::new(1.0, 1.0, 1.0, 0.5) };
                draw_line(cx - d.x, cy - d.y, cx + d.x, cy + d.y, 3.0, col);
            }
            for e in [vec2(cx, cy) - d, vec2(cx, cy) + d] {
                draw_circle(e.x, e.y, 5.0, Color::new(0.1, 0.11, 0.14, 0.9));
            }
        }
        {
            let [fx, fy, fa] = s.track.finish;
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
            let col = if b.lap == s.lap_count { Color::new(1.0, 0.16, 0.16, 0.95) } else { Color::new(0.6, 0.25, 0.25, 0.7) };
            draw_circle(x, y, 10.0, Color::new(0.25, 0.05, 0.05, 0.6));
            draw_line(x - 7.0, y - 7.0, x + 7.0, y + 7.0, 4.0, col);
            draw_line(x - 7.0, y + 7.0, x + 7.0, y - 7.0, 4.0, col);
        }

        // fantômes puis voiture, interpolés
        let alpha = (acc / DT).clamp(0.0, 1.0);
        if let Some(w) = &wr_ghost {
            if !me.sim.done {
                let k = (me.frame.saturating_sub(lap_start_frame) as f64 - 1.0 + alpha).max(0.0);
                let last = w.frames.len() - 1;
                let (i0, i1) = ((k.floor() as usize).min(last), (k.ceil() as usize).min(last));
                let f = (k - k.floor()) as f32;
                let (a0, a1) = (w.frames[i0], w.frames[i1]);
                let mut dh = a1[2] - a0[2];
                if dh > std::f32::consts::PI { dh -= 2.0 * std::f32::consts::PI; }
                if dh < -std::f32::consts::PI { dh += 2.0 * std::f32::consts::PI; }
                let gp = vec2(a0[0] + (a1[0] - a0[0]) * f, a0[1] + (a1[1] - a0[1]) * f);
                draw_car(gp, a0[2] + dh * f, Color::new(1.0, 0.82, 0.2, 0.5), 0.5);
            }
        }
        if let Some(g) = &ghost {
            if ghost_policy.is_some() {
                let (gp, gh) = g.pose(alpha);
                draw_car(gp, gh, Color::new(1.0, 0.6, 0.15, 0.5), 0.5);
            }
        }
        let (pos, heading) = me.pose(alpha);
        if show_lidar && !a.play && me.obs.len() >= 44 {
            for k in 0..9 {
                let ang = heading + (-std::f32::consts::FRAC_PI_2 + k as f32 * std::f32::consts::PI / 8.0);
                let d = me.obs[35 + k] * 400.0;
                let end = pos + vec2(ang.cos(), ang.sin()) * d;
                let col = if me.obs[35 + k] < 0.15 { Color::new(1.0, 0.3, 0.2, 0.55) } else { Color::new(0.4, 1.0, 0.4, 0.25) };
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

        bubbles.retain(|b| now - b.at < 2.5);

        // --- panneau ---
        set_default_camera();
        draw_rectangle(0.0, 0.0, side, sh, Color::from_rgba(18, 20, 26, 255));
        let lap_t = if s.lap_count < s.laps { s.t - s.lap_start_t } else { 0.0 };
        let grey = Color::from_rgba(190, 196, 210, 255);
        let mut lines: Vec<(String, f32, Color)> = vec![];
        if !label.is_empty() {
            lines.push((label.clone(), 26.0, WHITE));
        }
        if a.play {
            lines.push(("Mode pilote".into(), 26.0, WHITE));
        }
        lines.push((format!("Circuit #{}  ·  tour {}/{}", s.track.seed, (s.lap_count + 1).min(s.laps), s.laps), 20.0, grey));
        lines.push((fmt_time(lap_t), 44.0, WHITE));
        let len = s.track.length();
        let best_lap = s.lap_times.iter().cloned().fold(f64::INFINITY, f64::min);
        // une ligne par tour, même vide : le panneau ne bouge pas pendant la course
        for i in 0..s.laps {
            match s.lap_times.get(i) {
                Some(t) => {
                    let v = len / t / (MAX_SPEED * FPS) * 100.0;
                    let c = if *t == best_lap && s.lap_times.len() > 1 { Color::from_rgba(90, 220, 130, 255) } else { WHITE };
                    lines.push((format!("T{}  {}  {:.1} %", i + 1, fmt_time(*t), v), 20.0, c));
                }
                None => lines.push((format!("T{}  --:--.---", i + 1), 20.0, Color::from_rgba(95, 100, 115, 255))),
            }
        }
        if let (Some(g), false) = (&ghost, ghost_label.is_empty()) {
            let gs = &g.sim;
            let txt = match ghost_delta {
                Some(g) if g < -0.00005 && g > -0.001 => "devant".to_string(),
                Some(g) => format!("{}{:.2} s", if g < 0.0 { "-" } else { "+" }, g.abs()),
                None if gs.done => fmt_time(gs.lap_times.iter().sum()),
                None => "-".into(),
            };
            lines.push((format!("Fantôme ({})  {}", ghost_label.to_lowercase().replace("génération", "gén."), txt), 20.0, Color::from_rgba(255, 160, 60, 255)));
        }
        let fmt_gen = |g: Option<u64>| g.map(|g| format!("  (gén. {g})")).unwrap_or_default();
        if !a.play {
            lines.push((format!("PB vitesse  {}", pb_speed.map(|v| format!("{:.1} %", v * 100.0)).unwrap_or("-".into())), 20.0, Color::from_rgba(90, 220, 130, 255)));
            lines.push((
                match records.speed_record() {
                    Some((v, g)) => format!("Record vitesse  {:.1} %{}", v * 100.0, fmt_gen(g)),
                    None => "Record vitesse  -".into(),
                },
                20.0,
                Color::from_rgba(200, 120, 255, 255),
            ));
            lines.push((
                match records.wr(&record_key(s.track.seed, laps)) {
                    Some((t, g, _)) => format!("WR circuit  {}{}", fmt_time(t), fmt_gen(g)),
                    None => "WR circuit  -".into(),
                },
                20.0,
                Color::from_rgba(230, 200, 120, 255),
            ));
        } else if let Some((t, _)) = &session_best {
            lines.push((format!("Meilleur tour  {}", fmt_time(*t)), 20.0, Color::from_rgba(90, 220, 130, 255)));
        }
        if let Some(w) = &wr_ghost {
            lines.push((format!("Fantôme doré : WR {}{}", fmt_time(w.lap), fmt_gen(w.gen)), 18.0, Color::from_rgba(255, 210, 60, 255)));
        }
        let lap_hits = bonks.iter().filter(|b| b.lap == s.lap_count).count();
        lines.push((format!("Chocs  {}   (ce tour : {})", s.wall_hits, lap_hits), 20.0, Color::from_rgba(255, 90, 80, 255)));
        lines.push((format!("{:.0} px/s", s.car.speed.max(0.0) * FPS), 20.0, Color::from_rgba(150, 220, 160, 255)));
        if s.car.is_drifting {
            let (vx, vy) = (s.car.vel[0], s.car.vel[1]);
            let h = s.car.heading;
            let slip = (-vx * h.sin() + vy * h.cos()).atan2((vx * h.cos() + vy * h.sin()).abs()).to_degrees();
            lines.push((format!("DRIFT  {:.0}°", slip.abs()), 24.0, Color::from_rgba(255, 170, 60, 255)));
        } else {
            lines.push((String::new(), 24.0, WHITE)); // place gardée pour DRIFT
        }
        lines.push((format!("{} fps  ·  physique 50 Hz  ·  x{}", get_fps(), speed), 18.0, Color::from_rgba(150, 156, 170, 255)));
        let hgt: f32 = lines.iter().map(|l| l.1 + 6.0).sum::<f32>() + 20.0;
        draw_rectangle(12.0, 12.0, side - 24.0, hgt, Color::from_rgba(30, 33, 42, 255));
        let mut y = 22.0;
        for (t, sz, c) in &lines {
            y += sz;
            draw_text(t, 26.0, y, *sz, *c);
            y += 6.0;
        }
        let keys: &[&str] = if !show_help {
            &["H : aide   C : circuits avec un WR"]
        } else if a.play {
            &["Flèches, ZQSD ou WASD : conduire", "R : recommencer   N : autre circuit", "C : circuits avec un WR", "Espace : pause   H : aide", "Échap : quitter"]
        } else {
            &["N : circuit suivant   R : recommencer", "C : circuits avec un WR", "Espace : pause   +/- : vitesse", "L : lidars   H : aide", "Échap : quitter"]
        };
        for (k, t) in keys.iter().enumerate() {
            draw_text(t, 22.0, sh - 18.0 - 22.0 * (keys.len() - 1 - k) as f32, 18.0, Color::from_rgba(150, 156, 170, 255));
        }
        // écart au passage de la porte ou de la ligne : en haut au centre, comme dans Trackmania
        if let Some(b) = bubbles.last() {
            let age = (now - b.at) as f32;
            let fade = if age > 1.8 { (1.0 - (age - 1.8) / 0.7).max(0.0) } else { 1.0 };
            let cx = side + (sw - side) / 2.0;
            let main_txt = match b.delta {
                Some(d) => format!("{}{:.2}", if d < 0.0 { "-" } else { "+" }, d.abs()),
                None => fmt_time(b.time),
            };
            let main_col = match b.delta {
                Some(d) if d < 0.0 => Color::new(0.35, 0.9, 0.5, fade),
                Some(_) => Color::new(1.0, 0.35, 0.3, fade),
                None => Color::new(1.0, 1.0, 1.0, fade),
            };
            let sub = match (b.delta, b.ghost) {
                (_, Some(g)) if g < -0.00005 && g > -0.001 => format!("{}  ·  devant le fantôme", fmt_time(b.time)),
                (_, Some(g)) => format!("{}  ·  fantôme {}{:.2}", fmt_time(b.time), if g < 0.0 { "-" } else { "+" }, g.abs()),
                (Some(_), None) => fmt_time(b.time),
                (None, None) => String::new(),
            };
            let d1 = measure_text(&main_txt, None, 52, 1.0);
            let d2 = measure_text(&sub, None, 22, 1.0);
            let bw = d1.width.max(d2.width) + 40.0;
            draw_rectangle(cx - bw / 2.0, 14.0, bw, 84.0, Color::new(0.05, 0.06, 0.08, 0.75 * fade));
            draw_text(&main_txt, cx - d1.width / 2.0, 62.0, 52.0, main_col);
            draw_text(&sub, cx - d2.width / 2.0, 88.0, 22.0, Color::new(0.85, 0.87, 0.92, fade));
        }
        if paused {
            draw_text("PAUSE", side + (sw - side) / 2.0 - 50.0, 40.0, 40.0, WHITE);
        }

        if let Some((items, sel)) = &menu {
            draw_menu(items, *sel, me.sim.track.seed, laps);
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
