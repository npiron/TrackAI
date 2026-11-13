//! Calculs flottants reproduits au bit près : `math.hypot` de CPython (pas celui de la libm),
//! sommation par paires de numpy (`np.sum`), modulo flottant de Python.

#[inline]
fn dl_mul(x: f64, y: f64) -> (f64, f64) {
    let hi = x * y;
    (hi, x.mul_add(y, -hi))
}

#[inline]
fn dl_fast_sum(a: f64, b: f64) -> (f64, f64) {
    let hi = a + b;
    (hi, (a - hi) + b)
}

/// `math.hypot(x, y)` de CPython (vector_norm à deux coordonnées).
pub fn hypot(x: f64, y: f64) -> f64 {
    let v = [x.abs(), y.abs()];
    let max = if v[1] > v[0] { v[1] } else { v[0] };
    if max.is_infinite() {
        return max;
    }
    if v[0].is_nan() || v[1].is_nan() {
        return f64::NAN;
    }
    if max == 0.0 {
        return max;
    }
    let max_e = frexp_exp(max);
    if max_e < -1023 {
        // valeurs sous-normales : jamais atteint ici
        return (x * x + y * y).sqrt();
    }
    let scale = ldexp1(-max_e);
    let (mut csum, mut frac1, mut frac2) = (1.0f64, 0.0f64, 0.0f64);
    for &c in &v {
        let xs = c * scale;
        let (phi, plo) = dl_mul(xs, xs);
        let (shi, slo) = dl_fast_sum(csum, phi);
        csum = shi;
        frac1 += plo;
        frac2 += slo;
    }
    let mut h = (csum - 1.0 + (frac1 + frac2)).sqrt();
    let (phi, plo) = dl_mul(-h, h);
    let (shi, slo) = dl_fast_sum(csum, phi);
    csum = shi;
    frac1 += plo;
    frac2 += slo;
    let xx = csum - 1.0 + (frac1 + frac2);
    h += xx / (2.0 * h);
    h / scale
}

/// Exposant e tel que x = m * 2^e avec 0.5 <= m < 1 (frexp), pour x normal > 0.
fn frexp_exp(x: f64) -> i32 {
    let bits = x.to_bits();
    let e = ((bits >> 52) & 0x7ff) as i32;
    if e == 0 {
        // sous-normal
        let m = x * f64::powi(2.0, 54);
        return frexp_exp(m) - 54;
    }
    e - 1022
}

fn ldexp1(e: i32) -> f64 {
    // 2^e exact pour l'intervalle utile
    f64::powi(2.0, e)
}

/// `np.sum` sur un tableau float64 contigu (sommation par paires de numpy).
pub fn np_sum(a: &[f64]) -> f64 {
    let n = a.len();
    if n < 8 {
        let mut s = -0.0f64;
        for &v in a {
            s += v;
        }
        s
    } else if n <= 128 {
        let mut r = [a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7]];
        let mut i = 8;
        while i < n - (n % 8) {
            for j in 0..8 {
                r[j] += a[i + j];
            }
            i += 8;
        }
        let mut res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        while i < n {
            res += a[i];
            i += 1;
        }
        res
    } else {
        let mut n2 = n / 2;
        n2 -= n2 % 8;
        np_sum(&a[..n2]) + np_sum(&a[n2..])
    }
}

/// `x % m` de Python pour des flottants (résultat du signe de m).
#[inline]
pub fn pymod(x: f64, m: f64) -> f64 {
    let mut r = x % m;
    if r != 0.0 {
        if (m < 0.0) != (r < 0.0) {
            r += m;
        }
    } else {
        r = 0.0f64.copysign(m);
    }
    r
}

/// `np.clip(x, lo, hi)`.
#[inline]
pub fn clip(x: f64, lo: f64, hi: f64) -> f64 {
    if x < lo {
        lo
    } else if x > hi {
        hi
    } else {
        x
    }
}

/// `math.sin` : appel isolé, pour que le compilateur ne fusionne pas sin et cos en `sincos`
/// (le sin de `__sincos_stret` d'Apple diffère parfois d'un bit de celui de la libm).
#[inline(never)]
pub fn sin(x: f64) -> f64 {
    x.sin()
}

/// `math.cos` (voir `sin`).
#[inline(never)]
pub fn cos(x: f64) -> f64 {
    x.cos()
}
