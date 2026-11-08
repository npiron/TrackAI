"""Affinage PPO d'un modèle imité (best/) avec perte d'imitation auxiliaire décroissante.

Usage : python scripts/ppo_finetune.py --init data/models/best/best.zip --timesteps 500000 --out data/checkpoints/ppo_ft
Sauve <out>.zip et <out>_vecnormalize.pkl (compatibles scripts/eval.py).

- lr faible, petit clip, ent_coef 0 : on évite d'oublier la politique imitée.
- Environnements en alternance piste fixe (resets pairs) / procédurale (graines >= 1000, banc 0-49 jamais vu).
- VecNormalize chargé depuis le modèle initial, statistiques GELÉES (training=False), récompense non normalisée.
- Après chaque mise à jour PPO : quelques pas de cross-entropy sur un jeu de données étiqueté par le professeur
  (collecte DAgger-like : le modèle initial conduit, l'heuristique étiquette), pondérés par un coefficient
  qui décroît linéairement de --aux-coef0 à 0.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

LOG_EVERY = 20_000
AUX_STEPS = 8          # minibatchs de cross-entropy par mise à jour PPO
AUX_BATCH = 512


def _make_env_class():
    from src.game.track import build_track
    from src.rl.wrappers import GymTimeAttack

    class MixEnv(GymTimeAttack):
        """Resets pairs : piste fixe ; impairs : procédurale de graine >= 1000."""

        def __init__(self, rank=0, seed=0, **kw):
            super().__init__(render_mode=None, procedural=True, **kw)
            self._static_track = build_track()
            self._rng = np.random.RandomState(seed * 1000 + rank)
            self._n_reset = 0

        def reset(self, seed=None, options=None):
            if self._n_reset % 2 == 0:
                self.ta.procedural = False
                self.ta.track = self._static_track
                options = None
            else:
                self.ta.procedural = True
                options = {"track_seed": 1000 + int(self._rng.randint(0, 1_000_000))}
            self._n_reset += 1
            return super().reset(seed=seed, options=options)

    return MixEnv


def _make_ppo_class():
    import torch
    from stable_baselines3 import PPO

    class AuxPPO(PPO):
        """PPO + cross-entropy sur (obs normalisées, action du professeur) à chaque mise à jour."""
        aux_obs = None
        aux_act = None
        aux_coef0 = 1.0
        aux_coef = 0.0
        aux_coef_hist = None  # coefficients appliqués à chaque mise à jour

        def train(self):
            super().train()
            self.aux_coef = self.aux_coef0 * max(0.0, self._current_progress_remaining)
            self.aux_coef_hist = (self.aux_coef_hist or []) + [self.aux_coef]
            self.logger.record("train/aux_coef", self.aux_coef)
            if self.aux_coef <= 0.0 or self.aux_obs is None:
                return
            n = len(self.aux_obs)
            tot = 0.0
            for _ in range(AUX_STEPS):
                idx = torch.randint(0, n, (min(AUX_BATCH, n),))
                dist = self.policy.get_distribution(self.aux_obs[idx])
                loss = self.aux_coef * -dist.log_prob(self.aux_act[idx]).mean()
                self.policy.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.policy.optimizer.step()
                tot += loss.item()
            self.logger.record("train/aux_loss", tot / AUX_STEPS)

    return AuxPPO


def _make_callback(max_minutes, log_every=LOG_EVERY):
    import torch
    from stable_baselines3.common.callbacks import BaseCallback

    class FinetuneCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.t0 = time.time()
            self.stopped = False
            self.next_log = log_every
            self.hits, self.laps = [], []

        def _on_step(self):
            for info, done in zip(self.locals["infos"], self.locals["dones"]):
                if done:
                    self.hits.append(info.get("wall_hits", 0))
                    if info.get("is_success") and info.get("lap_times"):
                        self.laps.append(float(np.mean(info["lap_times"])))
            if time.time() - self.t0 > max_minutes * 60:
                self.stopped = True
                return False
            return True

        def _on_rollout_end(self):
            if self.num_timesteps < self.next_log:
                return
            self.next_log += log_every
            buf = self.model.rollout_buffer
            with torch.no_grad():
                ent = float(self.model.policy.get_distribution(
                    torch.as_tensor(buf.observations.reshape(-1, buf.obs_shape[0]))).entropy().mean())
            hits = f"{np.mean(self.hits):.2f}" if self.hits else "n/a"
            lap = f"{np.mean(self.laps):.2f}s" if self.laps else "n/a"
            coef = self.model.aux_coef0 * max(0.0, self.model._current_progress_remaining)
            print(f"[{self.num_timesteps:>8} pas, {(time.time() - self.t0) / 60:5.1f} min] coef aux {coef:.3f} | "
                  f"chocs/ép {hits} | tour moyen {lap} | entropie {ent:.3f} | {len(self.hits)} ép.", flush=True)
            self.hits, self.laps = [], []

    return FinetuneCallback()


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--init", required=True, help="modèle .zip de départ (+ <nom>_vecnormalize.pkl)")
    p.add_argument("--timesteps", type=int, default=500_000)
    p.add_argument("--lr", type=float, default=3e-5)
    p.add_argument("--clip", type=float, default=0.05)
    p.add_argument("--n-envs", type=int, default=8)
    p.add_argument("--aux-coef0", type=float, default=1.0, help="coefficient initial de la perte d'imitation (→ 0 linéairement)")
    p.add_argument("--aux-episodes", type=int, default=60, help="épisodes de collecte du jeu de données professeur")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--reward-mode", default="simple", choices=("legacy", "simple"))
    p.add_argument("--wall-penalty", type=float, default=-50.0)
    p.add_argument("--out", default="data/checkpoints/ppo_ft")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-minutes", type=float, default=28.0, help="arrêt propre après N minutes (sauve l'état courant)")
    a = p.parse_args(argv)

    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize
    from scripts.eval import _load_model, detect_obs_version
    from scripts.imitate import collect, make_policy

    obs_version = detect_obs_version(_load_model(a.init)[0])
    kw = dict(laps=a.laps, obs_version=obs_version, reward_mode=a.reward_mode, wall_penalty=a.wall_penalty)
    MixEnv = _make_env_class()

    def factory(rank):
        return lambda: MixEnv(rank=rank, seed=a.seed, **kw)

    fns = [factory(i) for i in range(a.n_envs)]
    base = DummyVecEnv(fns) if a.n_envs == 1 else SubprocVecEnv(fns)
    venv = VecNormalize.load(a.init.replace(".zip", "") + "_vecnormalize.pkl", base)
    venv.training = False   # statistiques gelées (même normalisation que le banc)
    venv.norm_reward = False

    AuxPPO = _make_ppo_class()
    model = AuxPPO.load(a.init, env=venv, device="cpu", seed=a.seed, custom_objects=dict(
        learning_rate=a.lr, clip_range=a.clip, n_steps=512, batch_size=512, n_epochs=4,
        ent_coef=0.0, gamma=0.995, gae_lambda=0.95))
    model.aux_coef0 = a.aux_coef0
    model.aux_coef_hist = None  # l'historique est sauvé dans le .zip : repartir de zéro
    print(f"modèle initial chargé : {a.init} (obs v{obs_version}), {a.n_envs} env(s)", flush=True)

    # Jeu de données professeur : le modèle initial conduit (DAgger-like), l'heuristique étiquette.
    import torch
    ckw = dict(obs_version=obs_version, reward_mode=a.reward_mode, wall_penalty=a.wall_penalty)
    O, A = collect(a.aux_episodes, a.laps, True, a.seed, policy=make_policy(model, venv), env_kw=ckw,
                   hit_weight=10, mix_static=True)
    On = np.clip((O - venv.obs_rms.mean) / np.sqrt(venv.obs_rms.var + venv.epsilon), -venv.clip_obs,
                 venv.clip_obs).astype(np.float32)
    model.aux_obs, model.aux_act = torch.as_tensor(On), torch.as_tensor(A)
    print(f"{len(O)} échantillons professeur, répartition actions: {np.bincount(A, minlength=9).tolist()}", flush=True)

    cb = _make_callback(a.max_minutes)
    t0 = time.time()
    try:
        model.learn(total_timesteps=a.timesteps, callback=cb, reset_num_timesteps=True)
    finally:
        dt = max(time.time() - t0, 1e-9)
        model.save(a.out)
        venv.save(a.out + "_vecnormalize.pkl")
        venv.close()
    state = " (arrêt --max-minutes)" if cb.stopped else ""
    print(f"sauvé {a.out}.zip{state} : {model.num_timesteps} pas en {dt:.0f} s ({model.num_timesteps / dt:.0f} pas/s)")
    return model


if __name__ == "__main__":
    main()
