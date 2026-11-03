"""Banc d'évaluation reproductible.

Usage : python scripts/eval.py --model <chemin.zip|random> --episodes N --seed S [--metrics chemin.json]
Chaque épisode k utilise la graine S+k (piste + politique aléatoire) : deux lancements
identiques donnent le même résultat. Ajoute une entrée dans .team/metrics.json.
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

DEFAULT_METRICS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".team", "metrics.json")


def _load_model(path):
    """Charge un modèle PPO ou DQN (+ VecNormalize frère s'il existe)."""
    from stable_baselines3 import DQN, PPO
    last = None
    for cls in (PPO, DQN):
        try:
            model = cls.load(path, device="cpu")
            break
        except Exception as e:  # mauvais algo
            last = e
    else:
        raise RuntimeError(f"Impossible de charger {path}: {last}")
    stats = None
    cand = path.replace(".zip", "_vecnormalize.pkl")
    if os.path.exists(cand):
        import pickle
        with open(cand, "rb") as f:
            stats = pickle.load(f)
    return model, stats


def multi_lap_stats(succ, laps_done, totals):
    """Métriques multi-tours à partir des résultats par épisode (totals = temps totaux des épisodes réussis)."""
    return {
        "finish_rate": round(float(np.mean(succ)), 4),
        "mean_total_time": round(float(np.mean(totals)), 4) if totals else None,
        "best_total_time": round(float(np.min(totals)), 4) if totals else None,
        "mean_laps_done": round(float(np.mean(laps_done)), 4),
    }


def run_eval(model_path, episodes, seed, procedural=True, laps_n=1):
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=procedural, laps=laps_n)
    model, vn = (None, None) if model_path == "random" else _load_model(model_path)
    rng = np.random.RandomState(seed)
    rets, cps, succ, laps, lens = [], [], [], [], []
    laps_done, totals = [], []
    for k in range(episodes):
        random.seed(seed + k)
        np.random.seed(seed + k)
        obs, _ = env.reset()
        ret, steps, done, info = 0.0, 0, False, {}
        while not done:
            if model is None:
                action = int(rng.randint(env.action_space.n))
            else:
                o = obs
                if vn is not None:
                    o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                                -vn.clip_obs, vn.clip_obs)
                action = int(model.predict(o, deterministic=True)[0])
            obs, r, term, trunc, info = env.step(action)
            ret += r
            steps += 1
            done = term or trunc
        rets.append(ret)
        cps.append(info.get("checkpoints_reached", 0))
        succ.append(bool(info.get("is_success", False)))
        laps_done.append(info.get("laps_done", 0))
        if succ[-1]:
            totals.append(info.get("total_time", 0.0))
            laps.append(info["lap_time"])
        lens.append(steps)
    return {
        "mean_return": round(float(np.mean(rets)), 4),
        "mean_checkpoints": round(float(np.mean(cps)), 4),
        "success_rate": round(float(np.mean(succ)), 4),
        "mean_lap_time": round(float(np.mean(laps)), 4) if laps else None,
        "mean_episode_steps": round(float(np.mean(lens)), 4),
        **multi_lap_stats(succ, laps_done, totals),
    }


def append_metrics(path, entry):
    data = []
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="chemin .zip ou 'random'")
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--static", action="store_true", help="piste fixe")
    p.add_argument("--laps", type=int, default=1, help="nombre de tours")
    p.add_argument("--metrics", default=DEFAULT_METRICS)
    a = p.parse_args(argv)
    res = run_eval(a.model, a.episodes, a.seed, procedural=not a.static, laps_n=a.laps)
    entry = {"date": time.strftime("%Y-%m-%d %H:%M"), "model": a.model, "episodes": a.episodes,
             "seed": a.seed, "static": a.static, "laps": a.laps, **res}
    append_metrics(a.metrics, entry)
    print(json.dumps(entry, ensure_ascii=False))
    return entry


if __name__ == "__main__":
    main()
