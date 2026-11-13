//! Décision complète du bot en Rust (miroir de GymTimeAttack, reward_mode="simple") et N voitures
//! qui avancent en parallèle (rayon) : c'est ce que l'entraînement appelle à chaque pas.
use crate::consts::*;
use crate::env::Sim;
use crate::pymath::pymod;
use crate::pyrand::PyRandom;
use rayon::prelude::*;

pub const SIMPLE_LAP_REWARD: f64 = 100.0;

/// Jeux d'actions (volant, gaz, frein) : 1 = 9 touches, 2 = 15 actions avec demi-braquages.
pub fn action_set(k: u8) -> Vec<(f64, f64, f64)> {
    if k == 1 {
        vec![
            (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0),
            (-1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 0.0, 1.0), (1.0, 0.0, 1.0),
        ]
    } else {
        let mut v = Vec::new();
        for s in [-1.0, -0.5, 0.0, 0.5, 1.0] {
            for (a, b) in [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)] {
                v.push((s, a, b));
            }
        }
        v
    }
}

#[derive(Clone, Debug)]
pub struct Config {
    pub laps: usize,
    pub obs_version: u8,
    pub action_set: u8,
    pub action_repeat: usize,
    pub wall_penalty: f64,
    pub time_penalty: f64,
    pub speed_bonus: f64,
    pub k_prog: Option<f64>,
    /// circuits imposés : une part `track_mix` des épisodes y est tirée, le reste est aléatoire
    pub track_seeds: Vec<u64>,
    pub track_mix: f64,
    /// circuit unique (prioritaire)
    pub track_seed: Option<u64>,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            laps: 1,
            obs_version: 3,
            action_set: 2,
            action_repeat: BOT_DECISION_FRAMES,
            wall_penalty: 0.0,
            time_penalty: 0.01,
            speed_bonus: 0.0,
            k_prog: None,
            track_seeds: vec![],
            track_mix: 1.0,
            track_seed: None,
        }
    }
}

/// Bilan d'un épisode terminé (ce que lit train_long.py).
#[derive(Clone, Debug, Default)]
pub struct EpisodeEnd {
    pub env: usize,
    pub reward: f64,
    pub length: u64,
    pub is_success: bool,
    pub truncated: bool,
    pub end_cause: &'static str,
    pub laps_done: usize,
    pub checkpoints_reached: usize,
    pub wall_hits: u64,
    pub wall_contacts: u64,
    pub total_time: f64,
    pub lap_times: Vec<f64>,
    pub lap_speeds: Vec<f64>,
    pub track_seed: u64,
    /// progress, time_penalty, wall, env, speed
    pub components: [f64; 5],
    pub terminal_obs: Vec<f32>,
}

pub struct Agent {
    pub sim: Sim,
    rng: PyRandom,
    actions: Vec<(f64, f64, f64)>,
    episode_steps: u64,
    decisions: u64,
    stuck: u32,
    simple_s: f64,
    laps_rewarded: usize,
    ep_reward: f64,
    comps: [f64; 5],
}

impl Agent {
    pub fn new(cfg: &Config, seed: u64) -> Result<Agent, String> {
        let mut rng = PyRandom::new(seed);
        let first = Self::pick_track(cfg, &mut rng);
        let sim = Sim::new(first, cfg.laps)?;
        let mut a = Agent {
            sim,
            rng,
            actions: action_set(cfg.action_set),
            episode_steps: 0,
            decisions: 0,
            stuck: 0,
            simple_s: 0.0,
            laps_rewarded: 0,
            ep_reward: 0.0,
            comps: [0.0; 5],
        };
        a.begin_episode();
        Ok(a)
    }

    fn pick_track(cfg: &Config, rng: &mut PyRandom) -> u64 {
        if let Some(s) = cfg.track_seed {
            return s;
        }
        if !cfg.track_seeds.is_empty() && rng.random() < cfg.track_mix {
            return cfg.track_seeds[rng.randrange(cfg.track_seeds.len() as u64) as usize];
        }
        rng.randrange(1u64 << 31)
    }

    fn centerline_s(&self) -> f64 {
        let i = self.sim.track.closest(self.sim.car.pos[0], self.sim.car.pos[1]);
        self.sim.track.cum[i]
    }

    fn begin_episode(&mut self) {
        self.simple_s = self.centerline_s();
        self.episode_steps = 0;
        self.decisions = 0;
        self.stuck = 0;
        self.laps_rewarded = 0;
        self.ep_reward = 0.0;
        self.comps = [0.0; 5];
    }

    pub fn reset(&mut self, cfg: &Config) -> Result<(), String> {
        let seed = Self::pick_track(cfg, &mut self.rng);
        self.sim.laps = cfg.laps.max(1);
        self.sim.reset(seed)?;
        self.begin_episode();
        Ok(())
    }

    /// Une image. Renvoie (récompense, terminé, tronqué, cause).
    fn frame(&mut self, cfg: &Config, action: usize) -> (f64, bool, bool, &'static str) {
        self.episode_steps += 1;
        if self.episode_steps >= 2000 * cfg.laps as u64 {
            return (0.0, false, true, "timeout");
        }
        let (steer, accel, brake) = self.actions[action];
        let hits_before = self.sim.wall_hits;
        let env_r = self.sim.step(steer, accel, brake);
        let new_hits = (self.sim.wall_hits - hits_before) as f64;
        let speed = f64::max(0.0, self.sim.car.speed) / MAX_SPEED;
        if speed < 0.05 {
            self.stuck += 1;
        } else {
            self.stuck = 0;
        }
        if self.stuck >= 150 {
            self.comps[3] -= 100.0;
            return (-100.0, true, false, "wall_stuck");
        }
        let total_len = self.sim.track.length();
        let k_prog = cfg.k_prog.unwrap_or(SIMPLE_LAP_REWARD / total_len);
        let s = self.centerline_s();
        let mut ds = s - self.simple_s;
        ds = pymod(ds + total_len / 2.0, total_len) - total_len / 2.0;
        self.simple_s = s;
        if !self.sim.track.inside(self.sim.car.pos[0], self.sim.car.pos[1]) {
            ds = 0.0;
        }
        let progress = k_prog * ds;
        let wall = cfg.wall_penalty * new_hits;
        let mut spd = 0.0;
        if cfg.speed_bonus != 0.0 && self.sim.lap_count > self.laps_rewarded {
            for &t in &self.sim.lap_times[self.laps_rewarded..self.sim.lap_count] {
                if t > 0.0 {
                    spd += cfg.speed_bonus * total_len / t / (MAX_SPEED * FPS);
                }
            }
            self.laps_rewarded = self.sim.lap_count;
        }
        let total = progress - cfg.time_penalty + wall + env_r + spd;
        self.comps[0] += progress;
        self.comps[1] -= cfg.time_penalty;
        self.comps[2] += wall;
        self.comps[3] += env_r;
        self.comps[4] += spd;
        let done = self.sim.done;
        (total, done, false, if done { "finish" } else { "" })
    }

    /// Une décision (action_repeat images). Écrit l'observation dans `obs` ; en fin d'épisode,
    /// renvoie le bilan et repart sur un nouveau circuit (comme un VecEnv de SB3).
    pub fn decide(&mut self, cfg: &Config, action: usize, obs: &mut Vec<f32>, env_idx: usize) -> (f64, bool, Option<EpisodeEnd>) {
        let mut total = 0.0;
        let (mut term, mut trunc, mut cause) = (false, false, "");
        for _ in 0..cfg.action_repeat.max(1) {
            let (r, te, tr, c) = self.frame(cfg, action);
            total += r;
            if te || tr {
                term = te;
                trunc = tr;
                cause = c;
                break;
            }
        }
        self.decisions += 1;
        self.ep_reward += total;
        self.sim.obs(cfg.obs_version, obs);
        if !(term || trunc) {
            return (total, false, None);
        }
        let len = self.sim.track.length();
        let end = EpisodeEnd {
            env: env_idx,
            reward: self.ep_reward,
            length: self.decisions,
            is_success: term && self.sim.lap_count >= self.sim.laps,
            truncated: trunc,
            end_cause: cause,
            laps_done: self.sim.lap_count,
            checkpoints_reached: self.sim.cp_visited.iter().filter(|v| **v).count(),
            wall_hits: self.sim.wall_hits,
            wall_contacts: self.sim.wall_contacts,
            total_time: self.sim.lap_times.iter().sum(),
            lap_times: self.sim.lap_times.clone(),
            lap_speeds: self.sim.lap_times.iter().filter(|t| **t > 0.0).map(|t| len / t / (MAX_SPEED * FPS)).collect(),
            track_seed: self.sim.track.seed,
            components: self.comps,
            terminal_obs: obs.clone(),
        };
        // nouvel épisode : l'observation renvoyée est celle du départ
        if let Err(e) = self.reset(cfg) {
            eprintln!("trackai : {e}");
        }
        self.sim.obs(cfg.obs_version, obs);
        (total, true, Some(end))
    }
}

/// N voitures indépendantes qui avancent en parallèle.
pub struct VecGym {
    pub cfg: Config,
    pub agents: Vec<Agent>,
    pub obs_size: usize,
}

impl VecGym {
    pub fn new(cfg: Config, n: usize, seed: u64) -> Result<VecGym, String> {
        let agents: Result<Vec<Agent>, String> = (0..n).into_par_iter().map(|i| Agent::new(&cfg, seed + i as u64)).collect();
        let obs_size = match cfg.obs_version {
            1 => 14,
            2 => crate::env::OBS_V2_SIZE,
            _ => crate::env::OBS_V3_SIZE,
        };
        Ok(VecGym { cfg, agents: agents?, obs_size })
    }

    pub fn observe(&self, out: &mut [f32]) {
        let k = self.obs_size;
        out.par_chunks_mut(k).zip(self.agents.par_iter()).for_each_init(
            || Vec::with_capacity(64),
            |buf, (dst, a)| {
                a.sim.obs(self.cfg.obs_version, buf);
                dst.copy_from_slice(buf);
            },
        );
    }

    pub fn reset_all(&mut self, out: &mut [f32]) -> Result<(), String> {
        let cfg = &self.cfg;
        self.agents.par_iter_mut().try_for_each(|a| a.reset(cfg))?;
        self.observe(out);
        Ok(())
    }

    /// Un pas pour toutes les voitures : obs (n*k), récompenses, fins ; renvoie les bilans des épisodes finis.
    pub fn step(&mut self, actions: &[i64], obs: &mut [f32], rewards: &mut [f32], dones: &mut [bool]) -> Vec<EpisodeEnd> {
        let k = self.obs_size;
        let cfg = &self.cfg;
        let ends: Vec<Option<EpisodeEnd>> = self
            .agents
            .par_iter_mut()
            .zip(obs.par_chunks_mut(k))
            .zip(rewards.par_iter_mut().zip(dones.par_iter_mut()))
            .enumerate()
            .map_init(
                || Vec::with_capacity(64),
                |buf, (i, ((a, o), (r, d)))| {
                    let (rew, done, end) = a.decide(cfg, actions[i] as usize, buf, i);
                    o.copy_from_slice(buf);
                    *r = rew as f32;
                    *d = done;
                    end
                },
            )
            .collect();
        ends.into_iter().flatten().collect()
    }
}
