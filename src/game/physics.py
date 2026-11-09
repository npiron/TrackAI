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
    ACCEL, BRAKE, COAST_FRICTION, DRIFT_GRIP, DRIFT_MIN_SPEED, DRIFT_SCRUB, DRIFT_STEER_IN, DRIFT_TURN_SPEED, DRIFT_AUTO_STEER, DRIFT_AUTO_SPEED,
    DRIFT_RECOVER_GRIP, DRIFT_EXIT_SLIP,
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

    # 3. Drift : entrée (coup de frein en braquant, ou gros coup de volant à haute vitesse).
    #    La sortie se décide après l'adhérence (étape 5) : le drift tient tant que la voiture est en travers.
    speed = math.hypot(v_long, v_lat)
    if not drifting and v_long > DRIFT_MIN_SPEED and (
            (brake > 0 and abs(steering) > DRIFT_STEER_IN)
            or (abs(steering) > DRIFT_AUTO_STEER and v_long > DRIFT_AUTO_SPEED * MAX_SPEED)):
        drifting = True

    # 4. Rotation : modèle bicyclette
    sens = 1.0 - STEER_SPEED_SENS * min(abs(v_long) / MAX_SPEED, 1.0)
    target_av = v_long * steering * STEER_CURVATURE * sens
    cap = TURN_SPEED
    if drifting:
        target_av *= DRIFT_YAW_BOOST
        cap = DRIFT_TURN_SPEED
    target_av = max(-cap, min(cap, target_av))
    angular_velocity += (target_av - angular_velocity) * YAW_RESPONSE
    heading += angular_velocity

    # 5. Adhérence. En drift, l'arrière glisse : l'angle entre la vitesse et le cap se creuse tant qu'on
    #    braque, plafonné en douceur à DRIFT_MAX_SLIP ; volant relâché ou contre-braquage, l'adhérence revient
    #    progressivement et le drift se termine quand la voiture est de nouveau dans l'axe (un arc continu).
    if speed > 1e-6:
        ref = math.pi if v_long < 0 else 0.0
        slip = math.atan2(v_lat, v_long) - ref - angular_velocity
        slip = (slip + math.pi) % (2 * math.pi) - math.pi
        if drifting:
            countersteer = steering * slip > 0 and abs(steering) > DRIFT_STEER_OUT
            holding = abs(steering) >= DRIFT_STEER_OUT and not countersteer
            slip *= 1.0 - (DRIFT_GRIP if holding else DRIFT_RECOVER_GRIP)
            slip = max(-DRIFT_MAX_SLIP, min(DRIFT_MAX_SLIP, slip))
            speed *= 1.0 - DRIFT_SCRUB * abs(slip)
            if (not holding and abs(slip) < DRIFT_EXIT_SLIP) or speed < DRIFT_MIN_SPEED * 0.5:
                drifting = False
        else:
            slip *= 1.0 - LATERAL_GRIP
        d = heading + ref + slip
        new_vel = np.array([speed * math.cos(d), speed * math.sin(d)])
    else:
        new_vel = np.zeros(2)
        drifting = False
    return new_vel, heading, steering, angular_velocity, drifting
