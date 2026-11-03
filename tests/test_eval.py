import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import eval as ev


def test_eval_random_is_reproducible(tmp_path):
    m = str(tmp_path / "m.json")
    a = ev.main(["--model", "random", "--episodes", "2", "--seed", "3", "--metrics", m])
    b = ev.main(["--model", "random", "--episodes", "2", "--seed", "3", "--metrics", m])
    keys = ["mean_return", "mean_checkpoints", "success_rate", "mean_lap_time", "mean_episode_steps"]
    assert {k: a[k] for k in keys} == {k: b[k] for k in keys}
    assert len(json.load(open(m))) == 2
