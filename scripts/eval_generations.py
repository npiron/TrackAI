"""Mesure chaque génération de data/checkpoints/long en conduite déterministe sur N circuits longs
(variante 2, graines 0..N-1, 1 tour). Incrémental : seules les nouvelles générations sont mesurées.

Sorties (dans --dir) : eval_gen.csv (une ligne par génération) et eval_tracks.csv (génération x circuit).
Usage : .venv/bin/python scripts/eval_generations.py [--tracks 20]
"""
import argparse
import csv
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np


def run_gen(path, n_tracks):
    from scripts.eval import _load_model, detect_action_set, detect_obs_version
    from src.rl.wrappers import GymTimeAttack
    import contextlib
    import io
    m, vn = _load_model(path)
    env = GymTimeAttack(render_mode=None, procedural=True, laps=1, obs_version=detect_obs_version(m),
                        action_set=detect_action_set(m), track_variant=2)
    rows = []
    for seed in range(n_tracks):
        obs, _ = env.reset(options={"track_seed": seed})
        done = False
        with contextlib.redirect_stdout(io.StringIO()):
            while not done:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -10, 10)
                obs, _, t, tr, info = env.step(int(m.predict(o, deterministic=True)[0]))
                done = t or tr
        ok = info.get("laps_done", 0) >= 1
        rows.append(dict(circuit=seed, fini=int(ok), temps=round(env.ta.t, 2) if ok else "",
                         chocs=int(env.ta.wall_hits), checkpoints=int(info.get("checkpoints_reached", 0))))
    return rows


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="data/checkpoints/long")
    p.add_argument("--tracks", type=int, default=20)
    a = p.parse_args(argv)
    steps = {}
    prog = os.path.join(a.dir, "progress.csv")
    if os.path.exists(prog):
        with open(prog) as f:
            steps = {int(r["gen"]): int(r["timesteps"]) for r in csv.DictReader(f)}
    gpath, tpath = os.path.join(a.dir, "eval_gen.csv"), os.path.join(a.dir, "eval_tracks.csv")
    done = set()
    if os.path.exists(gpath):
        with open(gpath) as f:
            done = {int(r["gen"]) for r in csv.DictReader(f)}
    gens = sorted(int(os.path.basename(z)[4:7]) for z in glob.glob(os.path.join(a.dir, "gen_*.zip")))
    for g in gens:
        if g in done:
            continue
        rows = run_gen(os.path.join(a.dir, f"gen_{g:03d}.zip"), a.tracks)
        fin = [r for r in rows if r["fini"]]
        summary = dict(gen=g, pas=steps.get(g, ""), circuits=len(rows),
                       finis=round(len(fin) / len(rows), 3),
                       temps_moy=round(float(np.mean([r["temps"] for r in fin])), 2) if fin else "",
                       chocs_moy=round(float(np.mean([r["chocs"] for r in rows])), 2),
                       propres=round(sum(1 for r in fin if r["chocs"] == 0) / len(rows), 3))
        for path, recs in ((gpath, [summary]), (tpath, [dict(gen=g, **r) for r in rows])):
            new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(recs[0]))
                if new:
                    w.writeheader()
                w.writerows(recs)
        print("génération", summary, flush=True)


if __name__ == "__main__":
    main()
