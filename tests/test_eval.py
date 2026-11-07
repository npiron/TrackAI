import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import eval as ev


def test_eval_random_is_reproducible(tmp_path):
    m = str(tmp_path / "m.json")
    a = ev.main(["--model", "random", "--episodes", "2", "--seed", "3", "--metrics", m])
    b = ev.main(["--model", "random", "--episodes", "2", "--seed", "3", "--metrics", m])
    keys = ["mean_return", "mean_checkpoints", "success_rate", "mean_lap_time", "mean_episode_steps"]
    assert {k: a[k] for k in keys} == {k: b[k] for k in keys}
    assert len(json.load(open(m))) == 2


def test_multi_lap_stats():
    r = ev.multi_lap_stats([True, False, True, False], [3, 1, 3, 2], [30.0, 40.0])
    assert r == {"finish_rate": 0.5, "mean_total_time": 35.0, "best_total_time": 30.0, "mean_laps_done": 2.25}
    r = ev.multi_lap_stats([False], [0], [])
    assert r["mean_total_time"] is None and r["best_total_time"] is None


def test_eval_laps_keys(tmp_path):
    m = str(tmp_path / "m.json")
    a = ev.main(["--model", "random", "--static", "--laps", "3", "--episodes", "1", "--seed", "0", "--metrics", m])
    assert a["laps"] == 3 and "finish_rate" in a and "mean_laps_done" in a


def test_static_flags_parsing(monkeypatch):
    seen = []
    monkeypatch.setattr(ev, "run_eval", lambda *a, **k: seen.append(k["procedural"]) or {})
    monkeypatch.setattr(ev, "append_metrics", lambda *a: None)
    monkeypatch.setattr(ev, "_human_best", lambda: None)
    ev.main(["--model", "random"])
    ev.main(["--model", "random", "--no-static"])
    ev.main(["--model", "random", "--static"])
    assert seen == [True, True, False]
    import pytest
    with pytest.raises(SystemExit):
        ev.main(["--model", "random", "--static", "--no-static"])


def test_default_metrics_in_goal():
    assert ev.DEFAULT_METRICS.endswith(os.path.join(".goal", "metrics.json")) or not os.path.isdir(
        os.path.join(os.path.dirname(ev.DEFAULT_METRICS), ""))


def test_track_seed_fixes_track():
    from src.game.env import TimeAttackEnv
    env = TimeAttackEnv(procedural=True)
    env.reset(track_seed=7)
    t1 = env.track
    env.reset(track_seed=7)
    t2 = env.track
    env.reset(track_seed=8)
    t3 = env.track
    assert t1.seed == t2.seed == 7
    assert np.array_equal(np.asarray(t1.spline_points), np.asarray(t2.spline_points))
    assert t3.seed == 8
    assert not np.array_equal(np.asarray(t1.spline_points), np.asarray(t3.spline_points))


def test_gym_reset_track_seed_option():
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=True)
    env.reset(seed=1, options={"track_seed": 5})
    assert env.ta.track.seed == 5
    env.reset()


def test_bench_incompatible_with_static(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        ev.main(["--model", "random", "--bench", "--static", "--metrics", str(tmp_path / "m.json")])
