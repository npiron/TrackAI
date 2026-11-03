"""Banc physique (headless) : mouvement longitudinal.

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
        "frames_to_90pct_terminal": t90,
        "time_to_90pct_terminal_s": round(t90 / FPS, 3) if t90 else None,
        "frames_to_90pct_MAX_SPEED": t90_max,  # None = MAX_SPEED inatteignable
        "brake_frames_to_stop": frames,
        "brake_distance_px": round(brake_dist, 2),
        "coast_decel_px_frame2": round(coast_decel, 4),
        "coast_decel_pct_per_frame": round(100 * (1 - (1 - coast_decel / v0)), 3),
        "reverse_possible": reverse_possible,
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", default=DEFAULT_METRICS)
    a = p.parse_args(argv)
    res = measure()
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
