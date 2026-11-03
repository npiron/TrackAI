"""Audit de validité des tours rapides (T29).

Usage : python scripts/audit_lap.py --static --laps 3 [--out docs/AUDIT_T29.md]
Pour `best/` et l'heuristique : par tour, temps, vitesse moyenne/max, ordre des checkpoints,
distance min au bord de piste, frames hors piste / contact mur, couverture de la ligne centrale
(plus grand saut d'indice de spline entre deux frames, fraction parcourue). Déterministe.
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def audit(model_path, laps=3, seed=0):
    from src.core.constants import MAX_SPEED, TRACK_WIDTH, CHECKPOINT_RADIUS
    from src.rl.wrappers import GymTimeAttack
    from scripts.eval import _load_model
    env = GymTimeAttack(render_mode=None, procedural=False, laps=laps)
    if model_path == "heuristic":
        from scripts.heuristic_lap import heuristic_action
        model = vn = None
    else:
        model, vn = _load_model(model_path)
    random.seed(seed); np.random.seed(seed)
    obs, _ = env.reset()
    ta = env.ta
    sp = ta.track.spline_points
    n = len(sp)
    # longueur de la ligne centrale
    center_len = float(np.sum(np.linalg.norm(np.roll(sp, -1, axis=0) - sp, axis=1)))
    # demi-largeur réelle mesurée sur le masque (normale à la ligne centrale, min des deux côtés)
    hw = []
    for i in range(0, n, 10):
        tg = sp[(i + 1) % n] - sp[i - 1]
        tg = tg / np.linalg.norm(tg)
        nm = np.array([-tg[1], tg[0]])
        for sgn in (1, -1):
            r = 0
            while r < 200 and ta.track.inside_track(sp[i] + sgn * nm * r):
                r += 1
            hw.append(r)
    half = float(min(hw))
    cur = dict(frames=0, speeds=[], min_edge=1e9, off=0, wall=0, cps=[], idx_jumps=[], path=0.0, t0=0)
    laps_out, done, step = [], False, 0
    prev_pos = ta.car.pos.copy()
    prev_idx = int(np.argmin(np.sum((sp - ta.car.pos) ** 2, axis=1)))
    cum_idx = 0  # indice déroulé (somme des déplacements signés d'indice)
    lap_cum0 = 0
    prev_cp = list(ta.cp_visited)
    prev_laps = 0
    info = {}
    while not done:
        if model_path == "heuristic":
            a = heuristic_action(obs, ta)
        else:
            o = obs
            if vn is not None:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -vn.clip_obs, vn.clip_obs)
            a = int(model.predict(o, deterministic=True)[0])
        obs, r, term, trunc, info = env.step(a)
        done = term or trunc
        step += 1
        pos = ta.car.pos.copy()
        d = np.sqrt(np.sum((sp - pos) ** 2, axis=1))
        idx = int(np.argmin(d))
        jump = ((idx - prev_idx + n // 2) % n) - n // 2
        cum_idx += jump
        cur["idx_jumps"].append(abs(jump))
        prev_idx = idx
        cur["frames"] += 1
        cur["speeds"].append(ta.car.speed)
        cur["min_edge"] = min(cur["min_edge"], half - float(d[idx]))
        cur["path"] += float(np.linalg.norm(pos - prev_pos))
        if not ta.track.inside_track(pos):
            cur["off"] += 1
        # contact mur : déplacement différent de la vitesse (glissement/arrêt)
        if np.linalg.norm((pos - prev_pos) - ta.car.vel) > 1e-6:
            cur["wall"] += 1
        prev_pos = pos
        for i, (b, c) in enumerate(zip(prev_cp, ta.cp_visited)):
            if c and not b:
                cur["cps"].append((i, step))
        prev_cp = list(ta.cp_visited)
        if ta.lap_count != prev_laps or done:
            prev_laps = ta.lap_count
            cur["time"] = ta.lap_times[-1] if ta.lap_times else None
            cur["cover"] = (cum_idx - lap_cum0) / n
            lap_cum0 = cum_idx
            laps_out.append(cur)
            cur = dict(frames=0, speeds=[], min_edge=1e9, off=0, wall=0, cps=[], idx_jumps=[], path=0.0)
            prev_cp = list(ta.cp_visited)
    return dict(laps=laps_out, n_cp=len(ta.track.checkpoints), center_len=center_len, n=n,
                success=bool(info.get("is_success")), total=info.get("total_time"), max_speed=MAX_SPEED,
                half=half, cp_radius=CHECKPOINT_RADIUS, steps=step)


def fmt(name, r):
    L = [f"### {name}", "",
         f"success={r['success']}, temps total={r['total']:.2f} s, steps={r['steps']}, "
         f"demi-largeur route={r['half']:.0f} px, longueur ligne centrale={r['center_len']:.0f} px ({r['n']} pts), checkpoints={r['n_cp']}", "",
         "| tour | temps s | v moy | v max | chemin px | couverture ligne | ordre cp | min dist bord px (demi-largeur mesurée) | frames hors piste | frames contact mur | max saut idx |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, l in enumerate(r["laps"], 1):
        order = [c for c, _ in l["cps"]]
        ok = order == list(range(r["n_cp"]))
        L.append(f"| {k} | {l['time']:.2f} | {np.mean(l['speeds']):.2f} | {np.max(l['speeds']):.2f} | "
                 f"{l['path']:.0f} | {l['cover']:.3f} | {order} {'OK' if ok else 'ANOMALIE'} | "
                 f"{l['min_edge']:.1f} | {l['off']} | {l['wall']} | {max(l['idx_jumps'])} |")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--static", action="store_true")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--models", nargs="*", default=[os.path.join(ROOT, "data/models/best/best.zip"), "heuristic"])
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    out = ["# Audit T29", ""]
    for m in a.models:
        out.append(fmt(os.path.relpath(m, ROOT) if m != "heuristic" else m, audit(m, a.laps)))
    txt = "\n".join(out)
    print(txt)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt + "\n")


if __name__ == "__main__":
    main()
