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
        setattr(h, k, list(v) if k == "SECTOR_MULT" else v)
    r = ev.run_eval("heuristic", 1, 0, procedural=False, laps_n=3)
    ok = r["finish_rate"] == 1.0
    return ok, (r["mean_total_time"] if ok else None)


def climb(h, ev, rng, start, budget, max_seconds, sectors):
    """Hill-climbing (paramètres globaux + multiplicateurs de secteurs). Renvoie (best, temps, nb essais, journal)."""
    best = {k: (list(v) if isinstance(v, list) else v) for k, v in start.items()}
    ok, bt = evaluate(h, ev, best)
    if not ok:
        return best, None, 0, []
    log = [(0, bt)]
    t0, n = time.time(), 0
    keys = list(SPACE) + (["SECTOR_MULT"] if sectors else [])
    while n < budget and time.time() - t0 < max_seconds:
        n += 1
        cand = {k: (list(v) if isinstance(v, list) else v) for k, v in best.items()}
        for k in rng.sample(keys, rng.choice([1, 2])):
            if k == "SECTOR_MULT":
                j = rng.randrange(sectors)
                cand[k][j] = round(min(2.0, max(0.5, cand[k][j] + rng.gauss(0, 0.08))), 4)
            else:
                lo, hi, s, isint = SPACE[k]
                v = min(hi, max(lo, cand[k] + rng.gauss(0, s)))
                cand[k] = int(round(v)) if isint else round(v, 4)
        if cand == best:
            continue
        ok, t = evaluate(h, ev, cand)
        if ok and t < bt - 1e-9:
            best, bt = cand, t
            log.append((n, bt))
    return best, bt, n, log


def multi(a, h, ev, random):
    start = {k: getattr(h, k) for k in SPACE}
    if a.sectors:
        start["SECTOR_MULT"] = [1.0] * a.sectors
    per = a.max_seconds / a.restarts
    rows, overall = [], (None, 1e9)
    for i in range(a.restarts):
        rng = random.Random(a.seed + i)
        st = {k: (list(v) if isinstance(v, list) else v) for k, v in start.items()}
        if i > 0:  # départ perturbé
            for k in SPACE:
                lo, hi, s, isint = SPACE[k]
                v = min(hi, max(lo, st[k] + rng.gauss(0, s)))
                st[k] = int(round(v)) if isint else round(v, 4)
            if a.sectors:
                st["SECTOR_MULT"] = [round(min(1.5, max(0.7, 1 + rng.gauss(0, 0.1))), 4) for _ in range(a.sectors)]
            ok, _ = evaluate(h, ev, st)
            if not ok:
                st = {k: (list(v) if isinstance(v, list) else v) for k, v in start.items()}
        best, bt, n, log = climb(h, ev, rng, st, a.budget, per, a.sectors)
        rows.append((i, a.seed + i, n, bt, best))
        print("restart", i, "essais", n, "temps", bt, best, flush=True)
        if bt is not None and bt < overall[1]:
            overall = (best, bt)
    with open(a.out, "w") as f:
        f.write("# Recherche heuristique élargie (T33)\n\nHill-climbing, 3 tours, piste fixe, seed 0, %d secteurs de spline, %d redémarrages (graine %d+i), %.0f s chacun.\n\n" % (a.sectors, a.restarts, a.seed, per))
        f.write("| restart | graine | essais | temps (s) | paramètres |\n|---|---|---|---|---|\n")
        for i, sd, n, t, b in rows:
            f.write("| %d | %d | %d | %s | %s |\n" % (i, sd, n, t, b))
        f.write("\nMeilleur : %s s — `%s`\n" % (overall[1], overall[0]))
    print("meilleur", overall[1], overall[0])
    return overall


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
    p.add_argument("--sectors", type=int, default=0, help="nb de secteurs de spline (multiplicateurs de vitesse), 0 = off")
    p.add_argument("--restarts", type=int, default=1, help="redémarrages (graine seed+i, départ perturbé si i>0)")
    a = p.parse_args(argv)
    if a.restarts > 1 or a.sectors:
        return multi(a, h, ev, random)
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
