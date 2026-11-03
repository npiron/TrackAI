from scripts.physics_check import measure
from src.core.constants import MAX_SPEED


def test_longitudinal_deterministic_and_sane():
    a, b = measure(), measure()
    assert a == b
    assert 0 < a["terminal_speed_px_frame"] <= MAX_SPEED * 1.2
    assert a["brake_distance_px"] > 0
    assert a["coast_decel_px_frame2"] > 0
