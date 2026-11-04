"""T64 : rejoue un agent (piste statique) et décrit chaque choc mur : pas, tour, indice de spline,
vitesse, action de l'agent vs action du professeur (heuristic, SAFE_HORIZON courant) au même état.

Usage : python scripts/diagnose_hits.py --model data/checkpoints/ppo_t60.zip --laps 3 [--lookback 30]
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


def diagnose(model_path, laps_n, lookback, seed=0):
    from scripts import eval as ev
    from scripts.heuristic_lap import heuristic_action
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=False, laps=laps_n)
    model, vn = ev._load_model(model_path)
    random.seed(seed)
    np.random.seed(seed)
    obs, _ = env.reset()
    n = len(env.ta.track.spline_points)
    done, step, prev = False, 0, 0
    hist, events = [], []
    while not done:
        o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                    -vn.clip_obs, vn.clip_obs) if vn is not None else obs
        a = int(model.predict(o, deterministic=True)[0])
        t = int(heuristic_action(obs, env.ta))
        from scripts.heuristic_lap import closest_index
        hist.append((step, a, t, closest_index(env.ta), float(env.ta.car.speed)))
        obs, _, term, trunc, info = env.step(a)
        done = term or trunc
        step += 1
        if env.ta.wall_hits > prev:
            prev = env.ta.wall_hits
            h = hist[-lookback:]
            diff = [x for x in h if x[1] != x[2]]
            events.append({
                "step": step, "lap": int(info.get("laps_done", 0)) + 1,
                "spline_idx": closest_index(env.ta), "spline_pct": round(100 * closest_index(env.ta) / n, 1),
                "pos": [round(float(env.ta.car.pos[0]), 1), round(float(env.ta.car.pos[1]), 1)],
                "speed_before": round(hist[-1][4], 2), "agent_act": hist[-1][1], "teacher_act": hist[-1][2],
                "diff_in_last_%d" % lookback: len(diff),
                "first_diff": None if not diff else {"step": diff[0][0], "agent": diff[0][1], "teacher": diff[0][2],
                                                      "spline_idx": diff[0][3]},
                "agent_last": [x[1] for x in h[-8:]], "teacher_last": [x[2] for x in h[-8:]],
            })
    return {"model": model_path, "steps": step, "success": bool(info.get("is_success", False)),
            "total_time": info.get("total_time"), "spline_n": n, "hits": events,
            "action_diff_total": sum(1 for x in hist if x[1] != x[2]), "n_actions": len(hist)}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--lookback", type=int, default=30)
    a = p.parse_args(argv)
    print(json.dumps(diagnose(a.model, a.laps, a.lookback)))


if __name__ == "__main__":
    main()
