"""Dynamique de la voiture, inspirée de Trackmania (sans murs, boost ni checkpoints).

Fonction pure partagée par `TimeAttackEnv.step` et le simulateur du pilote programmé
(`scripts/heuristic_lap.py`), pour qu'ils ne divergent jamais.

- Rotation par le roulement (modèle bicyclette) : nulle à l'arrêt, inversée en marche arrière,
  braquage utile qui baisse avec la vitesse.
- Frein maintenu à l'arrêt : marche arrière.
- Adhérence : les pneus réalignent la vitesse sur le cap sans perdre sa norme.
- Drift : un coup de frein en braquant à vitesse élevée ; l'adhérence chute tant qu'on braque.
"""
import math

import numpy as np

from src.core.constants import (
    ACCEL, BRAKE, COAST_FRICTION, DRIFT_GRIP, DRIFT_MIN_SPEED, DRIFT_SCRUB, DRIFT_STEER_IN,
    DRIFT_MAX_SLIP, DRIFT_STEER_OUT, DRIFT_YAW_BOOST,
    FRICTION, LATERAL_GRIP, MAX_SPEED, REVERSE_ACCEL, REVERSE_MAX, STEER_CURVATURE,
    STEER_SPEED, STEER_SPEED_SENS, TURN_SPEED, YAW_RESPONSE,
)


def drive(vel, heading, steering, angular_velocity, drifting, steer, accel, brake):
    """Un pas de 1/FPS. Renvoie (vel, heading, steering, angular_velocity, drifting)."""
    c, s = math.cos(heading), math.sin(heading)
    vx, vy = float(vel[0]), float(vel[1])
    v_long = vx * c + vy * s
    v_lat = -vx * s + vy * c

    # 1. Longitudinal : gaz, frein, marche arrière (frein maintenu à l'arrêt)
    reversing = False
    if accel > 0:
        v_long += accel * (ACCEL if v_long >= 0 else BRAKE)
    if brake > 0:
        if v_long > 0.3:
            v_long = max(0.0, v_long - brake * BRAKE)
        elif accel == 0:
            reversing = True
            v_long = max(-REVERSE_MAX, v_long - brake * REVERSE_ACCEL)
    v_long *= FRICTION if (accel > 0 or reversing) else COAST_FRICTION
    if abs(v_long) < 0.01 and accel == 0 and not reversing:
        v_long = 0.0
    v_long = min(v_long, MAX_SPEED)

    # 2. Volant : il monte progressivement, même à l'arrêt (les roues tournent)
    if steer > steering:
        steering = min(steer, steering + STEER_SPEED)
    elif steer < steering:
        steering = max(steer, steering - STEER_SPEED)

    # 3. Drift
    speed = math.hypot(v_long, v_lat)
    if brake > 0 and abs(steering) > DRIFT_STEER_IN and v_long > DRIFT_MIN_SPEED:
        drifting = True
    elif drifting and (abs(steering) < DRIFT_STEER_OUT or speed < DRIFT_MIN_SPEED * 0.5):
        drifting = False

    # 4. Rotation : modèle bicyclette
    sens = 1.0 - STEER_SPEED_SENS * min(abs(v_long) / MAX_SPEED, 1.0)
    target_av = v_long * steering * STEER_CURVATURE * sens
    if drifting:
        target_av *= DRIFT_YAW_BOOST
    target_av = max(-TURN_SPEED, min(TURN_SPEED, target_av))
    angular_velocity += (target_av - angular_velocity) * YAW_RESPONSE
    heading += angular_velocity

    # 5. Adhérence
    if speed > 1e-6:
        ref = math.pi if v_long < 0 else 0.0
        slip = math.atan2(v_lat, v_long) - ref - angular_velocity
        slip = (slip + math.pi) % (2 * math.pi) - math.pi
        grip = DRIFT_GRIP if drifting and abs(slip) < DRIFT_MAX_SLIP else LATERAL_GRIP
        slip *= 1.0 - grip
        if drifting:
            speed *= 1.0 - DRIFT_SCRUB * abs(slip)
        d = heading + ref + slip
        new_vel = np.array([speed * math.cos(d), speed * math.sin(d)])
    else:
        new_vel = np.zeros(2)
    return new_vel, heading, steering, angular_velocity, drifting
