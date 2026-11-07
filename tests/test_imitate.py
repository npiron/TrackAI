import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy as np
from scripts.imitate import collect


def test_collect_labels_and_shape():
    O, A = collect(2, 1, False, seed=0, eps_levels=(0.0, 0.3), max_steps=50)
    assert O.shape == (100, 14) and A.shape == (100,)
    assert A.min() >= 0 and A.max() <= 8


def test_collect_with_policy_labels_from_heuristic():
    O, A = collect(1, 1, False, seed=0, eps_levels=(0.0,), max_steps=30, policy=lambda o: 0)
    assert O.shape == (30, 14) and A.max() <= 8


def test_collect_v2_shape():
    from src.game.env import TimeAttackEnv
    O, A = collect(1, 1, False, seed=0, eps_levels=(0.0,), max_steps=20, env_kw={"obs_version": 2})
    assert O.shape == (20, TimeAttackEnv.OBS_V2_SIZE) and A.shape == (20,)


def test_mini_bc_v2_then_eval(tmp_path):
    from scripts import imitate, eval as ev, robust_eval
    out = str(tmp_path / "m")
    imitate.main(["--obs-version", "2", "--episodes", "2", "--epochs", "1", "--static", "--out", out])
    assert os.path.exists(out + ".zip")
    m = str(tmp_path / "m.json")
    e = ev.main(["--model", out + ".zip", "--episodes", "1", "--static", "--metrics", m])
    assert "mean_return" in e
    r = robust_eval.run(out + ".zip", 1, 0, 0.0, 1, False)
    assert "finish_rate" in r
    e = ev.main(["--model", "heuristic", "--episodes", "1", "--static", "--obs-version", "2", "--metrics", m])
    assert "mean_return" in e
