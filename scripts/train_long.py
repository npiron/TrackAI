"""Gros entraînement par renforcement pur (PPO, depuis zéro) sur les circuits longs aléatoires.

Pas de professeur : récompense = progression le long de la piste - pénalité de temps - pénalité nette
par pas en contact avec un mur (frotter les murs ne paie pas ; les autres exploits sont permis). Observation v2. Une « génération » est sauvée tous les --gen-steps pas
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


# Indicateurs de stabilité PPO suivis par génération (entropie, écart à l'ancienne politique, critique)
TRAIN_KEYS = ("train/entropy_loss", "train/approx_kl", "train/clip_fraction", "train/value_loss",
              "train/explained_variance")


def make_env(rank, seed, wall_penalty, laps=1, time_penalty=None, track_seed=None):
    def _f():
        from src.rl.wrappers import GymTimeAttack
        kw = {} if time_penalty is None else {"time_penalty": time_penalty}
        env = GymTimeAttack(render_mode=None, procedural=True, laps=laps, obs_version=2, track_variant=2,
                            reward_mode="simple", wall_penalty=wall_penalty, track_seed=track_seed, **kw)
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
    p.add_argument("--wall-penalty", type=float, default=0.0,
                   help="par pas en contact avec un mur (un tour rapporte ~+100). 0 : c'est la physique qui punit les murs")
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--time-penalty", type=float, default=None, help="par pas (défaut du wrapper : 0.01)")
    p.add_argument("--ent", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--init", default=None)
    p.add_argument("--track-seed", type=int, default=None, help="s'entraîner sur un seul circuit (son numéro)")
    p.add_argument("--clip", type=float, default=None, help="clip_range PPO (reprise : 0.1 conseillé)")
    p.add_argument("--fresh-reward-scale", action="store_true",
                   help="reprise : remet à zéro l'échelle des récompenses (VecNormalize) et la mémoire d'Adam")
    p.add_argument("--out-dir", default="data/checkpoints/long")
    a = p.parse_args(argv)

    import torch
    torch.set_num_threads(2)
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize

    os.makedirs(a.out_dir, exist_ok=True)
    venv = VecMonitor(SubprocVecEnv([make_env(i, a.seed * 100, a.wall_penalty, a.laps, a.time_penalty, a.track_seed)
                                      for i in range(a.n_envs)]))
    if a.init:
        venv = VecNormalize.load(a.init[:-4] + "_vecnormalize.pkl", venv)
        over = dict(learning_rate=a.lr, lr_schedule=lambda _: a.lr, ent_coef=a.ent)
        if a.clip is not None:
            over["clip_range"] = lambda _: a.clip
        model = PPO.load(a.init, env=venv, device="cpu", custom_objects=over)
        if a.fresh_reward_scale:
            from stable_baselines3.common.running_mean_std import RunningMeanStd
            venv.ret_rms = RunningMeanStd(shape=())
            model.policy.optimizer.state.clear()
        try:
            gen0 = int(os.path.basename(a.init)[4:7])
        except ValueError:
            gen0 = 0
    else:
        venv = VecNormalize(venv, norm_obs=True, norm_reward=True, clip_obs=10.0, gamma=0.995)
        model = PPO("MlpPolicy", venv, device="cpu", seed=a.seed, learning_rate=a.lr,
                    n_steps=max(64, 4096 // a.n_envs), batch_size=1024, n_epochs=4, gamma=0.995,
                    gae_lambda=0.95, clip_range=0.2, ent_coef=a.ent,
                    policy_kwargs=dict(net_arch=dict(pi=[256, 256], vf=[256, 256])))
        gen0 = 0
    import json
    with open(os.path.join(a.out_dir, "config.json"), "w") as f:
        json.dump(vars(a), f, indent=1)
    log_path = os.path.join(a.out_dir, "progress.csv")
    new_log = not os.path.exists(log_path)

    class Cb(BaseCallback):
        def _on_training_start(self):
            self.t0, self.gen, self.ts0 = time.time(), gen0, self.num_timesteps
            self.marks = [m for m in a.early if m > self.num_timesteps] if a.init is None else []
            self.next_save = self.marks.pop(0) if self.marks else self.num_timesteps + a.gen_steps
            self.laps, self.prog, self.hits = [], [], []
            self.comps, self.train_stats = [], []
            stats_path = os.path.join(a.out_dir, "train_stats.csv")
            new_stats = not os.path.exists(stats_path)
            self.fs = open(stats_path, "a", newline="")
            self.ws = csv.writer(self.fs)
            if new_stats:
                self.ws.writerow(["gen", "timesteps", "ep_reward", "r_progress", "r_time", "r_wall", "r_env",
                                  "contacts_moy"] + [k.split("/")[1] for k in TRAIN_KEYS])
            self.f = open(log_path, "a", newline="")
            self.w = csv.writer(self.f)
            if new_log:
                self.w.writerow(["gen", "timesteps", "minutes", "pas_s", "episodes", "taux_tour_fini",
                                 "checkpoints_moy", "chocs_moy"])

        def _on_rollout_start(self):
            # valeurs de la dernière mise à jour PPO (enregistrées par train(), pas encore effacées)
            vals = self.model.logger.name_to_value
            if all(k in vals for k in TRAIN_KEYS):
                self.train_stats.append([float(vals[k]) for k in TRAIN_KEYS])

        def _on_step(self):
            for info in self.locals["infos"]:
                if "episode" in info:
                    c = info.get("ep_reward_components", {})
                    self.comps.append([info["episode"]["r"], c.get("progress", 0.0), c.get("time_penalty", 0.0),
                                       c.get("wall", 0.0), c.get("env", 0.0), info.get("wall_contacts", 0)])
                    self.laps.append(1.0 if info.get("laps_done", 0) >= a.laps else 0.0)
                    self.prog.append(info.get("checkpoints_reached", 0))
                    self.hits.append(info.get("wall_hits", 0))
            if self.num_timesteps >= self.next_save:
                self.gen += 1
                self.next_save = self.marks.pop(0) if self.marks else self.next_save + a.gen_steps
                base = os.path.join(a.out_dir, f"gen_{self.gen:03d}")
                self.model.save(base)
                self.training_env.save(base + "_vecnormalize.pkl")
                dt = time.time() - self.t0
                row = [self.gen, self.num_timesteps, round(dt / 60, 1), round((self.num_timesteps - self.ts0) / max(dt, 1)),
                       len(self.laps), round(float(np.mean(self.laps)), 3) if self.laps else 0,
                       round(float(np.mean(self.prog)), 2) if self.prog else 0,
                       round(float(np.mean(self.hits)), 1) if self.hits else 0]
                self.w.writerow(row)
                self.f.flush()
                print("génération", row, flush=True)
                cm = np.mean(self.comps, axis=0) if self.comps else np.zeros(6)
                ts = np.mean(self.train_stats, axis=0) if self.train_stats else np.full(len(TRAIN_KEYS), np.nan)
                self.ws.writerow([self.gen, self.num_timesteps] + [round(float(x), 3) for x in cm]
                                 + [round(float(x), 5) for x in ts])
                self.fs.flush()
                self.laps, self.prog, self.hits = [], [], []
                self.comps, self.train_stats = [], []
            return time.time() - self.t0 < a.minutes * 60

    model.learn(total_timesteps=10**10, callback=Cb(), reset_num_timesteps=a.init is None)
    final = os.path.join(a.out_dir, "last")
    model.save(final)
    venv.save(final + "_vecnormalize.pkl")
    venv.close()
    print("fin :", final, flush=True)


if __name__ == "__main__":
    main()
