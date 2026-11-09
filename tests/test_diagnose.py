import numpy as np
from scripts.diagnose import add_components, summarize_episode, COMPONENTS
from src.rl.wrappers import GymTimeAttack


def test_summarize():
    acc = add_components({}, {"progress": 1.5, "env": 100.0})
    acc = add_components(acc, {"progress": -0.5, "alignment": -2.0})
    assert acc["progress"] == 1.0 and acc["alignment"] == -2.0
    s = summarize_episode([0.0, 0.5, 5.0, 10.0], [(0, 0), (3, 4)], 2, acc,
                          {"end_cause": "timeout", "laps_done": 0})
    assert s["stopped_frames"] == 2 and s["end_cause"] == "timeout"
    assert s["mean_speed"] == 3.875 and s["final_pos"] == [3.0, 4.0]
    assert s["reward_total"] == 99.0


def test_components_sum_to_reward():
    env = GymTimeAttack(procedural=False, reward_mode="legacy")
    env.reset()
    for a in [1, 5, 6, 1, 3, 0, 2, 4] * 10:
        _, r, term, _, info = env.step(a)
        if "reward_components" not in info:
            break
        assert set(info["reward_components"]) == set(COMPONENTS)
        assert abs(sum(info["reward_components"].values()) - r) < 1e-4
