"""Contrôleur heuristique sans apprentissage : poursuite du prochain checkpoint.

Usage : python scripts/heuristic_lap.py --static --laps 3 --episodes 20 --seed 0 [--metrics chemin.json]
La politique n'utilise que l'observation (14 floats) du GymTimeAttack ; l'évaluation passe par
scripts.eval.run_eval (model='heuristic'), donc même chrono et mêmes métriques que le banc.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Actions : 0 idle, 1 acc, 2 frein, 3 gauche, 4 droite, 5 G+acc, 6 D+acc, 7 G+frein, 8 D+frein
STEER_DEADZONE = 0.0342   # rad : en dessous on va tout droit
MAX_V_N = 1.0           # vitesse normalisée maximale visée
PREDICT_FRAMES = 9
SPEED_PER_RADIUS = 0.2567   # px/frame par px de rayon
MAX_SPEED_PX = 23.0
LOOK_MIN, LOOK_GAIN = 127, 400  # indices de spline en avance (± vitesse)
SECTOR_MULT = [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]        # multiplicateurs de SPEED_PER_RADIUS par secteur de spline (vide = 1 partout)
CORNER_V_N = 0.35       # vitesse visée pour un virage serré


def curve_speed_limit(ta, i, window=220, step=15):
    """Vitesse normalisée max pour tenir le plus serré des virages dans les `window` prochains points."""
    import numpy as np
    sp = ta.track.spline_points
    n = len(sp)
    idx = (i + np.arange(0, window, 10)) % n
    a, b, c = sp[idx], sp[(idx + step) % n], sp[(idx + 2 * step) % n]
    ab, bc, ca = (np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                  np.linalg.norm(a - c, axis=1))
    cross = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))
    radius = ab * bc * ca / (2 * cross + 1e-9)
    if SECTOR_MULT:
        mult = np.array(SECTOR_MULT)[idx * len(SECTOR_MULT) // n]
        return float(min(1.0, (SPEED_PER_RADIUS * mult * radius).min() / MAX_SPEED_PX))
    return float(min(1.0, SPEED_PER_RADIUS * radius.min() / MAX_SPEED_PX))


def closest_index(ta):
    import numpy as np
    return int(np.argmin(np.sum((ta.track.spline_points - ta.car.pos) ** 2, axis=1)))


def lookahead_error(ta, speed_n):
    """Erreur de cap (rad, >0 : à droite) vers un point de la ligne centrale en avance sur la voiture.

    Viser le centre de la route (et pas le checkpoint, parfois en coupant un virage) évite les murs.
    """
    import numpy as np
    sp = ta.track.spline_points
    i = closest_index(ta)
    ahead = int(LOOK_MIN + LOOK_GAIN * speed_n)
    tx, ty = sp[(i + ahead) % len(sp)]
    ang = math.atan2(ty - ta.car.pos[1], tx - ta.car.pos[0]) - ta.car.heading
    return math.atan2(math.sin(ang), math.cos(ang))


def heuristic_action(obs, ta=None):
    """Action discrète à partir de l'observation brute (et, si fourni, de la piste via `ta`)."""
    speed_n, tgt_x, tgt_y = float(obs[0]), float(obs[6]), float(obs[7])
    lidar_front = float(obs[11])
    if ta is not None:
        err = lookahead_error(ta, speed_n)
    else:
        err = math.atan2(tgt_y, tgt_x)  # >0 : cible à droite (cap à augmenter)
    # anticipation : la vitesse angulaire met ~20 images à s'éteindre (inertie de la direction)
    err -= PREDICT_FRAMES * float(obs[3])
    a = abs(err)
    # vitesse visée : décroît avec l'erreur d'angle et la proximité d'un mur devant
    v_target = MAX_V_N - (MAX_V_N - CORNER_V_N) * min(1.0, a / 0.8)
    if ta is not None:
        v_target = curve_speed_limit(ta, closest_index(ta))
    else:
        v_target = min(v_target, max(CORNER_V_N, lidar_front * 1.2))
    steer = 0 if a < STEER_DEADZONE else (1 if err > 0 else -1)
    if speed_n > v_target + 0.1:
        accel, brake = 0, 1
    elif speed_n > v_target:
        accel, brake = 0, 0
    else:
        accel, brake = 1, 0
    if steer == 0:
        return 1 if accel else (2 if brake else 0)
    if accel:
        return 6 if steer > 0 else 5
    if brake:
        return 8 if steer > 0 else 7
    return 4 if steer > 0 else 3


def main(argv=None):
    import argparse
    from scripts import eval as ev
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--static", action="store_true")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--metrics", default=ev.DEFAULT_METRICS)
    a = p.parse_args(argv)
    return ev.main(["--model", "heuristic", "--episodes", str(a.episodes), "--seed", str(a.seed),
                    "--laps", str(a.laps), "--metrics", a.metrics] + (["--static"] if a.static else []))


if __name__ == "__main__":
    main()
