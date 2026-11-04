"""Robustesse : N épisodes (graines S+k), bruit d'action epsilon (action aléatoire avec proba eps).

Usage : python scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --eps 0 0.05 0.1 --out docs/ROBUST_T28.md
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

from scripts.eval import DEFAULT_METRICS, _load_model, append_metrics


def run(model_path, episodes, seed, eps, laps_n, procedural=False):
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=procedural, laps=laps_n)
    model, vn = (None, None) if model_path == "heuristic" else _load_model(model_path)
    if model_path == "heuristic":
        from scripts.heuristic_lap import heuristic_action
    succ, totals, fails = [], [], []
    for k in range(episodes):
        random.seed(seed + k)
        np.random.seed(seed + k)
        rng = np.random.RandomState(seed + k)
        obs, _ = env.reset()
        done, info, steps, nrand = False, {}, 0, 0
        while not done:
            o = obs
            if model is None:
                pass
            elif vn is not None:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -vn.clip_obs, vn.clip_obs)
            if rng.rand() < eps:
                action = int(rng.randint(env.action_space.n))
                nrand += 1
            elif model is None:
                action = heuristic_action(obs, env.ta)
            else:
                action = int(model.predict(o, deterministic=True)[0])
            obs, r, term, trunc, info = env.step(action)
            steps += 1
            done = term or trunc
        ok = bool(info.get("is_success", False))
        succ.append(ok)
        if ok:
            totals.append(info.get("total_time", 0.0))
        else:
            car = env.ta.car
            fails.append({"seed": seed + k, "cp": info.get("checkpoints_reached", 0), "laps": info.get("laps_done", 0),
                          "steps": steps, "pos": [round(float(car.pos[0])), round(float(car.pos[1]))],
                          "info": {x: info[x] for x in info if x in ("termination", "reason", "wall_stuck", "timeout")}})
    return {"finish_rate": round(float(np.mean(succ)), 4), "n_ok": int(sum(succ)), "episodes": episodes,
            "mean_total_time": round(float(np.mean(totals)), 4) if totals else None,
            "std_total_time": round(float(np.std(totals)), 4) if totals else None,
            "worst_total_time": round(float(np.max(totals)), 4) if totals else None,
            "fails": fails}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--episodes", type=int, default=100)
    p.add_argument("--seed", type=int, default=1000)
    p.add_argument("--static", action="store_true")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--eps", type=float, nargs="+", default=[0.0, 0.05])
    p.add_argument("--out")
    p.add_argument("--metrics", default=DEFAULT_METRICS)
    a = p.parse_args(argv)
    lines = [f"# Robustesse de `{a.model}` (T28)", "",
             f"Commande : `python scripts/robust_eval.py --model {a.model} {'--static ' if a.static else ''}--laps {a.laps} "
             f"--episodes {a.episodes} --seed {a.seed} --eps {' '.join(map(str, a.eps))}`", "",
             "| eps | finish | temps moyen (s) | écart-type | pire (s) |", "|---|---|---|---|---|"]
    details = []
    for e in a.eps:
        r = run(a.model, a.episodes, a.seed, e, a.laps, not a.static)
        entry = {"date": time.strftime("%Y-%m-%d %H:%M"), "model": a.model, "episodes": a.episodes, "seed": a.seed,
                 "static": a.static, "laps": a.laps, "action_noise_eps": e, **{k: v for k, v in r.items() if k != "fails"}}
        append_metrics(a.metrics, entry)
        print(json.dumps(entry, ensure_ascii=False))
        lines.append(f"| {e} | {r['n_ok']}/{r['episodes']} | {r['mean_total_time']} | {r['std_total_time']} | {r['worst_total_time']} |")
        if r["fails"]:
            details.append((e, r["fails"]))
    for e, f in details:
        lines += ["", f"## Échecs eps={e}", ""] + [f"- {json.dumps(x, ensure_ascii=False)}" for x in f[:30]]
    if a.out:
        with open(a.out, "w") as fh:
            fh.write("\n".join(lines) + "\n")
    return lines


if __name__ == "__main__":
    main()
