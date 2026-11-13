//! Liaison Python du moteur TrackAI : `trackai_sim.Sim`.
use numpy::{PyArray1, PyArray2, PyArrayMethods};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use trackai_core::consts::{H, W};
use trackai_core::env::Sim as CoreSim;
use trackai_core::gym::{Config, VecGym};
use numpy::{IntoPyArray, PyReadonlyArray1};
use pyo3::types::PyDict;

#[pyclass(unsendable)]
struct Sim {
    s: CoreSim,
    buf: Vec<f32>,
}

#[pymethods]
impl Sim {
    #[new]
    #[pyo3(signature = (seed, laps=1))]
    fn new(seed: u64, laps: usize) -> PyResult<Self> {
        let s = CoreSim::new(seed, laps).map_err(PyValueError::new_err)?;
        Ok(Sim { s, buf: Vec::with_capacity(64) })
    }

    /// Nouveau circuit (graine) et départ.
    fn reset(&mut self, seed: u64) -> PyResult<()> {
        self.s.reset(seed).map_err(PyValueError::new_err)
    }

    /// Départ sur le circuit courant.
    fn restart(&mut self) {
        self.s.restart();
    }

    /// Une image ; renvoie la récompense de l'env (100 par tour bouclé).
    fn step(&mut self, steer: f64, accel: f64, brake: f64) -> f64 {
        self.s.step(steer, accel, brake)
    }

    /// Observation (version 1, 2 ou 3) en float32.
    fn obs<'py>(&mut self, py: Python<'py>, version: u8) -> Bound<'py, PyArray1<f32>> {
        self.s.obs(version, &mut self.buf);
        PyArray1::from_slice(py, &self.buf)
    }

    /// Les 5 lidars de l'observation v1 (affichage).
    fn lidar_v1(&self) -> Vec<f32> {
        let mut v = Vec::with_capacity(14);
        self.s.obs_v1(&mut v);
        v[9..].to_vec()
    }

    fn inside(&self, x: f64, y: f64) -> bool {
        self.s.track.inside(x, y)
    }

    #[getter]
    fn seed(&self) -> u64 { self.s.track.seed }
    #[getter]
    fn pos(&self) -> (f64, f64) { (self.s.car.pos[0], self.s.car.pos[1]) }
    #[getter]
    fn vel(&self) -> (f64, f64) { (self.s.car.vel[0], self.s.car.vel[1]) }
    #[getter]
    fn heading(&self) -> f64 { self.s.car.heading }
    #[getter]
    fn speed(&self) -> f64 { self.s.car.speed }
    #[getter]
    fn steering(&self) -> f64 { self.s.car.steering }
    #[getter]
    fn angular_velocity(&self) -> f64 { self.s.car.angular_velocity }
    #[getter]
    fn is_drifting(&self) -> bool { self.s.car.is_drifting }
    #[getter]
    fn braking(&self) -> bool { self.s.car.braking }
    #[getter]
    fn t(&self) -> f64 { self.s.t }
    #[getter]
    fn done(&self) -> bool { self.s.done }
    #[getter]
    fn laps(&self) -> usize { self.s.laps }
    #[setter]
    fn set_laps(&mut self, v: usize) { self.s.laps = v.max(1) }
    #[getter]
    fn lap_count(&self) -> usize { self.s.lap_count }
    #[getter]
    fn lap_times(&self) -> Vec<f64> { self.s.lap_times.clone() }
    #[getter]
    fn lap_start_t(&self) -> f64 { self.s.lap_start_t }
    #[getter]
    fn cp_visited(&self) -> Vec<bool> { self.s.cp_visited.clone() }
    #[getter]
    fn wall_hits(&self) -> u64 { self.s.wall_hits }
    #[getter]
    fn wall_contacts(&self) -> u64 { self.s.wall_contacts }
    #[getter]
    fn prev_steer(&self) -> f64 { self.s.prev_steer }
    #[getter]
    fn best_time(&self) -> Option<f64> { self.s.best_time }
    #[getter]
    fn ghost(&self) -> Vec<(f64, f64)> { self.s.ghost.iter().map(|p| (p[0], p[1])).collect() }
    #[getter]
    fn best_ghost(&self) -> Vec<(f64, f64)> { self.s.best_ghost.iter().map(|p| (p[0], p[1])).collect() }
    #[getter]
    fn half_width(&self) -> f64 { self.s.track.half_width }
    #[getter]
    fn start_pos(&self) -> (f64, f64) { (self.s.track.start_pos[0], self.s.track.start_pos[1]) }
    #[getter]
    fn start_heading(&self) -> f64 { self.s.track.start_heading }
    #[getter]
    fn finish_pos(&self) -> (f64, f64, f64) { let f = self.s.track.finish; (f[0], f[1], f[2]) }
    #[getter]
    fn checkpoints(&self) -> Vec<(f64, f64, f64)> { self.s.track.checkpoints.iter().map(|c| (c[0], c[1], c[2])).collect() }
    #[getter]
    fn arc_lengths<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f64>> { PyArray1::from_slice(py, &self.s.track.cum) }
    #[getter]
    fn spline_points<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray2<f64>> {
        let n = self.s.track.spline.len();
        let flat: Vec<f64> = self.s.track.spline.iter().flat_map(|p| [p[0], p[1]]).collect();
        PyArray1::from_vec(py, flat).reshape([n, 2]).unwrap()
    }
    /// Masque de la route (H, W) : True = route.
    #[getter]
    fn occupancy_grid<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray2<bool>> {
        PyArray1::from_slice(py, &self.s.track.mask).reshape([H as usize, W as usize]).unwrap()
    }
}

/// N voitures en parallèle (entraînement) : décision complète, récompense simple, fins d'épisode.
#[pyclass(unsendable)]
struct VecSim {
    v: VecGym,
}

#[pymethods]
impl VecSim {
    #[new]
    #[pyo3(signature = (n, seed=0, laps=1, obs_version=3, action_set=2, action_repeat=2, wall_penalty=0.0,
                        time_penalty=0.01, speed_bonus=0.0, k_prog=None, track_seeds=Vec::new(), track_mix=1.0, track_seed=None))]
    #[allow(clippy::too_many_arguments)]
    fn new(n: usize, seed: u64, laps: usize, obs_version: u8, action_set: u8, action_repeat: usize, wall_penalty: f64,
           time_penalty: f64, speed_bonus: f64, k_prog: Option<f64>, track_seeds: Vec<u64>, track_mix: f64,
           track_seed: Option<u64>) -> PyResult<Self> {
        let cfg = Config { laps, obs_version, action_set, action_repeat, wall_penalty, time_penalty, speed_bonus, k_prog,
                           track_seeds, track_mix, track_seed };
        Ok(VecSim { v: VecGym::new(cfg, n, seed).map_err(PyValueError::new_err)? })
    }

    #[getter]
    fn num_envs(&self) -> usize { self.v.agents.len() }
    #[getter]
    fn obs_size(&self) -> usize { self.v.obs_size }
    #[getter]
    fn n_actions(&self) -> usize { trackai_core::gym::action_set(self.v.cfg.action_set).len() }

    /// Nouveaux circuits pour toutes les voitures ; renvoie les observations (n, k).
    fn reset<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyArray2<f32>>> {
        let n = self.v.agents.len();
        let mut obs = vec![0f32; n * self.v.obs_size];
        self.v.reset_all(&mut obs).map_err(PyValueError::new_err)?;
        Ok(obs.into_pyarray(py).reshape([n, self.v.obs_size]).unwrap())
    }

    /// Un pas : renvoie (obs (n, k), récompenses (n,), fins (n,), liste de (index, bilan) des épisodes finis).
    fn step<'py>(&mut self, py: Python<'py>, actions: PyReadonlyArray1<'py, i64>)
        -> PyResult<(Bound<'py, PyArray2<f32>>, Bound<'py, PyArray1<f32>>, Bound<'py, PyArray1<bool>>, Vec<(usize, Bound<'py, PyDict>)>)> {
        let n = self.v.agents.len();
        let k = self.v.obs_size;
        let acts = actions.as_slice()?;
        if acts.len() != n {
            return Err(PyValueError::new_err("une action par voiture"));
        }
        let mut obs = vec![0f32; n * k];
        let mut rew = vec![0f32; n];
        let mut done = vec![false; n];
        let ends = py.detach(|| self.v.step(acts, &mut obs, &mut rew, &mut done));
        let mut infos = Vec::with_capacity(ends.len());
        for e in ends {
            let d = PyDict::new(py);
            let ep = PyDict::new(py);
            ep.set_item("r", e.reward)?;
            ep.set_item("l", e.length)?;
            d.set_item("episode_stats", ep)?;
            d.set_item("is_success", e.is_success)?;
            d.set_item("TimeLimit.truncated", e.truncated)?;
            d.set_item("end_cause", e.end_cause)?;
            d.set_item("laps_done", e.laps_done)?;
            d.set_item("checkpoints_reached", e.checkpoints_reached)?;
            d.set_item("wall_hits", e.wall_hits)?;
            d.set_item("wall_contacts", e.wall_contacts)?;
            d.set_item("total_time", e.total_time)?;
            d.set_item("lap_times", e.lap_times)?;
            d.set_item("lap_speeds", e.lap_speeds)?;
            d.set_item("track_seed", e.track_seed)?;
            let c = PyDict::new(py);
            for (name, v) in ["progress", "time_penalty", "wall", "env", "speed"].iter().zip(e.components) {
                c.set_item(*name, v)?;
            }
            d.set_item("ep_reward_components", c)?;
            d.set_item("terminal_observation", e.terminal_obs.into_pyarray(py))?;
            infos.push((e.env, d));
        }
        Ok((obs.into_pyarray(py).reshape([n, k]).unwrap(), rew.into_pyarray(py), done.into_pyarray(py), infos))
    }
}

#[pymodule]
fn trackai_sim(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Sim>()?;
    m.add_class::<VecSim>()?;
    Ok(())
}
