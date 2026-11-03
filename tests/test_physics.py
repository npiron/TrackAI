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
