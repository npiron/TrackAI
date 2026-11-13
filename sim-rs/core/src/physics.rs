//! Dynamique de la voiture (miroir de src/game/physics.py, fonction `drive`).
use crate::consts::*;
use crate::pymath::{cos, hypot, pymod, sin};

#[derive(Clone, Copy, Debug, Default)]
pub struct DriveState {
    pub vel: [f64; 2],
    pub heading: f64,
    pub steering: f64,
    pub angular_velocity: f64,
    pub drifting: bool,
}

/// Un pas de 1/FPS.
pub fn drive(s: DriveState, steer: f64, accel: f64, brake: f64) -> DriveState {
    let DriveState { vel, mut heading, mut steering, mut angular_velocity, mut drifting } = s;
    let (c, sn) = (cos(heading), sin(heading));
    let (vx, vy) = (vel[0], vel[1]);
    let mut v_long = vx * c + vy * sn;
    let v_lat = -vx * sn + vy * c;

    // 1. Longitudinal
    let mut reversing = false;
    if accel > 0.0 {
        v_long += accel * (if v_long >= 0.0 { ACCEL } else { BRAKE });
    }
    if brake > 0.0 {
        if v_long > 0.3 {
            v_long = f64::max(0.0, v_long - brake * BRAKE);
        } else if accel == 0.0 {
            reversing = true;
            v_long = f64::max(-REVERSE_MAX, v_long - brake * REVERSE_ACCEL);
        }
    }
    v_long *= if accel > 0.0 || reversing { FRICTION } else { COAST_FRICTION };
    if v_long.abs() < 0.01 && accel == 0.0 && !reversing {
        v_long = 0.0;
    }
    v_long = f64::min(v_long, MAX_SPEED);

    // 2. Volant
    if steer > steering {
        steering = f64::min(steer, steering + STEER_SPEED);
    } else if steer < steering {
        steering = f64::max(steer, steering - STEER_SPEED);
    }

    // 3. Entrée en drift
    let mut speed = hypot(v_long, v_lat);
    if !drifting
        && v_long > DRIFT_MIN_SPEED
        && ((brake > 0.0 && steering.abs() > DRIFT_STEER_IN)
            || (steering.abs() > DRIFT_AUTO_STEER && v_long > DRIFT_AUTO_SPEED * MAX_SPEED))
    {
        drifting = true;
    }

    // 4. Rotation : modèle bicyclette
    let sens = 1.0 - STEER_SPEED_SENS * f64::min(v_long.abs() / MAX_SPEED, 1.0);
    let mut target_av = v_long * steering * STEER_CURVATURE * sens;
    let mut cap = TURN_SPEED;
    if drifting {
        target_av *= DRIFT_YAW_BOOST;
        cap = DRIFT_TURN_SPEED;
    }
    target_av = f64::max(-cap, f64::min(cap, target_av));
    angular_velocity += (target_av - angular_velocity) * YAW_RESPONSE;
    heading += angular_velocity;

    // 5. Adhérence
    let new_vel;
    if speed > 1e-6 {
        let r#ref = if v_long < 0.0 { PI } else { 0.0 };
        let mut slip = v_lat.atan2(v_long) - r#ref - angular_velocity;
        slip = pymod(slip + PI, 2.0 * PI) - PI;
        if drifting {
            let countersteer = steering * slip > 0.0 && steering.abs() > DRIFT_STEER_OUT;
            let holding = steering.abs() >= DRIFT_STEER_OUT && !countersteer;
            slip *= 1.0 - (if holding { DRIFT_GRIP } else { DRIFT_RECOVER_GRIP });
            slip = f64::max(-DRIFT_MAX_SLIP, f64::min(DRIFT_MAX_SLIP, slip));
            speed *= 1.0 - DRIFT_SCRUB * slip.abs();
            if (!holding && slip.abs() < DRIFT_EXIT_SLIP) || speed < DRIFT_MIN_SPEED * 0.5 {
                drifting = false;
            }
        } else {
            slip *= 1.0 - LATERAL_GRIP;
        }
        let d = heading + r#ref + slip;
        new_vel = [speed * cos(d), speed * sin(d)];
    } else {
        new_vel = [0.0, 0.0];
        drifting = false;
    }
    DriveState { vel: new_vel, heading, steering, angular_velocity, drifting }
}
