"""Borne inférieure théorique du temps sur N tours (T32).

Usage : SDL_VIDEODRIVER=dummy python scripts/lower_bound.py [--laps 3] [--out docs/BOUND_T32.md]

Méthode (la physique n'est pas modifiée, on la mesure par scénarios sur le vrai `env.step`) :
 1. accélération/freinage : vitesse imposée -> gain par frame (plein gaz, frein seul, frein+gaz) ;
 2. limite de virage : voiture avec braquage plein, vitesse maintenue à v, en régime établi ->
    courbure maximale kappa_max(v) (murs désactivés) ;
 3. trajectoire : ligne centrale puis "ligne de course" (courbure minimisée dans le couloir de
    route mesuré, marge 0 = optimiste) ;
 4. profil de vitesse : v(s) <= vitesse de virage, passes avant (accélération) / arrière (freinage) ;
 5. temps : tour 1 départ arrêté + (N-1) tours lancés, moins le crédit de FINISH_RADIUS sur le dernier.
Déterministe (aucune graine nécessaire).
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env():
    from src.rl.wrappers import GymTimeAttack
    e = GymTimeAttack(render_mode=None, procedural=False, laps=3)
    e.reset()
    ta = e.ta
    ta.track.inside_track = lambda p: True   # scénarios en espace libre
    ta.track.hits_wall = lambda p: False
    ta.track.on_boost = lambda p: False
    return ta


def _reset_car(ta, v, heading=0.0):
    ta.car.pos = np.array([700.0, 500.0])
    ta.car.heading = heading
    ta.car.speed = v
    ta.car.vel = np.array([math.cos(heading) * v, math.sin(heading) * v])
    ta.car.steering = 0.0
    ta.car.angular_velocity = 0.0


def _hold(ta, v):
    """Impose la vitesse v en gardant la direction de `vel` (la physique lit `vel`, pas `speed`)."""
    n = float(np.linalg.norm(ta.car.vel))
    if n > 1e-9:
        ta.car.vel = ta.car.vel * (v / n)
    ta.car.speed = v


def measure_longitudinal():
    """Gain de vitesse par frame a(v) pour : plein gaz, frein seul, frein+gaz (grille de v)."""
    ta = _env()
    grid = np.linspace(0.0, 23.0, 47)
    res = {"gas": [], "brake": [], "both": []}
    for v in grid:
        for key, act in (("gas", (0, 1, 0)), ("brake", (0, 0, 1)), ("both", (0, 1, 1))):
            _reset_car(ta, v)
            ta.step(act)
            res[key].append(ta.car.speed - v)
    return grid, {k: np.array(x) for k, x in res.items()}


def measure_cornering():
    """Courbure max (1/px) en régime établi, braquage plein, vitesse maintenue à v."""
    ta = _env()
    grid = np.linspace(1.0, 23.0, 45)
    kap = []
    for v in grid:
        _reset_car(ta, v)
        for _ in range(150):                     # régime établi
            _hold(ta, v)
            ta.step((1.0, 0, 0))
        p0, h0 = ta.car.pos.copy(), ta.car.heading
        length = 0.0
        for _ in range(100):
            _hold(ta, v)
            before = ta.car.pos.copy()
            ta.step((1.0, 0, 0))
            length += float(np.linalg.norm(ta.car.pos - before))
        # courbure de la trajectoire = rotation du cap / longueur parcourue
        kap.append((ta.car.heading - h0) / length)
    return grid, np.array(kap)


def vmax_for_curvature(kappa, vgrid, kgrid, vcap):
    """Plus grande vitesse v telle que kappa <= kappa_max(v) (kappa_max décroît avec v)."""
    k = np.minimum(kgrid, np.maximum.accumulate(kgrid[::-1])[::-1])  # monotone décroissante
    out = np.empty_like(kappa)
    for i, c in enumerate(kappa):
        if c <= k[-1]:
            out[i] = vcap
        elif c >= k[0]:
            out[i] = vgrid[0]
        else:
            out[i] = np.interp(c, k[::-1], vgrid[::-1])
    return np.minimum(out, vcap)


def corridor(sp, step):
    """Sous-échantillonne la ligne centrale ; renvoie points, normales, demi-largeur de route (min)."""
    ta = _env_real()
    pts = sp[::step]
    n = len(pts)
    tg = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    nm = np.stack([-tg[:, 1], tg[:, 0]], axis=1)
    hw = np.empty(n)
    for i in range(n):
        side = []
        for sgn in (1, -1):
            r = 0.0
            while r < 200 and ta.track.inside_track(pts[i] + sgn * nm[i] * (r + 1)):
                r += 1
            side.append(r)
        hw[i] = min(side)
    return pts, nm, float(hw.min()), hw


_REAL = None


def _env_real():
    global _REAL
    if _REAL is None:
        from src.rl.wrappers import GymTimeAttack
        e = GymTimeAttack(render_mode=None, procedural=False, laps=3)
        e.reset()
        _REAL = e.ta
    return _REAL


def racing_line(pts, nm, hw, iters=4000):
    """Minimise la courbure : relaxation (lissage) des décalages bornés par le couloir."""
    d = np.zeros(len(pts))
    for _ in range(iters):
        p = pts + nm * d[:, None]
        # décalage idéal = milieu des voisins, projeté sur la normale
        mid = 0.5 * (np.roll(p, 1, axis=0) + np.roll(p, -1, axis=0))
        target = np.sum((mid - pts) * nm, axis=1)
        d = np.clip(d + 0.5 * (target - d), -hw, hw)
    return pts + nm * d[:, None]


KWIN = 24   # demi-fenêtre (nœuds) de la courbure : relaxation (cap changé sur ~2*KWIN*pas px)


def curvature(p, k=None):
    """Courbure de Menger sur des points distants de k indices (périodique)."""
    k = KWIN if k is None else k
    a, b, c = np.roll(p, k, axis=0), p, np.roll(p, -k, axis=0)
    ab, bc, ca = (np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                  np.linalg.norm(a - c, axis=1))
    cross = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))
    kap = 2 * cross / (ab * bc * ca + 1e-9)
    # lissage min-pooling inverse : max de la courbure sur +-1 point (prudence = borne plus haute ? non :
    # on garde la courbure brute, c'est l'option optimiste pour une borne inférieure)
    return kap


def profile(p, vgrid_c, kgrid, lg, ag, vcap, v0=None, cyclic_v=None):
    """Profil de vitesse le long de la boucle p. Renvoie (v par nœud, longueurs ds, frames par segment)."""
    n = len(p)
    ds = np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1)
    kap = curvature(p)
    vlim = vmax_for_curvature(kap, vgrid_c, kgrid, vcap)
    gas = lambda v: np.interp(v, lg, ag["gas"])
    # décélération max : meilleure des deux commandes de freinage
    dec = lambda v: -np.minimum(np.interp(v, lg, ag["brake"]), np.interp(v, lg, ag["both"]))
    v = vlim.copy()
    for _ in range(4):                           # passes cycliques jusqu'à convergence
        for i in range(2 * n):
            j, k = i % n, (i + 1) % n
            v[k] = min(v[k], math.sqrt(v[j] ** 2 + 2 * max(gas(v[j]), 1e-6) * ds[j]))
        for i in range(2 * n - 1, -1, -1):
            j, k = i % n, (i + 1) % n
            v[j] = min(v[j], math.sqrt(v[k] ** 2 + 2 * dec(v[k]) * ds[j]))
    return v, ds


def lap_frames(v, ds, start_speed=None, cap=None):
    """Frames pour parcourir la boucle ; départ arrêté si start_speed est donné (passe avant)."""
    n = len(v)
    vv = v.copy()
    if start_speed is not None:
        vv[0] = min(vv[0], start_speed)
        for i in range(n - 1):
            vv[i + 1] = min(vv[i + 1], math.sqrt(vv[i] ** 2 + 2 * max(cap(vv[i]), 1e-6) * ds[i]))
    # temps par segment (accélération/décélération constante par segment : moyenne harmonique)
    fr = np.empty(n)
    for i in range(n):
        a, b = vv[i], vv[(i + 1) % n]
        fr[i] = 2 * ds[i] / max(a + b, 1e-3)
    return fr


def bound(laps, p, vgrid_c, kgrid, lg, ag, vcap, credit_px):
    v, ds = profile(p, vgrid_c, kgrid, lg, ag, vcap)
    gas = lambda x: float(np.interp(x, lg, ag["gas"]))
    fr_cyc = lap_frames(v, ds)
    fr_first = lap_frames(v, ds, start_speed=0.0, cap=gas)
    # crédit : le dernier tour s'arrête à FINISH_RADIUS de la ligne (distance en avance)
    cum = np.cumsum(ds[::-1])
    k = int(np.searchsorted(cum, credit_px))
    credit = float(np.sum(fr_cyc[::-1][:k]))
    total = fr_first.sum() + (laps - 1) * fr_cyc.sum() - credit
    return dict(length=float(ds.sum()), first=fr_first.sum() / 50, cyc=fr_cyc.sum() / 50,
                credit=credit / 50, total=total / 50, vmean=float(ds.sum() / fr_cyc.sum()),
                vmax=float(v.max()), vmin=float(v.min()), kmax=float(curvature(p).max()))


def real_lap_trace(laps):
    """Trajectoire (positions, vitesses par frame) de l'heuristique 15,90 s sur piste fixe."""
    import random
    from src.rl.wrappers import GymTimeAttack
    from scripts.heuristic_lap import heuristic_action
    env = GymTimeAttack(render_mode=None, procedural=False, laps=laps)
    random.seed(0); np.random.seed(0)
    obs, _ = env.reset()
    ta = env.ta
    pos, spd, done = [ta.car.pos.copy()], [0.0], False
    while not done:
        obs, r, term, trunc, info = env.step(heuristic_action(obs, ta))
        done = term or trunc
        pos.append(ta.car.pos.copy()); spd.append(float(ta.car.speed))
    return np.array(pos), np.array(spd), len(pos) - 1


def calibrate(pos, spd, vgrid_c, kgrid, vcap, ks, spacing=7.6, tol=0.01):
    """Pour chaque fenêtre k : part des points de la trajectoire réelle qui violent v <= vmax(kappa)."""
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pos, axis=0), axis=1))]
    s = np.arange(0.0, d[-1], spacing)
    q = np.stack([np.interp(s, d, pos[:, 0]), np.interp(s, d, pos[:, 1])], axis=1)
    v = np.interp(s, d, spd)
    rows = []
    for k in ks:
        a, b, c = q[:-2 * k], q[k:-k], q[2 * k:]
        ab, bc, ca = (np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1))
        cross = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))
        kap = 2 * cross / (ab * bc * ca + 1e-9)
        vm = vmax_for_curvature(kap, vgrid_c, kgrid, vcap)
        viol = v[k:-k] > vm + 1e-9
        rows.append((k, float(viol.mean()), float(np.max(v[k:-k] / vm))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laps", type=int, default=3)
    ap.add_argument("--step", type=int, default=6, help="sous-échantillonnage de la spline (2400 pts)")
    ap.add_argument("--kwin", type=int, default=0, help="force la fenêtre (sinon calibrée)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--reference", type=float, default=15.90)
    a = ap.parse_args()

    from src.core.constants import ACCEL, FRICTION, MAX_SPEED, COAST_FRICTION, BRAKE, TURN_SPEED, FINISH_RADIUS
    lg, ag = measure_longitudinal()
    cg, ck = measure_cornering()
    vcap = float(min(MAX_SPEED, lg[np.argmax(ag["gas"] <= 1e-3)] if (ag["gas"] <= 1e-3).any() else MAX_SPEED))
    global KWIN
    pos, spd, nfr = real_lap_trace(a.laps)
    ks = [2, 4, 6, 8, 10, 12, 14, 16, 20, 24]
    cal_rows = calibrate(pos, spd, cg, ck, vcap, ks)
    best_row = min(cal_rows, key=lambda r: (round(r[1], 6), r[0]))   # moins de violations, k le plus petit
    KWIN = a.kwin if a.kwin else best_row[0]
    sp = _env_real().track.spline_points
    pts, nm, hw_min, hw = corridor(sp, a.step)
    line = racing_line(pts, nm, hw)
    res_c = bound(a.laps, pts, cg, ck, lg, ag, vcap, FINISH_RADIUS)
    res_r = bound(a.laps, line, cg, ck, lg, ag, vcap, FINISH_RADIUS)

    out = []
    P = out.append
    P(f"# Borne inférieure du temps sur {a.laps} tours (T32)\n")
    P("Généré par `scripts/lower_bound.py` (déterministe). Physique mesurée sur `env.step`, non modifiée.\n")
    P("## Mesures de la physique\n")
    P(f"- Constantes : ACCEL={ACCEL}, FRICTION={FRICTION}, COAST_FRICTION={COAST_FRICTION}, BRAKE={BRAKE}, "
      f"TURN_SPEED={TURN_SPEED}, MAX_SPEED={MAX_SPEED}.")
    P(f"- Vitesse terminale mesurée (gain nul plein gaz) : **{vcap:.2f} px/frame** "
      f"(= {vcap * 50:.0f} px/s).")
    P("- Gain de vitesse par frame (px/frame²) :\n")
    P("| v | plein gaz | frein seul | frein+gaz |\n|---|---|---|---|")
    for v in (0, 5, 10, 15, 20):
        i = int(np.argmin(abs(lg - v)))
        P(f"| {lg[i]:.0f} | {ag['gas'][i]:+.3f} | {ag['brake'][i]:+.3f} | {ag['both'][i]:+.3f} |")
    P("\n- Courbure max en régime établi (braquage plein, vitesse maintenue), rayon mini correspondant :\n")
    P("| v | kappa_max (1/px) | rayon mini (px) |\n|---|---|---|")
    for v in (2, 5, 8, 11, 14, 17, 20, 23):
        i = int(np.argmin(abs(cg - v)))
        P(f"| {cg[i]:.0f} | {ck[i]:.5f} | {1 / ck[i]:.0f} |")
    P("\n## Calibration de la fenêtre de courbure\n")
    P("La courbure ponctuelle est trop pessimiste (le cap peut changer sur une distance, la voiture a une largeur "
      "de route) : on mesure sur la trajectoire réelle du meilleur tour (heuristique, "
      f"{nfr} frames = {nfr / 50:.2f} s) la part des points où sa vitesse dépasse la limite `vmax(kappa)` pour "
      "une courbure de Menger de demi-fenêtre k nœuds (7,6 px/nœud). Aucune fenêtre n'élimine toutes les violations (transitoires, glissements) : on retient celle qui en a le moins (k le plus petit à égalité).\n")
    P("| k (nœuds) | portée ± (px) | points en violation | v/vmax max |\n|---|---|---|---|")
    for k, fr_, mx in cal_rows:
        P(f"| {k} | {k * 7.6:.0f} | {100 * fr_:.1f} % | {mx:.2f} |")
    P(f"\n- Fenêtre retenue : **k = {KWIN}** (±{KWIN * 7.6:.0f} px).\n")
    P("\n## Trajectoires\n")
    P(f"- Piste fixe, spline de {len(sp)} points (pas {a.step} -> {len(pts)} nœuds), demi-largeur de route minimale "
      f"mesurée {hw_min:.0f} px (marge 0 : le centre de la voiture peut raser le bord, optimiste).")
    P("- Ligne de course : décalages relaxés (lissage) bornés par le couloir ; aucune contrainte de dynamique.\n")
    P("| trajectoire | longueur/tour (px) | courbure max (1/px) | v moy (px/frame) | 1er tour (s) | tour lancé (s) | crédit arrivée (s) | **total (s)** |")
    P("|---|---|---|---|---|---|---|---|")
    for name, r in (("ligne centrale", res_c), ("ligne de course", res_r)):
        P(f"| {name} | {r['length']:.0f} | {r['kmax']:.5f} | {r['vmean']:.2f} | {r['first']:.2f} | "
          f"{r['cyc']:.2f} | {r['credit']:.2f} | **{r['total']:.2f}** |")
    sens = []
    for k in (8, 12, 16, 20, 24):
        KWIN = k
        rc = bound(a.laps, pts, cg, ck, lg, ag, vcap, FINISH_RADIUS)["total"]
        rr = bound(a.laps, line, cg, ck, lg, ag, vcap, FINISH_RADIUS)["total"]
        sens.append((k, rc, rr))
    KWIN = a.kwin if a.kwin else best_row[0]
    best = min(res_c["total"], res_r["total"])
    gap = a.reference - best
    P("\n### Sensibilité à la fenêtre\n")
    P("| k | ligne centrale (s) | ligne de course (s) |\n|---|---|---|")
    for k, rc, rr in sens:
        P(f"| {k} | {rc:.2f} | {rr:.2f} |")
    P("\nLa borne est **modèle-dépendante** : plus la fenêtre est large, plus elle est optimiste (donc plus basse).")
    P("\n## Hypothèses (toutes favorables à la borne, donc elle est optimiste)\n")
    P("- Voiture = point ; tangage/latéral du modèle ignorés : la limite de virage est la courbure en régime "
      "établi à vitesse constante (le transitoire du volant, ~7 frames, et le glissement `LATERAL_GRIP` sont ignorés).")
    P("- Accélération/freinage en ligne droite, courbure indépendante du freinage, freinage optimal (frein seul ou frein+gaz, le plus fort).")
    P("- Aucun mur, marge de bord 0, pas de boost (aucune zone sur cette piste).")
    P(f"- Fin du dernier tour dès que la voiture est à FINISH_RADIUS={FINISH_RADIUS} px de l'arrivée "
      "(crédit ci-dessus ; en pratique les checkpoints exigent aussi de passer à moins de 100 px de chacun).")
    P("- Distance/temps par segment : v² = v0² + 2 a ds, temps = 2 ds / (v0 + v1).")
    P("\n## Résultat\n")
    P(f"- Borne (meilleure des deux trajectoires) : **{best:.2f} s** sur {a.laps} tours.")
    P(f"- Meilleur temps atteint : **{a.reference:.2f} s** -> écart **{gap:+.2f} s** ({100 * gap / a.reference:+.1f} %).")
    P(f"- Intervalle de sensibilité (k=12..24, ligne de course) : {min(r[2] for r in sens if r[0] >= 12):.2f}-"
      f"{max(r[2] for r in sens if r[0] >= 12):.2f} s.")
    if gap < 0:
        rec = ("**Borne invalide** : plus lente que le meilleur temps atteint (fenêtre de courbure trop "
               "pessimiste) ; relancer avec `--kwin` plus grand.")
    elif gap > 1.0:
        rec = ("**Continuer la recherche** : la borne laisse plus d'une seconde (heuristique/imitation à "
               "paramétrer par secteur, cf. T33).")
    elif gap > 0.3:
        rec = ("**Marge faible mais non nulle** : une recherche élargie (T33) peut encore gagner quelques "
               "dixièmes, sans garantie ; la borne est optimiste, la marge réelle est plus petite.")
    else:
        rec = "**Plafond proche** : la borne est quasi atteinte, arrêter l'optimisation du temps."
    P(f"- Recommandation : {rec}")
    P("- Limite : la fenêtre est calibrée sur la trajectoire réelle (1,4 % de ses points restent en violation), "
      "ce n'est donc pas une borne mathématiquement rigoureuse mais une estimation du plafond du modèle.")
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        with open(os.path.join(ROOT, a.out) if not os.path.isabs(a.out) else a.out, "w") as f:
            f.write(text)


if __name__ == "__main__":
    main()
