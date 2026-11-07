"""Behavior cloning depuis l'heuristique : collecte (obs, action) puis pré-entraîne une PPO MlpPolicy.

Usage : python scripts/imitate.py --static --laps 1 --out data/checkpoints/ppo_t24_bc [--episodes 30]
Sauve <out>.zip et <out>_vecnormalize.pkl (compatibles `rl_train_ppo.py --load` et scripts/eval.py).
Les épisodes bruités (action aléatoire avec proba eps, étiquette = action de l'heuristique) couvrent
les états hors trajectoire (type DAgger sans politique apprise).
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

EPS_LEVELS = (0.0, 0.1, 0.2, 0.3)


def collect(episodes, laps, procedural, seed=0, eps_levels=EPS_LEVELS, max_steps=3000, policy=None, env_kw=None,
            hit_weight=1, hit_window=30, mix_static=False):
    """Renvoie (obs[N,14 ou 35], actions[N]) ; l'étiquette est toujours l'action de l'heuristique.

    policy : fonction obs -> action ; si fournie, c'est elle qui conduit (DAgger), l'heuristique corrige.
    mix_static : épisodes pairs sur piste fixe, impairs sur piste procédurale (ignore `procedural`).
    hit_weight K > 1 : les `hit_window` pas précédant chaque choc mur sont présents K fois (poids K).
    """
    from src.rl.wrappers import GymTimeAttack
    from scripts.heuristic_lap import heuristic_action
    env = GymTimeAttack(render_mode=None, procedural=procedural, laps=laps, **(env_kw or {}))
    env_s = GymTimeAttack(render_mode=None, procedural=False, laps=laps, **(env_kw or {})) if mix_static else None
    env_p = env if procedural or not mix_static else GymTimeAttack(render_mode=None, procedural=True, laps=laps,
                                                                    **(env_kw or {}))
    O, A = [], []
    for k in range(episodes):
        random.seed(seed + k)
        np.random.seed(seed + k)
        rng = np.random.RandomState(seed + k)
        eps = eps_levels[k % len(eps_levels)]
        if mix_static:
            env = env_s if k % 2 == 0 else env_p
        obs, _ = env.reset()
        start, hits = len(O), []
        for _ in range(max_steps):
            a = heuristic_action(env.ta.obs_v1(), env.ta)  # le professeur voit toujours l'obs v1
            O.append(obs.copy())
            A.append(a)
            if policy is not None:
                a = int(policy(obs))
            if rng.rand() < eps:
                a = int(rng.randint(env.action_space.n))
            before = env.ta.wall_hits
            obs, _, term, trunc, _ = env.step(a)
            if env.ta.wall_hits > before:
                hits.append(len(O))
            if term or trunc:
                break
        if hit_weight > 1 and hits:
            sel = sorted({i for h in hits for i in range(max(start, h - hit_window), h)})
            for _r in range(hit_weight - 1):
                O.extend(O[i] for i in sel)
                A.extend(A[i] for i in sel)
    return np.array(O, dtype=np.float32), np.array(A, dtype=np.int64)


def behavior_clone(model, obs_n, acts, epochs, lr=1e-3, batch=256, seed=0):
    """Cross-entropy sur les logits de la politique ; renvoie (perte finale, précision)."""
    import torch
    torch.manual_seed(seed)
    pol = model.policy
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    X, Y = torch.as_tensor(obs_n), torch.as_tensor(acts)
    n = len(X)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            dist = pol.get_distribution(X[idx])
            loss = -dist.log_prob(Y[idx]).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    with torch.no_grad():
        logits = pol.get_distribution(X).distribution.logits
        acc = float((logits.argmax(1) == Y).float().mean())
    return float(loss), acc


def make_policy(model, venv):
    """Politique déterministe sur obs brute, normalisée avec les stats courantes de venv."""
    def pol(obs):
        o = np.clip((obs - venv.obs_rms.mean) / np.sqrt(venv.obs_rms.var + venv.epsilon), -10, 10)
        return model.predict(o.astype(np.float32), deterministic=True)[0]
    return pol


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=40)
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--static", action="store_true")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--dagger", type=int, default=0, help="tours de DAgger (la politique conduit)")
    p.add_argument("--dagger-episodes", type=int, default=20)
    p.add_argument("--dagger-eps", type=float, nargs="+", default=[0.0, 0.05],
                   help="niveaux de bruit d'action pendant DAgger (alternés par épisode)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--wall-fatal", action="store_true", help="un choc mur termine l'épisode (-100)")
    p.add_argument("--wall-penalty", type=float, default=0.0, help="récompense ajoutée par choc (ex. -50)")
    p.add_argument("--init", default=None, help="modèle .zip de départ (poids + <nom>_vecnormalize.pkl) ; "
                   "la 1re collecte est alors conduite par ce modèle, étiquetée par le professeur")
    p.add_argument("--lr", type=float, default=1e-3, help="taux d'apprentissage du BC")
    p.add_argument("--net-arch", type=int, nargs="+", default=[256, 256],
                   help="couches cachées du MLP (sans --init), ex. 256 256 256")
    p.add_argument("--teacher-horizon", type=int, default=None,
                   help="SAFE_HORIZON du professeur heuristique (défaut : valeur de heuristic_lap)")
    p.add_argument("--hit-weight", type=int, default=1,
                   help="DAgger : poids K des ~30 pas précédant un choc mur (échantillons dupliqués), défaut 1 = off")
    p.add_argument("--mix-static", action="store_true",
                   help="DAgger : épisodes alternant piste fixe (pairs) et procédurale (impairs)")
    p.add_argument("--obs-version", type=int, choices=(1, 2), default=1,
                   help="observation de l'env/politique (sans --init ; avec --init : déduite du modèle)")
    p.add_argument("--out", default="data/checkpoints/ppo_t24_bc")
    a = p.parse_args(argv)
    if a.teacher_horizon is not None:
        import scripts.heuristic_lap as _h
        _h.SAFE_HORIZON = a.teacher_horizon
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    from src.rl.wrappers import GymTimeAttack
    kw = dict(wall_fatal=a.wall_fatal, wall_penalty=a.wall_penalty, obs_version=a.obs_version)
    if a.init:
        from scripts.eval import _load_model, detect_obs_version
        kw["obs_version"] = detect_obs_version(_load_model(a.init)[0])
        venv = VecNormalize.load(a.init.replace(".zip", "") + "_vecnormalize.pkl",
                                 DummyVecEnv([lambda: GymTimeAttack(render_mode=None, procedural=not a.static,
                                                                    laps=a.laps, **kw)]))
        venv.training = False
        venv.norm_reward = False
        model = PPO.load(a.init, env=venv, device="cpu")
        print("modèle initial chargé :", a.init)
        O, A = collect(a.episodes, a.laps, not a.static, a.seed, eps_levels=tuple(a.dagger_eps),
                       policy=make_policy(model, venv), env_kw=kw,
                       hit_weight=a.hit_weight, mix_static=a.mix_static)
        print(f"{len(O)} échantillons (états visités par le modèle initial), "
              f"répartition actions: {np.bincount(A, minlength=9).tolist()}")
        On = np.clip((O - venv.obs_rms.mean) / np.sqrt(venv.obs_rms.var + venv.epsilon), -10, 10).astype(np.float32)
        import torch
        with torch.no_grad():
            lg = model.policy.get_distribution(torch.as_tensor(On)).distribution.logits
        print(f"précision initiale sur les données du professeur : {float((lg.argmax(1).numpy() == A).mean()):.3f}")
        if a.epochs > 0:
            loss, acc = behavior_clone(model, On, A, a.epochs, lr=a.lr, seed=a.seed)
            print(f"BC: perte {loss:.4f}, précision {acc:.3f}")
    else:
        O, A = collect(a.episodes, a.laps, not a.static, a.seed, env_kw=kw)
        print(f"{len(O)} échantillons, répartition actions: {np.bincount(A, minlength=9).tolist()}")
        venv = VecNormalize(DummyVecEnv([lambda: GymTimeAttack(render_mode=None, procedural=not a.static,
                                                               laps=a.laps, **kw)]),
                            norm_obs=True, norm_reward=True, clip_obs=10.0)
        venv.obs_rms.mean, venv.obs_rms.var, venv.obs_rms.count = O.mean(0).astype(np.float64), O.var(0).astype(np.float64) + 1e-8, len(O)
        On = np.clip((O - venv.obs_rms.mean) / np.sqrt(venv.obs_rms.var + venv.epsilon), -10, 10).astype(np.float32)
        model = PPO("MlpPolicy", venv, device="cpu", seed=a.seed,
                    policy_kwargs=dict(net_arch=[dict(pi=list(a.net_arch), vf=list(a.net_arch))]))
        loss, acc = behavior_clone(model, On, A, a.epochs, lr=a.lr, seed=a.seed)
        print(f"BC: perte {loss:.4f}, précision {acc:.3f}")
    for r in range(a.dagger):
        pol = make_policy(model, venv)
        # niveaux --dagger-eps en alternance (défaut 0 et 0.05) : la politique apprise explore ses propres erreurs
        O2, A2 = collect(a.dagger_episodes, a.laps, not a.static, a.seed + 1000 * (r + 1),
                         eps_levels=tuple(a.dagger_eps), policy=pol, env_kw=kw,
                         hit_weight=a.hit_weight, mix_static=a.mix_static)
        O, A = np.concatenate([O, O2]), np.concatenate([A, A2])
        On = np.clip((O - venv.obs_rms.mean) / np.sqrt(venv.obs_rms.var + venv.epsilon), -10, 10).astype(np.float32)
        loss, acc = behavior_clone(model, On, A, a.epochs, lr=a.lr, seed=a.seed + r + 1)
        print(f"DAgger {r + 1}: +{len(O2)} échantillons (total {len(O)}), perte {loss:.4f}, précision {acc:.3f}")
    model.save(a.out)
    venv.save(a.out + "_vecnormalize.pkl")
    print("sauvé", a.out + ".zip")


if __name__ == "__main__":
    main()
