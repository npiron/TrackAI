"""Localise les chocs murs : histogramme par secteur de spline (et tour).

Usage : python scripts/wall_locate.py --model <zip|heuristic> --static --laps 3 --episodes 20 --seed 0 [--sectors 12]
Un choc = pas où env.wall_hits augmente ; position = indice de spline le plus proche de la voiture.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


def locate(model_path, episodes, seed, laps_n, sectors):
    from scripts import eval as ev
    from scripts.heuristic_lap import closest_index, heuristic_action
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=False, laps=laps_n)
    model, vn = (None, None) if model_path == "heuristic" else ev._load_model(model_path)
    hist = np.zeros(sectors, int)
    per_ep = []
    for k in range(episodes):
        random.seed(seed + k)
        np.random.seed(seed + k)
        obs, _ = env.reset()
        done, prev = False, 0
        while not done:
            if model is None:
                a = heuristic_action(obs, env.ta)
            else:
                o = obs
                if vn is not None:
                    o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                                -vn.clip_obs, vn.clip_obs)
                a = int(model.predict(o, deterministic=True)[0])
            obs, _, term, trunc, info = env.step(a)
            done = term or trunc
            if env.ta.wall_hits > prev:
                n = len(env.ta.track.spline_points)
                hist[closest_index(env.ta) * sectors // n] += env.ta.wall_hits - prev
                prev = env.ta.wall_hits
        per_ep.append(int(env.ta.wall_hits))
    return hist.tolist(), per_ep


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--sectors", type=int, default=12)
    p.add_argument("--static", action="store_true")
    a = p.parse_args(argv)
    hist, per_ep = locate(a.model, a.episodes, a.seed, a.laps, a.sectors)
    print(json.dumps({"model": a.model, "sectors": a.sectors, "hits_per_sector": hist, "per_episode": per_ep}))


if __name__ == "__main__":
    main()
