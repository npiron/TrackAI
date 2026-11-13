//! Circuit pré-rendu en texture : herbe rayée, bas-côté, vibreurs rouge et blanc, route.
use macroquad::prelude::*;
use std::collections::VecDeque;
use trackai_core::consts::{H, W};
use trackai_core::track::Track;

/// Distance (en pas de 4-voisinage, plafonnée à `cap`) de chaque pixel au plus proche pixel de l'autre nature.
fn dist_to_other(mask: &[bool], cap: u8) -> Vec<u8> {
    let (w, h) = (W as usize, H as usize);
    let mut d = vec![cap; w * h];
    let mut q = VecDeque::new();
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let m = mask[i];
            let border = (x > 0 && mask[i - 1] != m) || (x + 1 < w && mask[i + 1] != m)
                || (y > 0 && mask[i - w] != m) || (y + 1 < h && mask[i + w] != m);
            if border {
                d[i] = 0;
                q.push_back(i);
            }
        }
    }
    while let Some(i) = q.pop_front() {
        let nd = d[i] + 1;
        if nd >= cap {
            continue;
        }
        let (x, y) = (i % w, i / w);
        let mut go = |j: usize| {
            if mask[j] == mask[i] && d[j] > nd {
                d[j] = nd;
                q.push_back(j);
            }
        };
        if x > 0 { go(i - 1); }
        if x + 1 < w { go(i + 1); }
        if y > 0 { go(i - w); }
        if y + 1 < h { go(i + w); }
    }
    d
}

fn hash(x: u32, y: u32) -> u32 {
    let mut h = x.wrapping_mul(374761393) ^ y.wrapping_mul(668265263);
    h = (h ^ (h >> 13)).wrapping_mul(1274126177);
    h ^ (h >> 16)
}

/// Courbure signée (1/px, >0 : virage à droite à l'écran) de la ligne centrale, lissée puis élargie
/// (max sur une fenêtre) pour que les vibreurs débordent un peu à l'entrée et à la sortie des virages.
fn corner_map(t: &Track) -> Vec<f64> {
    let sp = &t.spline;
    let n = sp.len();
    let k = 10;
    let head = |i: usize| -> f64 {
        let a = sp[i % n];
        let b = sp[(i + k) % n];
        (b[1] - a[1]).atan2(b[0] - a[0])
    };
    let raw: Vec<f64> = (0..n)
        .map(|i| {
            let (h0, h1) = (head(i + n - k), head(i));
            let mut d = h1 - h0;
            while d > std::f64::consts::PI { d -= 2.0 * std::f64::consts::PI; }
            while d < -std::f64::consts::PI { d += 2.0 * std::f64::consts::PI; }
            let arc = t.cum[(i + k).min(n)] - t.cum[i.saturating_sub(k)];
            if arc > 1e-6 { d / arc } else { 0.0 }
        })
        .collect();
    let wdw = 25;
    (0..n)
        .map(|i| {
            let mut best = 0.0f64;
            for j in 0..=2 * wdw {
                let v = raw[(i + n + j - wdw) % n];
                if v.abs() > best.abs() {
                    best = v;
                }
            }
            best
        })
        .collect()
}

pub fn track_texture(t: &Track) -> Texture2D {
    let (w, h) = (W as usize, H as usize);
    let d = dist_to_other(&t.mask, 16);
    let curv = corner_map(t);
    let n = t.spline.len();
    let mut bytes = vec![0u8; w * h * 4];
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let road = t.mask[i];
            let noise = (hash(x as u32, y as u32) % 9) as i32 - 4;
            let (r, g, b): (i32, i32, i32) = if road {
                if d[i] <= 7 {
                    // vibreurs seulement dans les virages : toujours à la corde, à l'extérieur si c'est serré
                    let k = t.closest(x as f64, y as f64);
                    let c = curv[k.min(n - 1)];
                    let a = t.spline[k];
                    let b = t.spline[(k + 1) % n];
                    let side = (b[0] - a[0]) * (y as f64 - a[1]) - (b[1] - a[1]) * (x as f64 - a[0]); // >0 : à droite
                    let inside = c != 0.0 && (side > 0.0) == (c > 0.0);
                    let radius = if c != 0.0 { 1.0 / c.abs() } else { f64::INFINITY };
                    let kerb = d[i] <= 5 && ((inside && radius < 260.0) || (!inside && radius < 120.0));
                    if kerb {
                        let s = t.cum[k.min(n - 1)];
                        if ((s / 14.0) as i64) % 2 == 0 { (214, 40, 40) } else { (240, 240, 240) }
                    } else if d[i] <= 2 {
                        (230, 230, 230) // ligne blanche de bord de route
                    } else {
                        (92 + noise, 94 + noise, 100 + noise)
                    }
                } else {
                    (92 + noise, 94 + noise, 100 + noise)
                }
            } else if d[i] <= 9 {
                (88 + noise, 160 + noise, 74 + noise)
            } else {
                let stripe = ((x + y) / 60) % 2 == 0;
                if stripe { (60 + noise, 114 + noise, 52 + noise) } else { (66 + noise, 124 + noise, 57 + noise) }
            };
            let o = i * 4;
            bytes[o] = r.clamp(0, 255) as u8;
            bytes[o + 1] = g.clamp(0, 255) as u8;
            bytes[o + 2] = b.clamp(0, 255) as u8;
            bytes[o + 3] = 255;
        }
    }
    let img = Image { bytes, width: w as u16, height: h as u16 };
    let tex = Texture2D::from_image(&img);
    tex.set_filter(FilterMode::Linear);
    tex
}
