"""VecEnv de Stable-Baselines3 branché sur le moteur Rust (sim-rs, module `trackai_sim`).

Remplace SubprocVecEnv([GymTimeAttack, ...]) pour l'entraînement : toutes les voitures avancent dans un seul
processus, en parallèle sur les cœurs (rayon), avec la récompense « simple » calculée en Rust.
Mêmes espaces d'observation et d'action que GymTimeAttack : les modèles se chargent indifféremment.
"""
import numpy as np
from gymnasium import spaces
from stable_baselines3.common.vec_env.base_vec_env import VecEnv


class RustVecEnv(VecEnv):
    def __init__(self, n_envs, seed=0, laps=1, obs_version=3, action_set=2, wall_penalty=0.0, time_penalty=0.01,
                 speed_bonus=0.0, track_seeds=None, track_mix=1.0, track_seed=None):
        import trackai_sim
        self.sim = trackai_sim.VecSim(
            n_envs, seed=seed, laps=laps, obs_version=obs_version, action_set=action_set, wall_penalty=wall_penalty,
            time_penalty=time_penalty, speed_bonus=speed_bonus, track_seeds=[int(s) for s in (track_seeds or [])],
            track_mix=track_mix, track_seed=track_seed)
        obs_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.sim.obs_size,), dtype=np.float32)
        super().__init__(n_envs, obs_space, spaces.Discrete(self.sim.n_actions))
        self._actions = None

    def reset(self):
        return self.sim.reset()

    def step_async(self, actions):
        self._actions = np.asarray(actions, dtype=np.int64).reshape(-1)

    def step_wait(self):
        obs, rew, done, ends = self.sim.step(self._actions)
        infos = [{} for _ in range(self.num_envs)]
        for i, info in ends:
            infos[i] = info
        return obs, rew, done, infos

    def close(self):
        pass

    def get_attr(self, attr_name, indices=None):
        return [getattr(self, attr_name, None) for _ in self._get_indices(indices)]

    def set_attr(self, attr_name, value, indices=None):
        setattr(self, attr_name, value)

    def env_method(self, method_name, *args, indices=None, **kwargs):
        return [None for _ in self._get_indices(indices)]

    def env_is_wrapped(self, wrapper_class, indices=None):
        return [False for _ in self._get_indices(indices)]

    def seed(self, seed=None):
        return [None for _ in range(self.num_envs)]
