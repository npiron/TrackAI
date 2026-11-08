"""Gros entraînement par renforcement pur (PPO, depuis zéro) sur les circuits longs aléatoires.

Pas de professeur : récompense = progression le long de la piste - pénalité de temps (+ petite pénalité
par choc, les exploits sont permis). Observation v2. Une « génération » est sauvée tous les --gen-steps pas
dans --out-dir (gen_001.zip + _vecnormalize.pkl), pour suivre les progrès et faire la vidéo d'évolution.

Usage : .venv/bin/python scripts/train_long.py --minutes 180
        (reprise : --init data/checkpoints/long/gen_012.zip)
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np


def make_env(rank, seed, wall_penalty):
    def _f():
        from src.rl.wrappers import GymTimeAttack
        env = GymTimeAttack(render_mode=None, procedural=True, laps=1, obs_version=2, track_variant=2,
                            reward_mode="simple", wall_penalty=wall_penalty)
        env.reset(seed=seed + rank)
        return env
    return _f


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--minutes", type=float, default=180)
    p.add_argument("--n-envs", type=int, default=16)
    p.add_argument("--gen-steps", type=int, default=3_000_000)
    p.add_argument("--early", type=int, nargs="*", default=[20_000, 50_000, 100_000, 200_000, 400_000, 800_000, 1_500_000],
                   help="générations rapprochées au début (pour voir l'IA partir de zéro)")
    p.add_argument("--wall-penalty", type=float, default=-0.5)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--ent", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--init", default=None)
    p.add_argument("--out-dir", default="data/checkpoints/long")
    a = p.parse_args(argv)

    import torch
    torch.set_num_threads(2)
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize

    os.makedirs(a.out_dir, exist_ok=True)
    venv = VecMonitor(SubprocVecEnv([make_env(i, a.seed * 100, a.wall_penalty) for i in range(a.n_envs)]))
    if a.init:
        venv = VecNormalize.load(a.init[:-4] + "_vecnormalize.pkl", venv)
        model = PPO.load(a.init, env=venv, device="cpu")
        gen0 = int(os.path.basename(a.init)[4:7])
    else:
        venv = VecNormalize(venv, norm_obs=True, norm_reward=True, clip_obs=10.0, gamma=0.995)
        model = PPO("MlpPolicy", venv, device="cpu", seed=a.seed, learning_rate=a.lr,
                    n_steps=max(64, 4096 // a.n_envs), batch_size=1024, n_epochs=4, gamma=0.995,
                    gae_lambda=0.95, clip_range=0.2, ent_coef=a.ent,
                    policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256])))
        gen0 = 0
    log_path = os.path.join(a.out_dir, "progress.csv")
    new_log = not os.path.exists(log_path)

    class Cb(BaseCallback):
        def _on_training_start(self):
            self.t0, self.gen = time.time(), gen0
            self.marks = [m for m in a.early if m > self.num_timesteps] if a.init is None else []
            self.next_save = self.marks.pop(0) if self.marks else self.num_timesteps + a.gen_steps
            self.laps, self.prog, self.hits = [], [], []
            self.f = open(log_path, "a", newline="")
            self.w = csv.writer(self.f)
            if new_log:
                self.w.writerow(["gen", "timesteps", "minutes", "pas_s", "episodes", "taux_tour_fini",
                                 "checkpoints_moy", "chocs_moy"])

        def _on_step(self):
            for info in self.locals["infos"]:
                if "episode" in info:
                    self.laps.append(1.0 if info.get("laps_done", 0) >= 1 else 0.0)
                    self.prog.append(info.get("checkpoints_reached", 0))
                    self.hits.append(info.get("wall_hits", 0))
            if self.num_timesteps >= self.next_save:
                self.gen += 1
                self.next_save = self.marks.pop(0) if self.marks else self.next_save + a.gen_steps
                base = os.path.join(a.out_dir, f"gen_{self.gen:03d}")
                self.model.save(base)
                self.training_env.save(base + "_vecnormalize.pkl")
                dt = time.time() - self.t0
                row = [self.gen, self.num_timesteps, round(dt / 60, 1), round(self.num_timesteps / max(dt, 1)),
                       len(self.laps), round(float(np.mean(self.laps)), 3) if self.laps else 0,
                       round(float(np.mean(self.prog)), 2) if self.prog else 0,
                       round(float(np.mean(self.hits)), 1) if self.hits else 0]
                self.w.writerow(row)
                self.f.flush()
                print("génération", row, flush=True)
                self.laps, self.prog, self.hits = [], [], []
            return time.time() - self.t0 < a.minutes * 60

    model.learn(total_timesteps=10**10, callback=Cb(), reset_num_timesteps=a.init is None)
    final = os.path.join(a.out_dir, "last")
    model.save(final)
    venv.save(final + "_vecnormalize.pkl")
    venv.close()
    print("fin :", final, flush=True)


if __name__ == "__main__":
    main()
