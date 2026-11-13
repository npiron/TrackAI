//! Course contre la montre (miroir de src/game/env.py, `TimeAttackEnv`, circuits longs).
use crate::consts::*;
use crate::physics::{drive, DriveState};
use crate::pymath::{clip, cos, hypot, np_sum, pymod, sin};
use crate::track::{generate, Track};

pub const V2_POINT_DISTANCES: [f64; 8] = [30.0, 60.0, 100.0, 150.0, 220.0, 300.0, 420.0, 560.0];
pub const V2_RAY_LENGTH: f64 = 400.0;
pub const V1_RAY_LENGTH: f64 = 150.0;
pub const OBS_V2_SIZE: usize = 10 + 3 * 8 + 1 + 9;
pub const OBS_V3_SIZE: usize = OBS_V2_SIZE + 6;

fn v2_lidar_angles() -> [f64; 9] {
    let mut a = [0.0; 9];
    for (i, v) in a.iter_mut().enumerate() {
        *v = -PI / 2.0 + i as f64 * PI / 8.0;
    }
    a
}

fn v1_lidar_angles() -> [f64; 5] {
    [-PI / 2.0, -PI / 4.0, 0.0, PI / 4.0, PI / 2.0]
}

fn wall_dirs() -> [[f64; 2]; 16] {
    // np.linspace(0, 2π, 16, endpoint=False) : i * (2π / 16)
    let step = (2.0 * PI - 0.0) / 16.0;
    let mut d = [[0.0; 2]; 16];
    for (i, v) in d.iter_mut().enumerate() {
        let a = i as f64 * step + 0.0;
        *v = [cos(a), sin(a)];
    }
    d
}

#[derive(Clone, Debug, Default)]
pub struct Car {
    pub pos: [f64; 2],
    pub vel: [f64; 2],
    pub heading: f64,
    pub speed: f64,
    pub steering: f64,
    pub angular_velocity: f64,
    pub is_drifting: bool,
    pub braking: bool,
}

pub struct Sim {
    pub track: Track,
    pub car: Car,
    pub laps: usize,
    pub lap_count: usize,
    pub lap_times: Vec<f64>,
    pub lap_start_t: f64,
    pub t: f64,
    pub done: bool,
    pub cp_visited: Vec<bool>,
    pub prev_steer: f64,
    pub wall_hits: u64,
    pub wall_contacts: u64,
    wall_prev: bool,
    frames_since_wall: i64,
    pub ghost: Vec<[f64; 2]>,
    pub best_time: Option<f64>,
    pub best_ghost: Vec<[f64; 2]>,
    wall_dirs: [[f64; 2]; 16],
}

impl Sim {
    pub fn new(seed: u64, laps: usize) -> Result<Sim, String> {
        let track = generate(seed)?;
        let mut s = Sim {
            track,
            car: Car::default(),
            laps: laps.max(1),
            lap_count: 0,
            lap_times: vec![],
            lap_start_t: 0.0,
            t: 0.0,
            done: false,
            cp_visited: vec![],
            prev_steer: 0.0,
            wall_hits: 0,
            wall_contacts: 0,
            wall_prev: false,
            frames_since_wall: 1_000_000,
            ghost: vec![],
            best_time: None,
            best_ghost: vec![],
            wall_dirs: wall_dirs(),
        };
        s.restart();
        Ok(s)
    }

    /// Nouveau circuit (graine) puis départ.
    pub fn reset(&mut self, seed: u64) -> Result<(), String> {
        if seed != self.track.seed {
            self.track = generate(seed)?;
        }
        self.best_time = None;
        self.best_ghost.clear();
        self.restart();
        Ok(())
    }

    /// Départ sur le circuit courant.
    pub fn restart(&mut self) {
        self.car = Car {
            pos: self.track.start_pos,
            vel: [0.0, 0.0],
            heading: self.track.start_heading,
            ..Default::default()
        };
        self.t = 0.0;
        self.done = false;
        self.lap_count = 0;
        self.lap_times.clear();
        self.lap_start_t = 0.0;
        self.cp_visited = vec![false; self.track.checkpoints.len()];
        self.ghost.clear();
        self.prev_steer = 0.0;
        self.wall_hits = 0;
        self.wall_contacts = 0;
        self.wall_prev = false;
        self.frames_since_wall = 1_000_000;
    }

    #[inline]
    fn speed_along_heading(&self) -> f64 {
        let (c, s) = (cos(self.car.heading), sin(self.car.heading));
        self.car.vel[0] * c + self.car.vel[1] * s
    }

    /// Une image (1/FPS). Renvoie la récompense de l'env (100 à chaque tour bouclé).
    pub fn step(&mut self, steer: f64, accel: f64, brake: f64) -> f64 {
        let steer = clip(steer, -1.0, 1.0);
        let accel = clip(accel, 0.0, 1.0);
        let brake = clip(brake, 0.0, 1.0);
        let ds = drive(
            DriveState {
                vel: self.car.vel,
                heading: self.car.heading,
                steering: self.car.steering,
                angular_velocity: self.car.angular_velocity,
                drifting: self.car.is_drifting,
            },
            steer,
            accel,
            brake,
        );
        self.car.vel = ds.vel;
        self.car.heading = ds.heading;
        self.car.steering = ds.steering;
        self.car.angular_velocity = ds.angular_velocity;
        self.car.is_drifting = ds.drifting;
        self.car.speed = self.speed_along_heading();
        self.prev_steer = steer;
        self.car.braking = brake > 0.0 && self.car.speed > 0.5;

        // murs
        let new_pos = [self.car.pos[0] + self.car.vel[0], self.car.pos[1] + self.car.vel[1]];
        let mut wall_now = false;
        if self.track.inside(new_pos[0], new_pos[1]) {
            self.car.pos = new_pos;
        } else {
            self.wall_hits += 1;
            if !self.wall_prev {
                self.wall_contacts += 1;
            }
            wall_now = true;
            let inward = self.wall_normal(self.car.pos);
            let tangent = [-inward[1], inward[0]];
            let vel = self.car.vel;
            let norm_v = (vel[0] * vel[0] + vel[1] * vel[1]).sqrt();
            let v_t = vel[0] * tangent[0] + vel[1] * tangent[1];
            let impact = if norm_v > 1e-6 { f64::max(0.0, 1.0 - (v_t / norm_v).powi(2)).sqrt() } else { 0.0 };
            let first = self.frames_since_wall > WALL_CONTACT_GAP;
            let keep = 1.0 - (if first { WALL_HIT_LOSS } else { WALL_RUB_LOSS }) - WALL_IMPACT_LOSS * impact * impact;
            self.frames_since_wall = 0;
            let km = f64::max(0.0, keep);
            self.car.vel = [
                tangent[0] * v_t * km + inward[0] * norm_v * impact * WALL_BOUNCE,
                tangent[1] * v_t * km + inward[1] * norm_v * impact * WALL_BOUNCE,
            ];
            let along = tangent[1].atan2(tangent[0]);
            let mut diff = pymod(along - self.car.heading + PI, 2.0 * PI) - PI;
            if diff.abs() > PI / 2.0 {
                diff = pymod(diff + 2.0 * PI, 2.0 * PI) - PI;
            }
            let nose_in = f64::max(impact, 1.0 - f64::min(norm_v / 2.0, 1.0));
            self.car.heading += diff * WALL_ALIGN * nose_in;
            self.car.angular_velocity *= 1.0 - nose_in;
            let mut placed = false;
            for push in [0.0, 1.0, 2.0] {
                let moved = [
                    self.car.pos[0] + self.car.vel[0] + inward[0] * push,
                    self.car.pos[1] + self.car.vel[1] + inward[1] * push,
                ];
                if self.track.inside(moved[0], moved[1]) {
                    self.car.pos = moved;
                    placed = true;
                    break;
                }
            }
            if !placed {
                self.car.vel = [0.0, 0.0];
            }
            self.car.speed = self.speed_along_heading();
        }
        self.wall_prev = wall_now;
        if !wall_now {
            self.frames_since_wall += 1;
        }

        // bords de l'écran (sécurité)
        let (x, y) = (self.car.pos[0], self.car.pos[1]);
        if x < 0.0 || x > W as f64 || y < 0.0 || y > H as f64 {
            self.car.vel = [self.car.vel[0] * 0.3, self.car.vel[1] * 0.3];
            self.car.speed *= 0.3;
            self.car.pos[0] = f64::max(5.0, f64::min((W - 5) as f64, self.car.pos[0]));
            self.car.pos[1] = f64::max(5.0, f64::min((H - 5) as f64, self.car.pos[1]));
        }

        self.update_checkpoints();

        let mut lap_finished = false;
        if self.check_finish() {
            let t_end = self.t + 1.0 / FPS;
            self.lap_times.push(t_end - self.lap_start_t);
            self.lap_count += 1;
            if self.lap_count < self.laps {
                lap_finished = true;
                self.lap_start_t = t_end;
                self.cp_visited.iter_mut().for_each(|v| *v = false);
            } else {
                self.done = true;
                if self.best_time.map_or(true, |b| self.t < b) {
                    self.best_time = Some(self.t);
                    self.best_ghost = self.ghost.clone();
                }
            }
        }

        let p = self.car.pos;
        let record = match self.ghost.last() {
            None => true,
            Some(g) => {
                let (dx, dy) = (p[0] - g[0], p[1] - g[1]);
                (dx * dx + dy * dy).sqrt() > 5.0
            }
        };
        if record {
            self.ghost.push(p);
        }
        self.t += 1.0 / FPS;
        if self.done || lap_finished { 100.0 } else { 0.0 }
    }

    fn wall_normal(&self, pos: [f64; 2]) -> [f64; 2] {
        let mut acc = [0.0f64, 0.0f64];
        for r in [4.0, 8.0] {
            for d in &self.wall_dirs {
                if self.track.inside(pos[0] + d[0] * r, pos[1] + d[1] * r) {
                    acc[0] += d[0];
                    acc[1] += d[1];
                }
            }
        }
        let n = (acc[0] * acc[0] + acc[1] * acc[1]).sqrt();
        if n > 1e-6 {
            return [acc[0] / n, acc[1] / n];
        }
        let j = self.track.closest(pos[0], pos[1]);
        let c = self.track.spline[j];
        let to_c = [c[0] - pos[0], c[1] - pos[1]];
        let n = (to_c[0] * to_c[0] + to_c[1] * to_c[1]).sqrt();
        if n > 1e-6 { [to_c[0] / n, to_c[1] / n] } else { [0.0, 0.0] }
    }

    pub fn next_cp(&self) -> Option<usize> {
        self.cp_visited.iter().position(|v| !v)
    }

    fn update_checkpoints(&mut self) {
        let Some(i) = self.next_cp() else { return };
        let [cx, cy, ang] = self.track.checkpoints[i];
        let [tx, ty] = self.track.cp_dirs[i];
        let rel = [self.car.pos[0] - cx, self.car.pos[1] - cy];
        let along = rel[0] * tx + rel[1] * ty;
        let across = rel[0] * cos(ang) + rel[1] * sin(ang);
        let half = self.track.half_width + 10.0;
        let nose = CAR_NOSE * f64::max(0.0, cos(self.car.heading - ty.atan2(tx)));
        if -CHECKPOINT_RADIUS < along + nose && along + nose >= 0.0 && across.abs() <= half {
            self.cp_visited[i] = true;
        }
    }

    fn check_finish(&self) -> bool {
        if !self.cp_visited.iter().all(|v| *v) {
            return false;
        }
        let [fx, fy, fang] = self.track.finish;
        let rel = [self.car.pos[0] - fx, self.car.pos[1] - fy];
        let along = rel[0] * sin(fang) - rel[1] * cos(fang);
        let across = rel[0] * cos(fang) + rel[1] * sin(fang);
        let half = self.track.half_width + 10.0;
        0.0 <= along && along < FINISH_RADIUS && across.abs() <= half
    }

    /// Lidars (miroir de cast_rays_jit) : distances normalisées en float32.
    pub fn cast_rays(&self, angles: &[f64], ray_length: f64, out: &mut Vec<f32>) {
        let (px, py, h) = (self.car.pos[0], self.car.pos[1], self.car.heading);
        let step = 2.0;
        let n_steps = ((ray_length - 4.0) / step) as i64;
        for &a in angles {
            let rel = a as f32 as f64; // angles passés en float32 au JIT
            let abs = h + rel;
            let (rx, ry) = (cos(abs), sin(abs));
            let mut fin = ray_length;
            for s in 0..n_steps {
                let d = 4.0 + s as f64 * step;
                let x = (px + rx * d) as i64;
                let y = (py + ry * d) as i64;
                if x < 0 || x >= W as i64 || y < 0 || y >= H as i64 || !self.track.mask[(y * W as i64 + x) as usize] {
                    fin = d;
                    break;
                }
            }
            out.push((fin / ray_length) as f32);
        }
    }

    /// Observation v1 (14 valeurs) ; `lidar` reçoit les 5 lidars (aussi utilisés pour l'affichage).
    pub fn obs_v1(&self, out: &mut Vec<f32>) {
        let car = &self.car;
        let speed_n = car.speed / MAX_SPEED;
        let (hx, hy) = (cos(car.heading), sin(car.heading));
        let (vx, vy) = (car.vel[0], car.vel[1]);
        let local_vx = (vx * hx + vy * hy) / MAX_SPEED;
        let local_vy = (vx * -hy + vy * hx) / MAX_SPEED;
        let target = match self.next_cp() {
            Some(i) => [self.track.checkpoints[i][0], self.track.checkpoints[i][1]],
            None => [self.track.finish[0], self.track.finish[1]],
        };
        let dxg = target[0] - car.pos[0];
        let dyg = target[1] - car.pos[1];
        let dist = (dxg * dxg + dyg * dyg).sqrt();
        let dist_n = f64::min(1.0, dist / (W as f64 * 1.4));
        let tlx = dxg * hx + dyg * hy;
        let tly = -dxg * hy + dyg * hx;
        let (tdx, tdy) = if dist > 0.1 { (tlx / dist, tly / dist) } else { (1.0, 0.0) };
        let on_track = if self.track.inside(car.pos[0], car.pos[1]) { 1.0 } else { 0.0 };
        for v in [speed_n, local_vx, local_vy, car.angular_velocity, self.prev_steer, dist_n, tdx, tdy, on_track] {
            out.push(v as f32);
        }
        self.cast_rays(&v1_lidar_angles(), V1_RAY_LENGTH, out);
    }

    /// Observation v2 (44) ou v3 (50).
    pub fn obs(&self, version: u8, out: &mut Vec<f32>) {
        out.clear();
        let mut v1 = Vec::with_capacity(14);
        self.obs_v1(&mut v1);
        if version == 1 {
            out.extend_from_slice(&v1);
            return;
        }
        out.extend_from_slice(&v1[..9]);
        let car = &self.car;
        let sp = &self.track.spline;
        let cum = &self.track.cum;
        let total = self.track.length();
        let n = sp.len();
        let pos = car.pos;
        let i0 = self.track.closest(pos[0], pos[1]);
        let (ch, sh) = (cos(car.heading), sin(car.heading));
        out.push(car.steering as f32);
        let mut pts = [[0.0f64; 2]; 8];
        for (k, &da) in V2_POINT_DISTANCES.iter().enumerate() {
            let target = pymod(cum[i0] + da, total);
            // searchsorted(cum[:-1], target, side="right") - 1
            let c = &cum[..n];
            let idx = c.partition_point(|&v| v <= target);
            let j = ((idx as i64 - 1).rem_euclid(n as i64)) as usize;
            pts[k] = sp[j];
        }
        for p in &pts {
            let (dx, dy) = (p[0] - pos[0], p[1] - pos[1]);
            let lx = dx * ch + dy * sh;
            let ly = -dx * sh + dy * ch;
            let d = hypot(lx, ly);
            let dn = f64::min(1.0, d / (V2_POINT_DISTANCES[7] * 1.25));
            let ang = ly.atan2(lx);
            out.push(dn as f32);
            out.push(sin(ang) as f32);
            out.push(cos(ang) as f32);
        }
        let mut chain = [[0.0f64; 2]; 9];
        chain[0] = sp[i0];
        chain[1..].copy_from_slice(&pts);
        let mut heads = [0.0f64; 8];
        for k in 0..8 {
            heads[k] = (chain[k + 1][1] - chain[k][1]).atan2(chain[k + 1][0] - chain[k][0]);
        }
        let mut dh = [0.0f64; 7];
        for k in 0..7 {
            dh[k] = pymod(heads[k + 1] - heads[k] + PI, 2.0 * PI) - PI;
        }
        let curv = clip(np_sum(&dh) / 7.0 / (PI / 4.0), -1.0, 1.0);
        out.push(curv as f32);
        self.cast_rays(&v2_lidar_angles(), V2_RAY_LENGTH, out);
        if version == 2 {
            return;
        }
        // v3
        let a = sp[i0];
        let b = sp[(i0 + 1) % n];
        let t = [b[0] - a[0], b[1] - a[1]];
        let mut tl = hypot(t[0], t[1]);
        if tl == 0.0 {
            tl = 1.0;
        }
        let rel = [pos[0] - a[0], pos[1] - a[1]];
        let lateral = (t[0] * rel[1] - t[1] * rel[0]) / tl;
        let offset = clip(lateral / self.track.half_width, -1.5, 1.5);
        let bends = [
            clip(np_sum(&dh[0..3]) / (PI / 2.0), -1.0, 1.0),
            clip(np_sum(&dh[3..5]) / (PI / 2.0), -1.0, 1.0),
            clip(np_sum(&dh[5..]) / (PI / 2.0), -1.0, 1.0),
        ];
        let (vx, vy) = (car.vel[0], car.vel[1]);
        let slip = if hypot(vx, vy) > 0.5 {
            let h = car.heading;
            let v_long = vx * cos(h) + vy * sin(h);
            let v_lat = -vx * sin(h) + vy * cos(h);
            v_lat.atan2(v_long.abs())
        } else {
            0.0
        };
        out.push(offset as f32);
        for b in bends {
            out.push(b as f32);
        }
        out.push(if car.is_drifting { 1.0 } else { 0.0 });
        out.push(clip(slip / (PI / 4.0), -1.0, 1.0) as f32);
    }
}
