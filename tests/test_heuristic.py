import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from scripts.heuristic_lap import heuristic_action
from scripts.eval import run_eval


def test_heuristic_action_valid_range():
    import numpy as np
    obs = np.zeros(14, dtype=np.float32)
    obs[6], obs[7] = 1.0, 0.5  # cible à droite, vitesse nulle -> accélère en tournant à droite
    assert heuristic_action(obs) == 6
    obs[7] = -0.5
    assert heuristic_action(obs) == 5


def test_heuristic_finishes_three_laps_static():
    r = run_eval("heuristic", 1, 0, procedural=False, laps_n=3)
    assert r["finish_rate"] == 1.0 and r["mean_laps_done"] == 3.0
