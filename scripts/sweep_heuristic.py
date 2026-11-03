"""Balayage des constantes de scripts/heuristic_lap.py (piste fixe, déterministe : 1 épisode suffit).

Usage : python scripts/sweep_heuristic.py [--episodes 1] [--out docs/SPEED_T25.md]
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None):
    import argparse
    from scripts import eval as ev
    from scripts import heuristic_lap as h
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=1)
    p.add_argument("--out", default="docs/SPEED_T25.md")
    p.add_argument("--spr", type=float, nargs="+", default=[0.06, 0.07, 0.08, 0.09, 0.10, 0.12])
    p.add_argument("--pred", type=int, nargs="+", default=[12, 18, 24])
    p.add_argument("--look", type=int, nargs="+", default=[15, 25, 35])
    p.add_argument("--gain", type=int, nargs="+", default=[20, 40])
    a = p.parse_args(argv)
    rows = []
    for spr, pred, look, gain in itertools.product(a.spr, a.pred, a.look, a.gain):
        h.SPEED_PER_RADIUS, h.PREDICT_FRAMES, h.LOOK_MIN, h.LOOK_GAIN = spr, pred, look, gain
        r = ev.run_eval("heuristic", a.episodes, 0, procedural=False, laps_n=3)
        rows.append((spr, pred, look, gain, r["finish_rate"], r["mean_total_time"], r["mean_checkpoints"]))
        print(rows[-1], flush=True)
    rows.sort(key=lambda x: (-x[4], x[5] if x[5] is not None else 1e9))
    with open(a.out, "w") as f:
        f.write("# Balayage heuristique (T25)\n\n3 tours, piste fixe, seed 0, %d épisode(s) par combinaison.\n\n" % a.episodes)
        f.write("| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    return rows


if __name__ == "__main__":
    main()
