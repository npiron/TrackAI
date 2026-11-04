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
INNER_OFFSET = 0.0      # px : décale la cible vers l'intérieur du virage (T49 ; 0 = comportement historique)
CROSS_GAIN = 0.0        # rad par px d'écart latéral à la ligne centrale (T49 ; >0 : rappelle vers le centre)
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


_LIMIT_CACHE = {}


def _limit_table(ta):
    """curve_speed_limit pour chaque indice de spline (ne dépend que de la piste ; mis en cache)."""
    import numpy as np
    key = (id(ta.track), id(ta.track.spline_points), len(ta.track.spline_points), SPEED_PER_RADIUS, tuple(SECTOR_MULT))
    t = _LIMIT_CACHE.get(key)
    if t is None:
        t = np.array([curve_speed_limit(ta, i) for i in range(len(ta.track.spline_points))])
        _LIMIT_CACHE.clear()
        _LIMIT_CACHE[key] = t
    return t


def _near_index(ta, hint, w=40):
    """Indice de spline le plus proche, cherché dans ±w autour de `hint` (rollouts : la voiture avance peu par image)."""
    import numpy as np
    sp = ta.track.spline_points
    idx = (hint + np.arange(-w, w + 1)) % len(sp)
    d = np.sum((sp[idx] - ta.car.pos) ** 2, axis=1)
    return int(idx[int(np.argmin(d))])


def closest_index(ta):
    import numpy as np
    return int(np.argmin(np.sum((ta.track.spline_points - ta.car.pos) ** 2, axis=1)))


def lookahead_error(ta, speed_n, i=None):
    """Erreur de cap (rad, >0 : à droite) vers un point de la ligne centrale en avance sur la voiture.

    Viser le centre de la route (et pas le checkpoint, parfois en coupant un virage) évite les murs.
    """
    import numpy as np
    sp = ta.track.spline_points
    if i is None:
        i = closest_index(ta)
    ahead = int(LOOK_MIN + LOOK_GAIN * speed_n)
    n = len(sp)
    tx, ty = sp[(i + ahead) % n]
    if INNER_OFFSET:
        a, c = sp[(i + ahead - 15) % n], sp[(i + ahead + 15) % n]
        d1, d2 = np.array([tx, ty]) - a, c - np.array([tx, ty])
        turn = math.atan2(d1[0] * d2[1] - d1[1] * d2[0], float(d1 @ d2))
        nrm = np.array([-d1[1], d1[0]]) / (np.linalg.norm(d1) + 1e-9)
        tx, ty = np.array([tx, ty]) + INNER_OFFSET * max(-1.0, min(1.0, turn / 0.3)) * nrm
    ang = math.atan2(ty - ta.car.pos[1], tx - ta.car.pos[0]) - ta.car.heading
    if CROSS_GAIN:
        t = sp[(i + 5) % len(sp)] - sp[i]
        t = t / (np.linalg.norm(t) + 1e-9)
        lat = t[0] * (ta.car.pos[1] - sp[i][1]) - t[1] * (ta.car.pos[0] - sp[i][0])  # >0 : voiture à droite (écran, y vers le bas)
        ang -= CROSS_GAIN * lat
    return math.atan2(math.sin(ang), math.cos(ang))


SAFE_HORIZON = 29       # T49 (32 → 29 en T57 : 14,62 s, 0 choc ; non monotone, 28 et 25 échouent) : > 0 = prédiction de N images ; écarte une action qui mène à un choc mur (0 = off)
_ACTS = {0: (0, 0, 0), 1: (0, 1, 0), 2: (0, 0, 1), 3: (-1, 0, 0), 4: (1, 0, 0),
         5: (-1, 1, 0), 6: (1, 1, 0), 7: (-1, 0, 1), 8: (1, 0, 1)}


def _sim_step(st, act, track):
    """Copie de la physique de TimeAttackEnv.step (hors boost/bords écran). st = [x, y, vx, vy, cap, vitesse, braquage, vit_ang].
    Renvoie (nouvel état, choc)."""
    from src.core.constants import ACCEL, BRAKE, COAST_FRICTION, FRICTION, LATERAL_GRIP, MAX_SPEED, TURN_SPEED
    x, y, vx, vy, hd, sp, stw, av = st
    steer, accel, brake = _ACTS[act]
    if accel:
        sp += ACCEL
    if brake:
        sp -= BRAKE
    sp *= FRICTION if accel else COAST_FRICTION
    sp = max(0.0, min(sp, MAX_SPEED))
    if steer > stw:
        stw = min(steer, stw + 0.15)
    elif steer < stw:
        stw = max(steer, stw - 0.15)
    av += (stw * TURN_SPEED - av) * 0.05
    hd += av * (1.0 - sp / MAX_SPEED * 0.3)
    vx = vx * (1 - LATERAL_GRIP) + math.cos(hd) * sp * LATERAL_GRIP
    vy = vy * (1 - LATERAL_GRIP) + math.sin(hd) * sp * LATERAL_GRIP
    nx, ny = x + vx, y + vy
    if not track.inside_track((nx, ny)):
        return None, True
    return [nx, ny, vx, vy, hd, sp, stw, av], False


def _rollout(st, first, ta, horizon):
    """Images survivées (horizon = aucun choc) en jouant `first` puis la politique de base."""
    import numpy as np
    from types import SimpleNamespace
    from src.core.constants import MAX_SPEED
    act = first
    ci = closest_index(ta)
    fake = SimpleNamespace(car=SimpleNamespace(pos=np.zeros(2), heading=0.0), track=ta.track)
    obs = np.zeros(14)
    for k in range(horizon):
        st, hit = _sim_step(st, act, ta.track)
        if hit:
            return k
        fake.car.pos[0], fake.car.pos[1], fake.car.heading = st[0], st[1], st[4]
        obs[0], obs[3] = st[5] / MAX_SPEED, st[7]
        ci = _near_index(fake, ci)
        act = base_action(obs, fake, ci)
    return horizon


def _safe_action(ta, base):
    c = ta.car
    st = [float(c.pos[0]), float(c.pos[1]), float(c.vel[0]), float(c.vel[1]), float(c.heading),
          float(c.speed), float(c.steering), float(c.angular_velocity)]
    H = SAFE_HORIZON
    base_k = _rollout(list(st), base, ta, H)
    if base_k >= H:
        return base
    bs = _ACTS[base]
    cands = sorted((a for a in _ACTS if a != base),
                   key=lambda a: 2 * abs(_ACTS[a][0] - bs[0]) + abs(_ACTS[a][1] - bs[1]) + abs(_ACTS[a][2] - bs[2]))
    best, best_k = base, base_k
    for a in cands:
        k = _rollout(list(st), a, ta, H)
        if k >= H:
            return a
        if k > best_k:
            best, best_k = a, k
    return best


def heuristic_action(obs, ta=None):
    a = base_action(obs, ta)
    if SAFE_HORIZON and ta is not None and hasattr(ta.car, "steering"):
        a = _safe_action(ta, a)
    return a


def base_action(obs, ta=None, ci=None):
    """Action discrète à partir de l'observation brute (et, si fourni, de la piste via `ta`)."""
    speed_n, tgt_x, tgt_y = float(obs[0]), float(obs[6]), float(obs[7])
    lidar_front = float(obs[11])
    if ta is not None:
        if ci is None:
            ci = closest_index(ta)
        err = lookahead_error(ta, speed_n, ci)
    else:
        err = math.atan2(tgt_y, tgt_x)  # >0 : cible à droite (cap à augmenter)
    # anticipation : la vitesse angulaire met ~20 images à s'éteindre (inertie de la direction)
    err -= PREDICT_FRAMES * float(obs[3])
    a = abs(err)
    # vitesse visée : décroît avec l'erreur d'angle et la proximité d'un mur devant
    v_target = MAX_V_N - (MAX_V_N - CORNER_V_N) * min(1.0, a / 0.8)
    if ta is not None:
        v_target = float(_limit_table(ta)[ci])
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
