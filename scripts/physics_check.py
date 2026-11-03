"""Banc physique (headless) : mouvement longitudinal, virage et adhérence.

Usage : SDL_VIDEODRIVER=dummy python scripts/physics_check.py [--metrics chemin.json]
Piste fixe (build_track). Pour isoler la physique longitudinale, murs et boost sont
neutralisés sur l'instance (voiture libre en ligne droite). Déterministe : aucun aléa.
Unités : px/frame (vitesse de l'env) et px/s (= px/frame * FPS).
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.constants import FPS, MAX_SPEED
from src.game.env import TimeAttackEnv
from src.game.track import build_track

DEFAULT_METRICS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".team", "metrics.json")
MAX_FRAMES = 5000


def _free_env():
    env = TimeAttackEnv(build_track(), procedural=False)
    env.track.inside_track = lambda p: True
    env.track.hits_wall = lambda p: False
    env.track.on_boost = lambda p: False
    env._update_checkpoints = lambda: None
    env._check_finish = lambda: False
    return env


def _terminal(env):
    """Pleine accélération jusqu'à convergence ; renvoie (vitesse, courbe)."""
    curve = []
    for _ in range(MAX_FRAMES):
        env.step((0.0, 1.0, 0.0))
        curve.append(env.car.speed)
        if len(curve) > 1 and abs(curve[-1] - curve[-2]) < 1e-9:
            break
    return curve[-1], curve


# Seuils « réalistes » (voir journal T8) : chaque scénario a un statut pass/fail.
TURN_RADIUS_RANGE = (20.0, 600.0)   # px, braquage plein ; ordre de grandeur largeur piste 90 px
MAX_DRIFT_DEG = 18.0                # angle heading/vel en régime établi
MAX_STEER_REACTION_FRAMES = 15      # braquage plein atteint en <= 15 frames
MAX_YAW_RATE_RAD_S = 6.0            # vitesse de rotation max plausible
TURN_SPEEDS = (5.0, 15.0, 22.0)


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _turn(v, steer=1.0, frames=300):
    """Braquage constant, vitesse maintenue ~v ; mesure en régime établi (50 dernières frames)."""
    env = _free_env()
    c = env.car
    h0 = c.heading
    c.speed = v
    c.vel = c.vel * 0 + [math.cos(h0) * v, math.sin(h0) * v]
    hs, drifts, speeds, steer_frames = [], [], [], None
    for i in range(frames):
        c.speed = v  # maintien de la vitesse (cible)
        env.step((steer, 0.0, 0.0))
        if steer_frames is None and abs(c.steering - steer) < 1e-9:
            steer_frames = i + 1
        hs.append(c.heading)
        speeds.append(c.speed)
        drifts.append(abs(_wrap(math.atan2(c.vel[1], c.vel[0]) - c.heading)))
    w = (hs[-1] - hs[-51]) / 50
    vel_mag = float(math.hypot(*c.vel))
    return {
        "yaw_rate_rad_frame": w,
        "radius_px": vel_mag / abs(w) if w else float("inf"),
        "drift_deg": math.degrees(max(drifts[-50:])),
        "steer_frames": steer_frames,
    }


def measure_turn():
    out, ok = {}, True
    radii = []
    for v in TURN_SPEEDS:
        r = _turn(v)
        rad = r["radius_px"]
        radii.append(rad)
        yaw_s = abs(r["yaw_rate_rad_frame"]) * FPS
        passed = (TURN_RADIUS_RANGE[0] <= rad <= TURN_RADIUS_RANGE[1]
                  and r["drift_deg"] <= MAX_DRIFT_DEG and yaw_s <= MAX_YAW_RATE_RAD_S)
        ok &= passed
        out[f"v{int(v)}"] = {
            "turn_radius_px": round(rad, 2),
            "yaw_rate_rad_s": round(yaw_s, 3),
            "drift_deg_steady": round(r["drift_deg"], 3),
            "pass": bool(passed),
        }
    out["steer_full_lock_frames"] = _turn(15.0)["steer_frames"]
    out["steer_reaction_pass"] = bool(out["steer_full_lock_frames"] <= MAX_STEER_REACTION_FRAMES)
    out["radius_increases_with_speed"] = bool(radii == sorted(radii))
    out["pass"] = bool(ok and out["steer_reaction_pass"] and out["radius_increases_with_speed"])
    return out


def measure_out_of_range():
    """Actions hors bornes : steer=5, accel=-1, brake=-1, accel=3. Physique doit rester bornée."""
    res = {}
    # steer=5 : le braquage effectif doit rester <= 1 et la rotation plausible
    t = _turn(15.0, steer=5.0, frames=200)
    env = _free_env()
    for _ in range(100):
        env.step((5.0, 0.0, 0.0))
    res["steer5_steering_value"] = round(float(env.car.steering), 3)
    res["steer5_yaw_rate_rad_s"] = round(abs(t["yaw_rate_rad_frame"]) * FPS, 3)
    res["steer5_pass"] = bool(env.car.steering <= 1.0 + 1e-9)
    # accel=-1 : ne doit pas accélérer ni produire de NaN
    env = _free_env()
    for _ in range(50):
        env.step((0.0, -1.0, 0.0))
    res["accel_neg1_speed"] = round(float(env.car.speed), 4)
    res["accel_neg1_pass"] = bool(env.car.speed <= 1e-9)
    # brake=-1 : un frein négatif ne doit pas accélérer
    env = _free_env()
    for _ in range(50):
        env.step((0.0, 0.0, -1.0))
    res["brake_neg1_speed"] = round(float(env.car.speed), 4)
    res["brake_neg1_pass"] = bool(env.car.speed <= 1e-9)
    # accel=3 : ne doit pas dépasser accel=1
    e1, e3 = _free_env(), _free_env()
    for _ in range(50):
        e1.step((0.0, 1.0, 0.0))
        e3.step((0.0, 3.0, 0.0))
    res["accel3_speed_after_50"] = round(float(e3.car.speed), 4)
    res["accel1_speed_after_50"] = round(float(e1.car.speed), 4)
    res["accel3_pass"] = bool(e3.car.speed <= e1.car.speed + 1e-9)
    # finitude
    res["all_finite"] = bool(all(math.isfinite(x) for x in (*e3.car.pos, *e3.car.vel, e3.car.heading)))
    res["pass"] = bool(all(v for k, v in res.items() if k.endswith("_pass")) and res["all_finite"])
    return res


# ---- T9 : murs, boost, checkpoints, arrivée, départ, reproductibilité ----
MAX_TELEPORT_PX = 1.0               # saut de position toléré au-delà de |vel| de la frame
MAX_SPEED_VEL_MISMATCH = 0.25       # |speed-|vel|| / max(speed,1) toléré juste après un choc
BOOST_CAP = MAX_SPEED * 1.2
MIN_TERMINAL_RATIO = 0.95           # la vitesse terminale doit atteindre 95 % de MAX_SPEED


def _real_env(seed=42):
    return TimeAttackEnv(build_track(seed), procedural=False)


def _wall_run(angle_off, v=15.0, frames=200):
    env = _real_env()
    c = env.car
    c.heading = env.track.start_heading + angle_off
    c.speed = v
    c.vel = c.vel * 0 + [math.cos(c.heading) * v, math.sin(c.heading) * v]
    outside, max_jump, max_mismatch, hit = 0, 0.0, 0.0, False
    for _ in range(frames):
        p0 = c.pos.copy()
        speed0 = c.speed
        env.step((0.0, 1.0, 0.0))
        if not env.track.inside_track(c.pos):
            outside += 1
        jump = float(math.hypot(*(c.pos - p0)))
        vm = float(math.hypot(*c.vel))
        max_jump = max(max_jump, jump - vm)
        if jump < 0.5 * vm or c.speed < 0.97 * speed0:  # frame de contact (vitesse cassée par le mur)
            hit = True
            max_mismatch = max(max_mismatch, abs(c.speed - vm) / max(c.speed, 1.0))
    finite = all(math.isfinite(x) for x in (*c.pos, *c.vel, c.heading, c.speed))
    return {"frames_outside_track": outside, "max_jump_over_vel_px": round(max_jump, 3),
            "max_speed_vel_mismatch": round(max_mismatch, 3), "contact_seen": hit,
            "final_speed": round(float(c.speed), 3), "finite": bool(finite)}


def measure_walls():
    res = {}
    ok = True
    for name, off in (("perpendicular", math.pi / 2), ("oblique", math.pi / 4)):
        r = _wall_run(off)
        r["pass_inside"] = r["frames_outside_track"] == 0 and r["finite"]
        r["pass_no_teleport"] = r["max_jump_over_vel_px"] <= MAX_TELEPORT_PX
        r["pass_speed_vel_coherent"] = r["max_speed_vel_mismatch"] <= MAX_SPEED_VEL_MISMATCH
        ok &= r["pass_inside"] and r["pass_no_teleport"] and r["pass_speed_vel_coherent"]
        res[name] = r
    res["pass"] = bool(ok)
    return res


def measure_boost():
    env = _free_env()
    import pygame
    env.track.boost_zones = [pygame.Rect(-100000, -100000, 200000, 200000)]
    env.track.on_boost = type(env.track).on_boost.__get__(env.track)
    peak = 0.0
    for _ in range(400):
        env.step((0.0, 1.0, 0.0))
        peak = max(peak, env.car.speed)
    return {"peak_speed": round(float(peak), 3), "cap": BOOST_CAP,
            "over_max_speed": bool(peak > MAX_SPEED + 1e-9),
            "pass": bool(peak <= BOOST_CAP + 1e-9)}


def _teleport(env, cp):
    env.car.pos = np.array([cp[0], cp[1]], dtype=float)


def measure_checkpoints():
    env = _real_env()
    cps, n = env.track.checkpoints, len(env.track.checkpoints)
    res = {"n_checkpoints": n}
    # départ
    res["start_speed_zero"] = bool(env.car.speed == 0.0 and not env.car.vel.any())
    # hors ordre : dernier checkpoint d'abord ne doit rien valider
    env.reset()
    _teleport(env, cps[-1])
    env.step((0.0, 0.0, 0.0))
    res["out_of_order_ignored"] = bool(not any(env.cp_visited)) if n > 1 else True
    # finish avant les checkpoints
    env.reset()
    fx, fy = env.track.finish_pos[:2]
    env.car.pos = np.array([fx, fy], dtype=float)
    _, _, done, _ = env.step((0.0, 0.0, 0.0))
    res["finish_before_cps_ignored"] = bool(not done)
    # dans l'ordre : un par un (une seule validation par frame, pas de saut)
    env.reset()
    visited_counts = []
    for cp in cps:
        _teleport(env, cp)
        env.step((0.0, 0.0, 0.0))
        visited_counts.append(sum(env.cp_visited))
    res["in_order_counts"] = visited_counts
    res["in_order_ok"] = visited_counts == list(range(1, n + 1))
    # plusieurs CP dans le rayon d'un coup : au plus 1 par frame ?
    env.reset()
    _teleport(env, cps[0])
    env.step((0.0, 0.0, 0.0))
    res["max_one_cp_per_frame"] = bool(sum(env.cp_visited) <= 1)
    # arrivée après tous les CP
    env.reset()
    for cp in cps:
        _teleport(env, cp)
        env.step((0.0, 0.0, 0.0))
    env.car.pos = np.array([fx, fy], dtype=float)
    _, reward, done, _ = env.step((0.0, 0.0, 0.0))
    res["finish_after_all_cps"] = bool(done and reward == 100.0)
    keys = ("start_speed_zero", "out_of_order_ignored", "finish_before_cps_ignored",
            "in_order_ok", "max_one_cp_per_frame", "finish_after_all_cps")
    res["pass"] = bool(all(res[k] for k in keys))
    return res


def measure_reproducibility():
    def run():
        env = _real_env(7)
        rng = np.random.RandomState(0)
        out = []
        for _ in range(300):
            env.step((float(rng.uniform(-1, 1)), float(rng.uniform(0, 1)), float(rng.uniform(0, 0.3))))
            out.append((round(float(env.car.pos[0]), 9), round(float(env.car.pos[1]), 9)))
        return out
    return {"pass": bool(run() == run())}


def measure_world():
    res = {"walls": measure_walls(), "boost": measure_boost(),
           "checkpoints": measure_checkpoints(), "reproducibility": measure_reproducibility()}
    res["pass"] = bool(all(v["pass"] for v in res.values()))
    return res


def measure():
    env = _free_env()
    start_speed = env.car.speed
    vterm, curve = _terminal(env)
    t90 = next((i + 1 for i, v in enumerate(curve) if v >= 0.9 * vterm), None)
    t90_max = next((i + 1 for i, v in enumerate(curve) if v >= 0.9 * MAX_SPEED), None)

    # Freinage depuis la vitesse terminale
    x0 = env.car.pos.copy()
    frames = 0
    while env.car.speed > 1e-3 and frames < MAX_FRAMES:
        env.step((0.0, 0.0, 1.0))
        frames += 1
    brake_dist = float(math.hypot(*(env.car.pos - x0)))

    # Roue libre depuis la vitesse terminale
    env = _free_env()
    env.car.speed = vterm
    env.car.vel = env.car.vel * 0 + [math.cos(env.car.heading) * vterm, math.sin(env.car.heading) * vterm]
    v0 = env.car.speed
    n = 50
    for _ in range(n):
        env.step((0.0, 0.0, 0.0))
    coast_decel = (v0 - env.car.speed) / n

    # Marche arrière : frein à l'arrêt
    env = _free_env()
    for _ in range(20):
        env.step((0.0, 0.0, 1.0))
    reverse_possible = env.car.speed < 0

    return {
        "fps": FPS,
        "start_speed": start_speed,
        "max_speed_const": MAX_SPEED,
        "terminal_speed_px_frame": round(vterm, 4),
        "terminal_speed_px_s": round(vterm * FPS, 2),
        "terminal_over_max": round(vterm / MAX_SPEED, 4),
        "terminal_reaches_max": {"ratio": round(vterm / MAX_SPEED, 4), "min_ratio": MIN_TERMINAL_RATIO,
                                 "pass": bool(vterm >= MIN_TERMINAL_RATIO * MAX_SPEED)},
        "frames_to_90pct_terminal": t90,
        "time_to_90pct_terminal_s": round(t90 / FPS, 3) if t90 else None,
        "frames_to_90pct_MAX_SPEED": t90_max,  # None = MAX_SPEED inatteignable
        "brake_frames_to_stop": frames,
        "brake_distance_px": round(brake_dist, 2),
        "coast_decel_px_frame2": round(coast_decel, 4),
        "coast_decel_pct_per_frame": round(100 * (1 - (1 - coast_decel / v0)), 3),
        "reverse_possible": reverse_possible,
        "turn": measure_turn(),
        "out_of_range_actions": measure_out_of_range(),
        "world": measure_world(),
    }


def summarize(res):
    """Résumé global : un scénario = un booléen pass nommé ; liste des fails."""
    t, o, w = res["turn"], res["out_of_range_actions"], res["world"]
    sc = {f"turn_{k}": t[k]["pass"] for k in t if k.startswith("v") and isinstance(t[k], dict)}
    sc["turn_steer_reaction"] = t["steer_reaction_pass"]
    sc["turn_radius_increases_with_speed"] = t["radius_increases_with_speed"]
    for k in ("steer5", "accel_neg1", "brake_neg1", "accel3"):
        sc[f"out_of_range_{k}"] = o[f"{k}_pass"]
    sc["terminal_reaches_max_speed"] = res["terminal_reaches_max"]["pass"]
    sc["out_of_range_finite"] = o["all_finite"]
    for k in ("perpendicular", "oblique"):
        sc[f"walls_{k}_inside"] = w["walls"][k]["pass_inside"]
        sc[f"walls_{k}_no_teleport"] = w["walls"][k]["pass_no_teleport"]
        sc[f"walls_{k}_speed_vel_coherent"] = w["walls"][k]["pass_speed_vel_coherent"]
    for k in ("boost", "checkpoints", "reproducibility"):
        sc[f"world_{k}"] = w[k]["pass"]
    sc = {k: bool(v) for k, v in sc.items()}
    fails = sorted(k for k, v in sc.items() if not v)
    return {"n_scenarios": len(sc), "n_pass": len(sc) - len(fails), "fails": fails}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", default=DEFAULT_METRICS)
    a = p.parse_args(argv)
    res = measure()
    res["summary"] = summarize(res)
    print(json.dumps(res, ensure_ascii=False, sort_keys=True))
    data = []
    if os.path.exists(a.metrics):
        with open(a.metrics) as f:
            data = json.load(f)
    data.append({"date": time.strftime("%Y-%m-%d %H:%M"), "physics_check": res})
    with open(a.metrics, "w") as f:
        json.dump(data, f, indent=2)
    return res


if __name__ == "__main__":
    main()
