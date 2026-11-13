//! Politique du bot exportée par scripts/export_policy.py : MLP tanh, argmax des logits.
use serde::Deserialize;

#[derive(Deserialize)]
struct Layer {
    #[serde(rename = "in")]
    n_in: usize,
    out: usize,
    w: Vec<f32>,
    b: Vec<f32>,
}

#[derive(Deserialize)]
struct Raw {
    obs_version: u8,
    action_set: u8,
    activation: String,
    layers: Vec<Layer>,
    obs_mean: Option<Vec<f64>>,
    obs_var: Option<Vec<f64>>,
    clip_obs: f64,
    epsilon: f64,
}

pub struct Policy {
    pub obs_version: u8,
    pub action_set: u8,
    tanh: bool,
    layers: Vec<Layer>,
    mean: Option<Vec<f64>>,
    std: Option<Vec<f64>>,
    clip: f64,
}

impl Policy {
    pub fn load(path: &str) -> Result<Policy, String> {
        let txt = std::fs::read_to_string(path).map_err(|e| format!("{path} : {e}"))?;
        let r: Raw = serde_json::from_str(&txt).map_err(|e| format!("{path} : {e}"))?;
        let std = r.obs_var.map(|v| v.iter().map(|x| (x + r.epsilon).sqrt()).collect());
        Ok(Policy {
            obs_version: r.obs_version,
            action_set: r.action_set,
            tanh: r.activation == "tanh",
            layers: r.layers,
            mean: r.obs_mean,
            std,
            clip: r.clip_obs,
        })
    }

    /// Action déterministe (argmax) pour une observation brute.
    pub fn act(&self, obs: &[f32]) -> usize {
        let mut x: Vec<f32> = obs
            .iter()
            .enumerate()
            .map(|(i, &o)| match (&self.mean, &self.std) {
                (Some(m), Some(s)) => (((o as f64 - m[i]) / s[i]).clamp(-self.clip, self.clip)) as f32,
                _ => o,
            })
            .collect();
        let last = self.layers.len() - 1;
        for (li, l) in self.layers.iter().enumerate() {
            let mut y = vec![0f32; l.out];
            for o in 0..l.out {
                let row = &l.w[o * l.n_in..(o + 1) * l.n_in];
                let mut acc = l.b[o];
                for (wi, xi) in row.iter().zip(&x) {
                    acc += wi * xi;
                }
                y[o] = if li == last { acc } else if self.tanh { acc.tanh() } else { acc.max(0.0) };
            }
            x = y;
        }
        let mut best = 0;
        for i in 1..x.len() {
            if x[i] > x[best] {
                best = i;
            }
        }
        best
    }
}
