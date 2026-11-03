"""T18 : chrono humain identique au chrono du banc (1/FPS par frame)."""
import json

import pytest

from scripts import human_lap
from src.core.constants import FPS
from src.game.env import TimeAttackEnv
from src.rl.wrappers import GymTimeAttack


def _finish_every(monkeypatch, n):
    """Force un passage de ligne d'arrivée valide tous les n steps (pas de conduite scriptée nécessaire)."""
    state = {"c": 0}
    orig_reset = TimeAttackEnv.reset

    def reset(self):
        state["c"] = 0
        return orig_reset(self)

    def check(self):
        state["c"] += 1
        return state["c"] % n == 0

    monkeypatch.setattr(TimeAttackEnv, "reset", reset)
    monkeypatch.setattr(TimeAttackEnv, "_check_finish", check)


def test_replay_total_matches_bench_clock(monkeypatch):
    _finish_every(monkeypatch, 40)
    ok, total, laps = human_lap.replay([(0.0, 1.0, 0.0)] * 200, laps=3)
    assert ok and len(laps) == 3
    assert total == pytest.approx(120 / FPS)
    env = GymTimeAttack(render_mode=None, procedural=False, laps=3)
    env.reset()
    info = {}
    for _ in range(120):
        _, _, term, trunc, info = env.step(0)
        if term or trunc:
            break
    assert info["total_time"] == pytest.approx(total)
    assert info["lap_times"] == pytest.approx(laps)


def test_replay_unfinished():
    ok, total, laps = human_lap.replay([(0.0, 1.0, 0.0)] * 10, laps=3)
    assert not ok and total is None


def test_record_and_load(tmp_path):
    p = str(tmp_path / "hb.json")
    assert human_lap.load_best(p) is None
    assert human_lap.record(30.0, [10.0] * 3, 3, p)
    assert not human_lap.record(31.0, [10.5] * 3, 3, p)
    assert human_lap.record(29.0, [9.7] * 3, 3, p)
    assert human_lap.load_best(p) == 29.0
