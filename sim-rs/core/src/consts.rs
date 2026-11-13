//! Constantes du jeu (miroir de src/core/constants.py).
pub const W: i32 = 1400;
pub const H: i32 = 1000;
pub const FPS: f64 = 50.0;

pub const MAX_SPEED: f64 = 13.7;
pub const ACCEL: f64 = 0.137;
pub const BRAKE: f64 = 0.16;
pub const FRICTION: f64 = 0.9899;
pub const COAST_FRICTION: f64 = 0.985;
pub const TURN_SPEED: f64 = 0.14;
pub const LATERAL_GRIP: f64 = 0.6;

pub const STEER_SPEED: f64 = 0.15;
pub const STEER_CURVATURE: f64 = 0.016;
pub const STEER_SPEED_SENS: f64 = 0.4;
pub const YAW_RESPONSE: f64 = 0.35;

pub const REVERSE_ACCEL: f64 = 0.08;
pub const REVERSE_MAX: f64 = 3.5;

pub const DRIFT_GRIP: f64 = 0.08;
pub const DRIFT_MIN_SPEED: f64 = 8.0;
pub const DRIFT_YAW_BOOST: f64 = 1.3;
pub const DRIFT_TURN_SPEED: f64 = 0.165;
pub const DRIFT_MAX_SLIP: f64 = 0.3;
pub const DRIFT_RECOVER_GRIP: f64 = 0.3;
pub const DRIFT_EXIT_SLIP: f64 = 0.1;
pub const DRIFT_SCRUB: f64 = 0.0025;
pub const DRIFT_STEER_IN: f64 = 0.5;
pub const DRIFT_STEER_OUT: f64 = 0.15;
pub const DRIFT_AUTO_STEER: f64 = 0.98;
pub const DRIFT_AUTO_SPEED: f64 = 0.95;

pub const BOT_DECISION_FRAMES: usize = 2;

pub const WALL_HIT_LOSS: f64 = 0.25;
pub const WALL_RUB_LOSS: f64 = 0.06;
pub const WALL_CONTACT_GAP: i64 = 10;
pub const WALL_IMPACT_LOSS: f64 = 0.85;
pub const WALL_BOUNCE: f64 = 0.15;
pub const WALL_ALIGN: f64 = 0.5;

pub const CHECKPOINT_RADIUS: f64 = 100.0;
pub const CAR_NOSE: f64 = 20.0;
pub const FINISH_RADIUS: f64 = 100.0;

pub const PI: f64 = std::f64::consts::PI;
