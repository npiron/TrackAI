import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest

from scripts.heuristic_lap import heuristic_action
from src.rl.wrappers import GymTimeAttack, SIMPLE_TIME_PENALTY


def test_invalid_reward_mode():
    with pytest.raises(ValueError):
        GymTimeAttack(procedural=False, reward_mode="nope")


def test_simple_lap_sum_and_wall():
    env = GymTimeAttack(procedural=False, laps=1, reward_mode="simple", wall_penalty=-5.0)
    env.reset()
    k_prog = 100.0 / float(env.ta._arc_lengths()[-1])
    length = float(env.ta._arc_lengths()[-1])
    total, steps, done, info = 0.0, 0, False, {}
    while not done and steps < 3000:
        a = heuristic_action(env.ta.obs_v1(), env.ta)
        _, r, done, _, info = env.step(a)
        comp = info["reward_components"]
        assert abs(sum(comp.values()) - r) < 1e-6
        # le bonus de fin de course de l'env (+100) n'est pas de la progression
        total += r - comp["env"]
        steps += 1
    assert info["is_success"] and info["wall_hits"] == 0
    expected = k_prog * length - SIMPLE_TIME_PENALTY * steps
    assert abs(total - expected) <= 0.05 * abs(expected)
    assert 90 < k_prog * length < 110

    # un choc retire exactement |wall_penalty|
    env.reset()
    hits = 0
    for _ in range(400):
        _, r, _, _, info = env.step(5)  # gauche + accélère : finit au mur
        if env.ta.wall_hits > hits:
            comp = info["reward_components"]
            assert comp["wall"] == -5.0
            assert abs(r - (comp["progress"] + comp["time_penalty"] - 5.0)) < 1e-9
            hits = env.ta.wall_hits
            break
    assert hits > 0
