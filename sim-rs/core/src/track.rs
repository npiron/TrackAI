//! Circuits longs (variante 2) : miroir de src/game/track.py (`generate_procedural_track(seed, variant=2)`).
use crate::consts::*;
use crate::pymath::{cos, np_sum, pymod, sin};
use crate::pyrand::PyRandom;
use crate::stamp::STAMP45;
use std::collections::{BTreeMap, BTreeSet, HashSet};

pub const GRID_COLS: i32 = 7;
pub const GRID_ROWS: i32 = 5;
pub const CELL: f64 = 172.0;
pub const V2_HALF_WIDTH: f64 = 45.0;

type Cell = (i32, i32);

pub struct Track {
    pub seed: u64,
    pub spline: Vec<[f64; 2]>,
    /// masque de la route : mask[y * W + x]
    pub mask: Vec<bool>,
    pub checkpoints: Vec<[f64; 3]>,
    pub start_pos: [f64; 2],
    pub start_heading: f64,
    pub finish: [f64; 3],
    pub half_width: f64,
    /// abscisse curviligne cumulée (n + 1 valeurs, la dernière = longueur totale)
    pub cum: Vec<f64>,
    /// sens de la course à chaque porte
    pub cp_dirs: Vec<[f64; 2]>,
}

impl Track {
    #[inline]
    pub fn inside(&self, x: f64, y: f64) -> bool {
        // int() de Python : troncature vers zéro
        let (xi, yi) = (x as i64, y as i64);
        if xi >= 0 && xi < W as i64 && yi >= 0 && yi < H as i64 {
            self.mask[(yi * W as i64 + xi) as usize]
        } else {
            false
        }
    }

    /// Index du point de la ligne centrale le plus proche (argmin numpy : premier minimum).
    pub fn closest(&self, x: f64, y: f64) -> usize {
        let mut best = f64::INFINITY;
        let mut bi = 0;
        for (i, p) in self.spline.iter().enumerate() {
            let dx = p[0] - x;
            let dy = p[1] - y;
            let d = dx * dx + dy * dy;
            if d < best {
                best = d;
                bi = i;
            }
        }
        bi
    }

    /// Comme `closest`, mais en cherchant autour de `hint` (le point trouvé à l'image précédente) :
    /// la voiture avance de quelques points par image. Si le résultat est loin de la route, recherche complète.
    pub fn closest_near(&self, x: f64, y: f64, hint: usize) -> usize {
        let n = self.spline.len();
        let w = 80usize.min(n / 2);
        let mut best = f64::INFINITY;
        let mut bi = hint;
        for k in 0..=2 * w {
            let i = (hint + n + k - w) % n;
            let p = self.spline[i];
            let dx = p[0] - x;
            let dy = p[1] - y;
            let d = dx * dx + dy * dy;
            if d < best || (d == best && i < bi) {
                best = d;
                bi = i;
            }
        }
        // au bord de la fenêtre, ou trop loin de la ligne centrale : on ne sait pas, recherche complète
        let edge = (bi + n - (hint + n - w) % n) % n;
        if edge == 0 || edge == 2 * w || best > (self.half_width * 1.6).powi(2) {
            return self.closest(x, y);
        }
        bi
    }

    pub fn length(&self) -> f64 {
        self.cum[self.cum.len() - 1]
    }
}

fn nb(c: Cell) -> [Cell; 4] {
    [(c.0 + 1, c.1), (c.0 - 1, c.1), (c.0, c.1 + 1), (c.0, c.1 - 1)]
}

fn has_hole_or_pinch(cells: &HashSet<Cell>) -> bool {
    for x in -1..GRID_COLS {
        for y in -1..GRID_ROWS {
            let q = [
                cells.contains(&(x, y)),
                cells.contains(&(x + 1, y)),
                cells.contains(&(x, y + 1)),
                cells.contains(&(x + 1, y + 1)),
            ];
            if q == [true, false, false, true] || q == [false, true, true, false] {
                return true;
            }
        }
    }
    let mut outside: HashSet<Cell> = HashSet::new();
    let mut todo = vec![(-1, -1)];
    while let Some(c) = todo.pop() {
        if outside.contains(&c) || cells.contains(&c) || !(-1 <= c.0 && c.0 <= GRID_COLS && -1 <= c.1 && c.1 <= GRID_ROWS) {
            continue;
        }
        outside.insert(c);
        todo.extend_from_slice(&nb(c));
    }
    ((GRID_COLS + 2) * (GRID_ROWS + 2)) as usize - outside.len() - cells.len() != 0
}

fn polyomino(rng: &mut PyRandom, n_cells: i64) -> Option<HashSet<Cell>> {
    let x0 = rng.randrange(GRID_COLS as u64) as i32;
    let y0 = rng.randrange(GRID_ROWS as u64) as i32;
    let mut cells: HashSet<Cell> = HashSet::new();
    cells.insert((x0, y0));
    let mut banned: HashSet<Cell> = HashSet::new();
    while (cells.len() as i64) < n_cells {
        let mut cand: BTreeSet<Cell> = BTreeSet::new();
        for x in cells.iter() {
            for c in nb(*x) {
                if !cells.contains(&c) && !banned.contains(&c) && 0 <= c.0 && c.0 < GRID_COLS && 0 <= c.1 && c.1 < GRID_ROWS {
                    cand.insert(c);
                }
            }
        }
        if cand.is_empty() {
            break;
        }
        let cand: Vec<Cell> = cand.into_iter().collect(); // trié comme les tuples Python
        let w: Vec<f64> = cand
            .iter()
            .map(|c| if nb(*c).iter().filter(|n| cells.contains(n)).count() == 1 { 1.0 } else { 0.12 })
            .collect();
        let c = cand[rng.choice_weighted(&w)];
        cells.insert(c);
        if has_hole_or_pinch(&cells) {
            cells.remove(&c);
            banned.insert(c);
        }
    }
    if cells.len() >= 6 { Some(cells) } else { None }
}

fn outline(cells: &HashSet<Cell>) -> Option<Vec<Cell>> {
    let mut edges: BTreeMap<Cell, Cell> = BTreeMap::new();
    for &(x, y) in cells.iter() {
        for (a, b, n) in [
            ((x, y), (x + 1, y), (x, y - 1)),
            ((x + 1, y), (x + 1, y + 1), (x + 1, y)),
            ((x + 1, y + 1), (x, y + 1), (x, y + 1)),
            ((x, y + 1), (x, y), (x - 1, y)),
        ] {
            if !cells.contains(&n) {
                edges.insert(a, b);
            }
        }
    }
    let start = *edges.keys().next()?;
    let mut lp = vec![start];
    let mut v = edges[&start];
    while v != start {
        if !edges.contains_key(&v) || lp.len() > 400 {
            return None;
        }
        lp.push(v);
        v = edges[&v];
    }
    if lp.len() != edges.len() {
        return None;
    }
    let n = lp.len();
    let mut corners = Vec::new();
    for i in 0..n {
        let prev = lp[(i + n - 1) % n];
        let nxt = lp[(i + 1) % n];
        if (lp[i].0 - prev.0, lp[i].1 - prev.1) != (nxt.0 - lp[i].0, nxt.1 - lp[i].1) {
            corners.push(lp[i]);
        }
    }
    Some(corners)
}

#[inline]
fn norm(v: [f64; 2]) -> f64 {
    (v[0] * v[0] + v[1] * v[1]).sqrt()
}

fn fillet_path(corners: &[[f64; 2]], rng: &mut PyRandom, spacing: f64) -> Vec<[f64; 2]> {
    let n = corners.len();
    let p = corners;
    // (p_in, p_out, r, u1, u2)
    let mut arcs: Vec<([f64; 2], [f64; 2], f64, [f64; 2], [f64; 2])> = Vec::with_capacity(n);
    for i in 0..n {
        let a = p[(i + n - 1) % n];
        let v = p[i];
        let b = p[(i + 1) % n];
        let va = [v[0] - a[0], v[1] - a[1]];
        let bv = [b[0] - v[0], b[1] - v[1]];
        let (nva, nbv) = (norm(va), norm(bv));
        let u1 = [va[0] / nva, va[1] / nva];
        let u2 = [bv[0] / nbv, bv[1] / nbv];
        let dot = u1[0] * u2[0] + u1[1] * u2[1];
        let turn = f64::max(-1.0, f64::min(1.0, dot)).acos();
        let mut r = rng.uniform(72.0, 200.0);
        let mut d = r * (turn / 2.0).tan();
        let dmax = 0.5 * f64::min(nva, nbv);
        if d > dmax {
            d = dmax;
            r = dmax / (turn / 2.0).tan();
        }
        arcs.push((
            [v[0] - u1[0] * d, v[1] - u1[1] * d],
            [v[0] + u2[0] * d, v[1] + u2[1] * d],
            r,
            u1,
            u2,
        ));
    }
    let mut out = Vec::new();
    for i in 0..n {
        let (p_in, p_out, r, u1, u2) = arcs[i];
        let side = if (u1[0] * u2[1] - u1[1] * u2[0]) > 0.0 { 1.0 } else { -1.0 };
        let nrm = [-u1[1] * side, u1[0] * side];
        let c = [p_in[0] + nrm[0] * r, p_in[1] + nrm[1] * r];
        let a0 = (p_in[1] - c[1]).atan2(p_in[0] - c[0]);
        let a1 = (p_out[1] - c[1]).atan2(p_out[0] - c[0]);
        let da = pymod(a1 - a0 + PI, 2.0 * PI) - PI;
        let k = std::cmp::max(2, (da.abs() * r / spacing) as i64);
        for t in 0..k {
            let ang = a0 + da * t as f64 / k as f64;
            out.push([c[0] + r * cos(ang), c[1] + r * sin(ang)]);
        }
        let q = arcs[(i + 1) % n].0;
        let qp = [q[0] - p_out[0], q[1] - p_out[1]];
        let l = norm(qp);
        let k = std::cmp::max(1, (l / spacing) as i64);
        for t in 0..k {
            let tf = t as f64;
            let kf = k as f64;
            out.push([p_out[0] + qp[0] * tf / kf, p_out[1] + qp[1] * tf / kf]);
        }
    }
    out
}

fn track_v2(rng: &mut PyRandom) -> Option<Vec<[f64; 2]>> {
    let n_cells = rng.randint(12, 24);
    let cells = polyomino(rng, n_cells)?;
    let corners = outline(&cells)?;
    if corners.len() < 4 {
        return None;
    }
    let xs: Vec<i32> = corners.iter().map(|c| c.0).collect();
    let ys: Vec<i32> = corners.iter().map(|c| c.1).collect();
    let (xmax, xmin) = (*xs.iter().max().unwrap(), *xs.iter().min().unwrap());
    let (ymax, ymin) = (*ys.iter().max().unwrap(), *ys.iter().min().unwrap());
    // (W - (max + min) * CELL) / 2 : arithmétique entière puis division vraie
    let ox = (W as i64 - (xmax + xmin) as i64 * CELL as i64) as f64 / 2.0;
    let oy = (H as i64 - (ymax + ymin) as i64 * CELL as i64) as f64 / 2.0;
    let mut pts = Vec::with_capacity(corners.len());
    for &(gx, gy) in &corners {
        let jx = rng.uniform(-5.0, 5.0);
        let jy = rng.uniform(-5.0, 5.0);
        pts.push([ox + (gx as i64 * CELL as i64) as f64 + jx, oy + (gy as i64 * CELL as i64) as f64 + jy]);
    }
    Some(fillet_path(&pts, rng, 1.5))
}

fn track_ok(a: &[[f64; 2]], min_radius: f64, half_width: f64) -> bool {
    let clearance = 2.0 * half_width + 30.0;
    let n = a.len();
    if n < 100 {
        return false;
    }
    let k = 10;
    let mut rmin = f64::INFINITY;
    for i in 0..n {
        let p0 = a[i];
        let p1 = a[(i + k) % n];
        let p2 = a[(i + 2 * k) % n];
        let ab = norm([p1[0] - p0[0], p1[1] - p0[1]]);
        let bc = norm([p2[0] - p1[0], p2[1] - p1[1]]);
        let ca = norm([p2[0] - p0[0], p2[1] - p0[1]]);
        let cross = ((p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])).abs();
        if cross < 1e-9 {
            continue;
        }
        let r = ab * bc * ca / (2.0 * cross);
        if r < rmin {
            rmin = r;
        }
    }
    if rmin < min_radius {
        return false;
    }
    let (mut xmin, mut xmax, mut ymin, mut ymax) = (f64::INFINITY, f64::NEG_INFINITY, f64::INFINITY, f64::NEG_INFINITY);
    for p in a {
        xmin = xmin.min(p[0]);
        xmax = xmax.max(p[0]);
        ymin = ymin.min(p[1]);
        ymax = ymax.max(p[1]);
    }
    if xmin < half_width + 5.0 || xmax > W as f64 - half_width - 5.0 {
        return false;
    }
    if ymin < half_width + 5.0 || ymax > H as f64 - half_width - 5.0 {
        return false;
    }
    let sub: Vec<[f64; 2]> = a.iter().step_by(8).cloned().collect();
    let diffs: Vec<f64> = (0..n - 1).map(|i| norm([a[i + 1][0] - a[i][0], a[i + 1][1] - a[i][1]])).collect();
    let seg = np_sum(&diffs) / n as f64 * 8.0;
    let m = sub.len();
    for i in 0..m {
        for j in 0..m {
            let g = (i as i64 - j as i64).unsigned_abs() as usize;
            let gap = std::cmp::min(g, m - g) as f64 * seg;
            if gap < 3.0 * clearance {
                continue;
            }
            let d = norm([sub[i][0] - sub[j][0], sub[i][1] - sub[j][1]]);
            if !(d >= clearance) {
                return false;
            }
        }
    }
    true
}

fn finish_track(spline: Vec<[f64; 2]>, seed: u64, half_width: f64) -> Track {
    // masque : un disque pygame de rayon half_width (45) à chaque point de la ligne centrale
    assert!(half_width == 45.0, "seul le rayon 45 est tamponné");
    let mut mask = vec![false; (W * H) as usize];
    for p in &spline {
        let (cx, cy) = (p[0] as i64 as i32, p[1] as i64 as i32);
        for &(dy, x0, x1) in STAMP45 {
            let y = cy + dy;
            if y < 0 || y >= H {
                continue;
            }
            let xa = (cx + x0).max(0);
            let xb = (cx + x1).min(W - 1);
            if xa <= xb {
                let row = (y * W) as usize;
                mask[row + xa as usize..=row + xb as usize].fill(true);
            }
        }
    }
    let l = spline.len();
    let step = l / 8;
    let mut checkpoints = Vec::new();
    let mut i = 0;
    while i < l {
        if checkpoints.len() >= 8 {
            break;
        }
        let p = spline[i];
        let np = spline[(i + 5) % l];
        let angle = (np[1] - p[1]).atan2(np[0] - p[0]);
        checkpoints.push([p[0], p[1], angle + PI / 2.0]);
        i += step;
    }
    let start_pos = spline[0];
    let p_next = spline[5];
    let start_heading = (p_next[1] - start_pos[1]).atan2(p_next[0] - start_pos[0]);
    let pf = spline[l - 10];
    let pfn = spline[(l - 10 + 5) % l];
    let finish = [pf[0], pf[1], (pfn[1] - pf[1]).atan2(pfn[0] - pf[0]) + PI / 2.0];
    let mut cum = Vec::with_capacity(l + 1);
    cum.push(0.0);
    let mut acc = 0.0;
    for i in 0..l {
        let a = spline[i];
        let b = spline[(i + 1) % l];
        acc += norm([b[0] - a[0], b[1] - a[1]]);
        cum.push(acc);
    }
    let mut t = Track {
        seed,
        spline,
        mask,
        checkpoints,
        start_pos,
        start_heading,
        finish,
        half_width,
        cum,
        cp_dirs: vec![],
    };
    // sens de la course à chaque porte (miroir de TimeAttackEnv._cp_direction)
    t.cp_dirs = t
        .checkpoints
        .iter()
        .map(|&[cx, cy, ang]| {
            let (mut tx, mut ty) = (-sin(ang), cos(ang));
            let j = t.closest(cx, cy);
            let a = t.spline[j];
            let b = t.spline[(j + 1) % t.spline.len()];
            if (b[0] - a[0]) * tx + (b[1] - a[1]) * ty < 0.0 {
                tx = -tx;
                ty = -ty;
            }
            [tx, ty]
        })
        .collect();
    t
}

use std::sync::{Arc, Mutex, OnceLock};

/// Circuits déjà générés (les circuits imposés reviennent souvent) : au plus CACHE_MAX, les plus anciens sortent.
const CACHE_MAX: usize = 512;
static CACHE: OnceLock<Mutex<(std::collections::HashMap<u64, Arc<Track>>, std::collections::VecDeque<u64>)>> = OnceLock::new();

/// Circuit partagé (en cache) pour une graine.
pub fn get(seed: u64) -> Result<Arc<Track>, String> {
    let cache = CACHE.get_or_init(|| Mutex::new((std::collections::HashMap::new(), std::collections::VecDeque::new())));
    if let Some(t) = cache.lock().unwrap().0.get(&seed) {
        return Ok(t.clone());
    }
    let t = Arc::new(generate(seed)?);
    let mut c = cache.lock().unwrap();
    if !c.0.contains_key(&seed) {
        c.0.insert(seed, t.clone());
        c.1.push_back(seed);
        while c.1.len() > CACHE_MAX {
            if let Some(old) = c.1.pop_front() {
                c.0.remove(&old);
            }
        }
    }
    Ok(t)
}

/// `generate_procedural_track(seed, variant=2)`.
pub fn generate(seed: u64) -> Result<Track, String> {
    let mut rng = PyRandom::new(seed);
    for _ in 0..2000 {
        if let Some(sp) = track_v2(&mut rng) {
            if !sp.is_empty() && track_ok(&sp, 78.0, V2_HALF_WIDTH) {
                return Ok(finish_track(sp, seed, V2_HALF_WIDTH));
            }
        }
    }
    Err(format!("aucun tracé valide pour la graine {seed}"))
}
