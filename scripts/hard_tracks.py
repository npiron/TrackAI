"""Repère les circuits longs où le bot se plante le plus.

Usage : python3 manage.py hard-tracks --model data/checkpoints/f1_5t/last.zip [--seeds 500] [--laps 3]
        (ou .venv/bin/python scripts/hard_tracks.py ...)

Fait rouler le modèle (déterministe) sur les circuits longs de graines start .. start+seeds-1 et note pour chacun :
chocs, chocs par tour, vitesse moyenne des tours, parcours fini ou non, et à quel checkpoint chaque choc arrive.
Écrit dans --out-dir :
- tracks.csv : un circuit par ligne, du plus dur au plus facile ;
- hard_tracks.json : les --top circuits les plus durs, coupés en {"train": [...], "val": [...]} (un sur deux),
  pour s'entraîner sur train (train_long.py --track-seeds-file) et vérifier sur val qu'on progresse sans les avoir vus.
"""
import argparse
import csv
import json
import os
import sys
import time
from multiprocessing import Pool

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np

_W = {}


def _init(model_path):
    import torch
    torch.set_num_threads(1)
    from scripts.eval import _load_model, detect_action_set, detect_obs_version
    model, vn = _load_model(model_path)
    _W.update(model=model, vn=vn, obs_version=detect_obs_version(model), action_set=detect_action_set(model))


def run_track(args):
    """Un circuit, un épisode déterministe. Renvoie les mesures du circuit."""
    seed, laps = args
    from src.rl.wrappers import GymTimeAttack
    model, vn = _W["model"], _W["vn"]
    env = GymTimeAttack(render_mode=None, procedural=True, laps=laps, obs_version=_W["obs_version"],
                        track_variant=2, action_set=_W["action_set"])
    obs, _ = env.reset(options={"track_seed": seed})
    n_cp = len(env.ta.track.checkpoints)
    done, info, hits_prev, hit_cps = False, {}, 0, []
    while not done:
        o = obs
        if vn is not None:
            o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -vn.clip_obs, vn.clip_obs)
        obs, _, term, trunc, info = env.step(int(model.predict(o, deterministic=True)[0]))
        done = term or trunc
        h = int(info.get("wall_hits", 0))
        if h > hits_prev:   # choc : on note le checkpoint visé (index dans le tour)
            hit_cps += [int(sum(env.ta.cp_visited)) % n_cp] * (h - hits_prev)
            hits_prev = h
    laps_done = int(info.get("laps_done", 0))
    speeds = info.get("lap_speeds", [])
    env.close()
    return {
        "seed": seed,
        "finished": bool(info.get("is_success", False)),
        "laps_done": laps_done,
        "hits": hits_prev,
        "hits_per_lap": round(hits_prev / max(1, laps_done), 3),
        "speed": round(float(np.mean(speeds)), 4) if speeds else 0.0,
        "total_time": round(float(info.get("total_time", 0.0)), 2),
        "checkpoints": n_cp,
        "hit_checkpoints": " ".join(map(str, hit_cps)),
    }


def difficulty_key(r):
    """Du plus dur au plus facile : pas fini, puis chocs par tour, puis lenteur."""
    return (r["finished"], -r["hits_per_lap"], r["speed"])


def split_hard(rows, top):
    """Les `top` premiers circuits ayant au moins un choc (ou pas finis), un sur deux en train / val."""
    hard = [r["seed"] for r in rows if r["hits"] > 0 or not r["finished"]][:top]
    return {"train": hard[0::2], "val": hard[1::2]}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--seeds", type=int, default=500, help="nombre de circuits testés")
    p.add_argument("--start", type=int, default=0, help="première graine")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--top", type=int, default=100, help="circuits durs gardés (coupés en train / val)")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--out-dir", default=os.path.join(_ROOT, "data", "hard_tracks"))
    a = p.parse_args(argv)

    os.makedirs(a.out_dir, exist_ok=True)
    jobs = [(s, a.laps) for s in range(a.start, a.start + a.seeds)]
    t0, rows = time.time(), []
    with Pool(a.workers, initializer=_init, initargs=(a.model,)) as pool:
        for i, r in enumerate(pool.imap_unordered(run_track, jobs), 1):
            rows.append(r)
            if i % 25 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} circuits ({time.time() - t0:.0f} s)", flush=True)
    rows.sort(key=difficulty_key)

    with open(os.path.join(a.out_dir, "tracks.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    split = split_hard(rows, a.top)
    with open(os.path.join(a.out_dir, "hard_tracks.json"), "w") as f:
        json.dump({"model": a.model, "laps": a.laps, "seeds": [a.start, a.start + a.seeds], **split}, f, indent=1)

    hits = np.array([r["hits"] for r in rows])
    print(f"\n{len(rows)} circuits, {a.laps} tours : fini {np.mean([r['finished'] for r in rows]):.0%}, "
          f"chocs moy {hits.mean():.2f}, sans choc {np.mean(hits == 0):.0%}")
    print(f"{len(split['train'])} circuits durs en train, {len(split['val'])} en val -> {a.out_dir}")
    print("\nLes 10 plus durs :")
    for r in rows[:10]:
        print(f"  graine {r['seed']:>5}  fini={'oui' if r['finished'] else 'non'}  chocs={r['hits']:>2}  "
              f"vitesse={r['speed']:.3f}  checkpoints des chocs : {r['hit_checkpoints'] or '-'}")


if __name__ == "__main__":
    main()
