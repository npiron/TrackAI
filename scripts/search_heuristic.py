"""Hill-climbing sur les constantes de scripts/heuristic_lap.py (piste fixe, 3 tours, déterministe).

Usage : python scripts/search_heuristic.py [--budget 500] [--seed 0] [--out docs/SEARCH_T30.md]
Perturbe aléatoirement un ou deux paramètres ; accepte si le tour est fini et plus court.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# nom: (min, max, pas gaussien relatif/absolu, entier?)
SPACE = {
    "SPEED_PER_RADIUS": (0.1, 0.5, 0.03, False),
    "PREDICT_FRAMES": (0, 25, 2, True),
    "LOOK_MIN": (50, 400, 25, True),
    "LOOK_GAIN": (0, 400, 30, True),
    "STEER_DEADZONE": (0.0, 0.15, 0.015, False),
}


def evaluate(h, ev, params):
    for k, v in params.items():
        setattr(h, k, v)
    r = ev.run_eval("heuristic", 1, 0, procedural=False, laps_n=3)
    ok = r["finish_rate"] == 1.0
    return ok, (r["mean_total_time"] if ok else None)


def main(argv=None):
    import argparse
    import random
    from scripts import eval as ev
    from scripts import heuristic_lap as h
    p = argparse.ArgumentParser()
    p.add_argument("--budget", type=int, default=500)
    p.add_argument("--max-seconds", type=float, default=540)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="docs/SEARCH_T30.md")
    a = p.parse_args(argv)
    rng = random.Random(a.seed)
    best = {k: getattr(h, k) for k in SPACE}
    ok, bt = evaluate(h, ev, best)
    assert ok
    log = [(0, dict(best), bt, "départ")]
    t0 = time.time()
    n = 0
    while n < a.budget and time.time() - t0 < a.max_seconds:
        n += 1
        cand = dict(best)
        for k in rng.sample(list(SPACE), rng.choice([1, 2])):
            lo, hi, s, isint = SPACE[k]
            v = min(hi, max(lo, cand[k] + rng.gauss(0, s)))
            cand[k] = int(round(v)) if isint else round(v, 4)
        if cand == best:
            continue
        ok, t = evaluate(h, ev, cand)
        if ok and t < bt - 1e-9:
            best, bt = cand, t
            log.append((n, dict(best), bt, "amélioré"))
            print(n, bt, best, flush=True)
    with open(a.out, "w") as f:
        f.write("# Recherche heuristique (T30)\n\nHill-climbing, 3 tours, piste fixe, seed 0, %d essais, graine %d.\n\n" % (n, a.seed))
        f.write("| essai | temps (s) | paramètres |\n|---|---|---|\n")
        for i, par, t, _ in log:
            f.write("| %d | %s | %s |\n" % (i, t, par))
    print("meilleur", bt, best)
    return best, bt


if __name__ == "__main__":
    main()
