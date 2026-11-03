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
