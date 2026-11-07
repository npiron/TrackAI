"""Banc d'évaluation reproductible.

Usage : python scripts/eval.py --model <chemin.zip|random> --episodes N --seed S [--static|--no-static|--bench] [--metrics chemin.json]
Chaque épisode k utilise la graine S+k (piste + politique aléatoire) : deux lancements
identiques donnent le même résultat. Ajoute une entrée dans .goal/metrics.json (.team/ si .goal/ n'existe pas).
Sans flag : pistes procédurales (= --no-static).
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_METRICS = os.path.join(_ROOT, ".goal" if os.path.isdir(os.path.join(_ROOT, ".goal")) else ".team", "metrics.json")


BENCH_EPISODES = 50


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
    cand = (path[:-4] if path.endswith(".zip") else path) + "_vecnormalize.pkl"
    if os.path.exists(cand):
        import pickle
        with open(cand, "rb") as f:
            stats = pickle.load(f)
    elif isinstance(model, PPO):
        raise FileNotFoundError(f"VecNormalize introuvable pour le modèle PPO {path} (attendu : {cand})")
    return model, stats


def detect_obs_version(model, forced=None):
    """obs_version d'après la forme d'observation du modèle (14 -> 1, taille v2 -> 2) ; `forced` prioritaire.
    Sans modèle (random/heuristic) : `forced` ou 1."""
    if forced is not None:
        return int(forced)
    if model is None:
        return 1
    from src.game.env import TimeAttackEnv
    n = model.observation_space.shape[0]
    if n == 14:
        return 1
    if n == TimeAttackEnv.OBS_V2_SIZE:
        return 2
    raise ValueError(f"taille d'observation inconnue : {n}")


def multi_lap_stats(succ, laps_done, totals):
    """Métriques multi-tours à partir des résultats par épisode (totals = temps totaux des épisodes réussis)."""
    return {
        "finish_rate": round(float(np.mean(succ)), 4),
        "mean_total_time": round(float(np.mean(totals)), 4) if totals else None,
        "best_total_time": round(float(np.min(totals)), 4) if totals else None,
        "mean_laps_done": round(float(np.mean(laps_done)), 4),
    }


def wall_stats(hits, succ):
    """Chocs par épisode ; clean_rate = part des épisodes finis avec 0 choc."""
    return {
        "mean_wall_hits": round(float(np.mean(hits)), 4),
        "max_wall_hits": int(np.max(hits)),
        "clean_rate": round(float(np.mean([s and h == 0 for s, h in zip(succ, hits)])), 4),
    }


def run_eval(model_path, episodes, seed, procedural=True, laps_n=1, bench=False, obs_version=None):
    """bench : l'épisode k utilise la piste de graine k (pistes fixes, seed ignoré).
    obs_version : None = déduite du modèle (1 pour random/heuristic)."""
    from src.rl.wrappers import GymTimeAttack
    shield = model_path.startswith("shield:")  # T55 : politique + garde-fou (NON conforme « agent seul »)
    real_path = model_path[len("shield:"):] if shield else model_path
    model, vn = (None, None) if model_path in ("random", "heuristic") else _load_model(real_path)
    env = GymTimeAttack(render_mode=None, procedural=procedural, laps=laps_n,
                        obs_version=detect_obs_version(model, obs_version))
    if shield:
        from scripts.heuristic_lap import _safe_action
    if model_path == "heuristic":
        from scripts.heuristic_lap import heuristic_action
    rng = np.random.RandomState(0 if bench else seed)
    rets, cps, succ, laps, lens = [], [], [], [], []
    laps_done, totals, hits = [], [], []
    for k in range(episodes):
        eseed = k if bench else seed + k
        random.seed(eseed)
        np.random.seed(eseed)
        obs, _ = env.reset(options={"track_seed": k} if bench else None)
        ret, steps, done, info = 0.0, 0, False, {}
        while not done:
            if model_path == "heuristic":
                action = heuristic_action(env.ta.obs_v1(), env.ta)
            elif model is None:
                action = int(rng.randint(env.action_space.n))
            else:
                o = obs
                if vn is not None:
                    o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                                -vn.clip_obs, vn.clip_obs)
                action = int(model.predict(o, deterministic=True)[0])
                if shield:
                    action = _safe_action(env.ta, action)
            obs, r, term, trunc, info = env.step(action)
            ret += r
            steps += 1
            done = term or trunc
        rets.append(ret)
        cps.append(info.get("checkpoints_reached", 0))
        succ.append(bool(info.get("is_success", False)))
        laps_done.append(info.get("laps_done", 0))
        hits.append(int(info.get("wall_hits", 0)))
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
        **wall_stats(hits, succ),
        **({"wall_hits_by_seed": hits} if bench else {}),
    }


def _human_best():
    from scripts.human_lap import load_best
    return load_best()


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
    p.add_argument("--bench", action="store_true", help="banc fixe : 50 pistes de graines 0 à 49")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--static", action="store_true", help="piste fixe")
    g.add_argument("--no-static", action="store_true", help="pistes aléatoires procédurales (défaut)")
    p.add_argument("--laps", type=int, default=1, help="nombre de tours")
    p.add_argument("--obs-version", type=int, choices=(1, 2), default=None,
                   help="force la version d'observation (défaut : déduite du modèle, 1 pour random/heuristic)")
    p.add_argument("--metrics", default=DEFAULT_METRICS)
    a = p.parse_args(argv)
    if a.bench and (a.static or a.no_static):
        p.error("--bench est incompatible avec --static/--no-static")
    if a.bench:
        a.episodes = BENCH_EPISODES
    res = run_eval(a.model, a.episodes, a.seed, procedural=not a.static, laps_n=a.laps, bench=a.bench,
                   obs_version=a.obs_version)
    entry = {"date": time.strftime("%Y-%m-%d %H:%M"), "model": a.model, "episodes": a.episodes,
             "seed": a.seed, "static": a.static, "laps": a.laps,
             **({"bench": True} if a.bench else {}),
             "human_best_total": _human_best(), **res}
    append_metrics(a.metrics, entry)
    print(json.dumps(entry, ensure_ascii=False))
    return entry


if __name__ == "__main__":
    main()
