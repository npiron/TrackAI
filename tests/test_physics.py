import math

import numpy as np

from scripts.physics_check import measure
from src.core.constants import MAX_SPEED


def test_longitudinal_deterministic_and_sane():
    a, b = measure(), measure()
    assert a == b
    assert 0 < a["terminal_speed_px_frame"] <= MAX_SPEED * 1.2
    assert a["brake_distance_px"] > 0
    assert a["coast_decel_px_frame2"] > 0


def test_turn_and_out_of_range_deterministic():
    a, b = measure(), measure()
    assert a["turn"] == b["turn"]
    assert a["out_of_range_actions"] == b["out_of_range_actions"]
    assert a["turn"]["radius_increases_with_speed"]
    assert a["out_of_range_actions"]["all_finite"]


def test_world_scenarios_deterministic():
    from scripts.physics_check import measure_world
    a, b = measure_world(), measure_world()
    assert a == b
    assert a["checkpoints"]["pass"] and a["reproducibility"]["pass"]
    assert a["walls"]["perpendicular"]["pass_inside"]


def test_step_clips_actions():
    from scripts.physics_check import measure_out_of_range
    r = measure_out_of_range()
    assert r["all_finite"]
    from src.game.env import TimeAttackEnv
    env = TimeAttackEnv()
    env.reset()
    env.step((5.0, 3.0, -2.0))
    assert abs(env.car.steering) <= 1.0


def test_speed_resynced_after_wall_hit():
    from scripts.physics_check import _wall_run
    for off in (0.0, math.pi / 4):
        r = _wall_run(off)
        assert r["contact_seen"]
        assert r["max_speed_vel_mismatch"] <= 0.25
        assert r["frames_outside_track"] == 0


def test_terminal_speed_reaches_max_speed():
    from scripts.physics_check import measure
    a = measure()
    assert a["terminal_reaches_max"]["pass"]
    assert a["terminal_speed_px_frame"] <= MAX_SPEED * 1.0 + 1e-6


# --- Physique façon Trackmania (rotation par le roulement, marche arrière, drift, murs) ---

def _free():
    from scripts.physics_check import _free_env
    e = _free_env()
    e.reset()
    return e


def test_no_rotation_when_stopped():
    e = _free()
    h0 = e.car.heading
    for _ in range(50):
        e.step((1.0, 0.0, 0.0))
    assert e.car.heading == h0          # la voiture ne pivote pas sur place
    assert e.car.steering == 1.0        # mais les roues sont braquées


def test_brake_when_stopped_reverses():
    e = _free()
    for _ in range(100):
        e.step((0.0, 0.0, 1.0))
    from src.core.constants import REVERSE_MAX
    assert -REVERSE_MAX - 1e-6 <= e.car.speed < -3.0


def test_rotation_grows_with_speed_then_steering_softens():
    def yaw(v):
        e = _free()
        while e.car.speed < v:
            e.step((0.0, 1.0, 0.0))
        for _ in range(100):
            e.step((1.0, 1.0 if e.car.speed < v else 0.0, 0.0))
        h = e.car.heading
        e.step((1.0, 1.0 if e.car.speed < v else 0.0, 0.0))
        return (e.car.heading - h), e.car.speed
    (w_slow, v_slow), (w_fast, v_fast) = yaw(3.0), yaw(22.0)
    assert 0 < w_slow
    assert v_fast / w_fast > 2 * v_slow / w_slow   # rayon bien plus grand à haute vitesse


def test_brake_while_steering_starts_drift():
    e = _free()
    while e.car.speed < 20:
        e.step((0.0, 1.0, 0.0))
    for _ in range(10):
        e.step((1.0, 1.0, 0.0))
    assert not e.car.is_drifting
    for _ in range(3):
        e.step((1.0, 0.0, 1.0))
    assert e.car.is_drifting
    for _ in range(20):
        e.step((0.0, 1.0, 0.0))
    assert not e.car.is_drifting       # volant droit : le drift s'arrête


def test_grazing_wall_keeps_more_speed_than_head_on():
    from src.game.env import TimeAttackEnv
    from src.game.track import build_track

    def after_hit(off):
        e = TimeAttackEnv(build_track(), procedural=False)
        e.reset()
        tan, _ = e.track.get_closest_track_info(e.car.pos)
        e.car.heading = math.atan2(tan[1], tan[0]) + off
        e.car.vel = 15 * np.array([math.cos(e.car.heading), math.sin(e.car.heading)])
        for _ in range(80):
            e.step((0.0, 0.0, 0.0))
            if e.wall_hits:
                return float(np.linalg.norm(e.car.vel))
        raise AssertionError("pas de contact")
    assert after_hit(0.15) > 2 * after_hit(1.4)


# --- Circuits longs (variante 2) ---

def test_long_tracks_are_valid_and_longer():
    from src.game.track import _track_ok, build_track, generate_procedural_track, V2_HALF_WIDTH
    v1 = np.asarray(build_track().spline_points)
    l1 = np.linalg.norm(np.diff(v1, axis=0), axis=1).sum()
    lens = []
    for seed in range(5):
        t = generate_procedural_track(seed, variant=2)
        assert t.half_width == V2_HALF_WIDTH
        assert _track_ok(t.spline_points, min_radius=78, half_width=V2_HALF_WIDTH)
        assert t.collision_mask.get_at(tuple(int(v) for v in t.start_pos)) == 1
        a = np.asarray(t.spline_points)
        lens.append(np.linalg.norm(np.diff(a, axis=0), axis=1).sum())
    assert np.mean(lens) > 1.2 * l1
    a = generate_procedural_track(7, variant=2).spline_points
    b = generate_procedural_track(7, variant=2).spline_points
    assert np.array_equal(a, b)  # même graine, même circuit


def test_variant_1_unchanged_by_default():
    from src.game.env import TimeAttackEnv
    e = TimeAttackEnv(procedural=True)
    e.reset(track_seed=3)
    assert e.track.half_width == 60.0
