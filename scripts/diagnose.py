"""Diagnostic d'une politique : rejoue en déterministe et résume pourquoi/où elle s'arrête.

Usage : python scripts/diagnose.py --model <zip> --static --laps N --episodes 5 --seed 0
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

COMPONENTS = ["progress", "alignment", "checkpoint", "speed", "urgency", "track", "wall",
              "ghost", "time_bonus", "env"]


def add_components(acc, comps):
    """Cumule un dict de composantes dans acc (modifié en place)."""
    for k in COMPONENTS:
        acc[k] = acc.get(k, 0.0) + float(comps.get(k, 0.0))
    return acc


def summarize_episode(speeds, positions, cp_idx, acc, info, stop_thr=1.0):
    """Résumé d'un épisode à partir des séries (vitesse brute par frame, positions)."""
    speeds = np.asarray(speeds, dtype=float)
    if info.get("is_success"):
        cause = "success"
    else:
        cause = info.get("end_cause", "other")
    return {
        "last_checkpoint": int(cp_idx),
        "final_pos": [round(float(positions[-1][0]), 1), round(float(positions[-1][1]), 1)],
        "mean_speed": round(float(speeds.mean()), 3) if len(speeds) else 0.0,
        "stopped_frames": int((speeds < stop_thr).sum()),
        "steps": int(len(speeds)),
        "end_cause": cause,
        "laps_done": int(info.get("laps_done", 0)),
        "reward_total": round(float(sum(acc.values())), 3),
        "components": {k: round(v, 3) for k, v in acc.items()},
    }


def run(model_path, episodes, seed, procedural, laps):
    from scripts.eval import _load_model
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=procedural, laps=laps)
    model, vn = _load_model(model_path)
    out = []
    for k in range(episodes):
        random.seed(seed + k)
        np.random.seed(seed + k)
        obs, _ = env.reset()
        done, info, acc, speeds, pos = False, {}, {}, [], []
        while not done:
            o = obs
            if vn is not None:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon),
                            -vn.clip_obs, vn.clip_obs)
            action = int(model.predict(o, deterministic=True)[0])
            obs, r, term, trunc, info = env.step(action)
            if "reward_components" in info:
                add_components(acc, info["reward_components"])
            else:  # fin forcée (timeout / wall_stuck) : seule la pénalité brute
                acc["env"] = acc.get("env", 0.0) + float(r)
            speeds.append(float(env.ta.car.speed))
            pos.append((env.ta.car.pos[0], env.ta.car.pos[1]))
            done = term or trunc
        cp_idx = info.get("checkpoints_reached", 0)
        out.append(summarize_episode(speeds, pos, cp_idx, acc, info))
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--static", action="store_true")
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--episodes", type=int, default=5)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    res = run(a.model, a.episodes, a.seed, not a.static, a.laps)
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
