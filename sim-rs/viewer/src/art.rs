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

pub fn track_texture(t: &Track) -> Texture2D {
    let (w, h) = (W as usize, H as usize);
    let d = dist_to_other(&t.mask, 16);
    // vibreurs : rayures le long de la piste (abscisse curviligne du point le plus proche)
    let n = t.spline.len();
    let mut bytes = vec![0u8; w * h * 4];
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let road = t.mask[i];
            let noise = (hash(x as u32, y as u32) % 9) as i32 - 4;
            let (r, g, b): (i32, i32, i32) = if road {
                if d[i] <= 5 {
                    // rayure : alterner selon la position projetée sur la ligne centrale
                    let k = t.closest(x as f64, y as f64);
                    let s = t.cum[k.min(n - 1)];
                    if ((s / 14.0) as i64) % 2 == 0 { (214, 40, 40) } else { (240, 240, 240) }
                } else if d[i] <= 7 {
                    (235, 235, 235)
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
