"""Multi-lap mode (laps) of TimeAttackEnv and GymTimeAttack."""
import hashlib

import numpy as np

from src.game.env import TimeAttackEnv
from src.game.track import build_track
from src.core.constants import FPS
from src.utils.math_utils import vec


def _teleport_lap(env):
    """Replay one lap by teleporting the (static) car on each checkpoint then the finish."""
    done = False
    for cx, cy, _ in env.track.checkpoints:
        env.car.pos = vec(cx, cy)
        _, _, done, _ = env.step((0.0, 0.0, 0.0))
    fx, fy = env.track.finish_pos[:2]
    env.car.pos = vec(fx, fy)
    return env.step((0.0, 0.0, 0.0))


def test_laps1_same_as_default_and_single_finish():
    a = TimeAttackEnv(build_track(), procedural=False)
    b = TimeAttackEnv(build_track(), procedural=False, laps=1)
    a.reset(); b.reset()
    rng = np.random.default_rng(0)
    for _ in range(300):
        act = (float(rng.uniform(-1, 1)), float(rng.uniform(0, 1)), 0.0)
        oa, ra, da, _ = a.step(act)
        ob, rb, db, _ = b.step(act)
        assert np.array_equal(oa, ob) and ra == rb and da == db
    a.reset()
    _, r, done, _ = _teleport_lap(a)
    assert done and r == 100.0 and a.lap_count == 1 and len(a.lap_times) == 1


def test_laps3_teleport_gives_3_lap_times():
    env = TimeAttackEnv(build_track(), procedural=False, laps=3)
    env.reset()
    n = len(env.track.checkpoints)
    for lap in range(3):
        _, _, done, _ = _teleport_lap(env)
        assert done == (lap == 2)
        assert env.lap_count == lap + 1
        if lap < 2:
            assert not any(env.cp_visited)
    assert len(env.lap_times) == 3
    assert abs(sum(env.lap_times) - env.t) < 1e-9
    assert all(abs(t - (n + 1) / FPS) < 1e-9 for t in env.lap_times)


def test_gym_wrapper_laps_info():
    from src.rl.wrappers import GymTimeAttack
    g = GymTimeAttack(render_mode=None, procedural=False, laps=3)
    g.reset()
    for lap in range(3):
        _, _, term, _, info = None, None, False, None, {}
        for cx, cy, _ in g.ta.track.checkpoints:
            g.ta.car.pos = vec(cx, cy)
            _, _, term, _, info = g.step(0)
        g.ta.car.pos = vec(*g.ta.track.finish_pos[:2])
        _, _, term, _, info = g.step(0)
        assert term == (lap == 2)
        assert info["laps_done"] == lap + 1
    assert info["is_success"] is True
    assert len(info["lap_times"]) == 3
    assert abs(info["total_time"] - sum(info["lap_times"])) < 1e-9


# Hash de la trajectoire (obs, récompense, done) mesuré sur le code d'avant le mode multi-tours
# (commit e32dec6~1) ; le code actuel avec laps omis doit le reproduire.
REF_HASH = "efb6b7436b6f8429fae500076aa20f1b595c80710b28df4a9b4c6ebece52826e"


def _traj_hash(**kw):
    env = TimeAttackEnv(build_track(), procedural=False, **kw)
    env.reset()
    rng = np.random.default_rng(0)
    h = hashlib.sha256()
    for _ in range(600):
        act = (float(rng.uniform(-1, 1)), float(rng.uniform(0, 1)), 0.0)
        o, r, d, _ = env.step(act)
        h.update(np.asarray(o, dtype=np.float64).tobytes())
        h.update(repr(float(r)).encode())
        h.update(bytes([d]))
        if d:
            break
    return h.hexdigest()


def test_default_and_laps1_match_pre_multilap_reference():
    assert _traj_hash() == REF_HASH
    assert _traj_hash(laps=1) == REF_HASH


def test_laps3_needs_ordered_checkpoints():
    env = TimeAttackEnv(build_track(), procedural=False, laps=3)
    env.reset()
    fx, fy = env.track.finish_pos[:2]
    env.car.pos = vec(fx, fy)  # arrivée sans checkpoints : ne compte pas
    _, _, done, _ = env.step((0.0, 0.0, 0.0))
    assert not done and env.lap_count == 0


def test_wall_hits_counted_without_changing_physics():
    env = TimeAttackEnv(build_track(), procedural=False)
    env.reset()
    assert env.wall_hits == 0 and env.wall_contacts == 0
    # plein gaz, sans braquer : la voiture finit dans un mur
    for _ in range(600):
        env.step((0.0, 1.0, 0.0))
    assert env.wall_hits > 0
    assert 1 <= env.wall_contacts <= env.wall_hits
    env.reset()
    assert env.wall_hits == 0 and env.wall_contacts == 0


def test_wrapper_info_has_wall_counters():
    from src.rl.wrappers import GymTimeAttack
    env = GymTimeAttack(render_mode=None, procedural=False)
    env.reset()
    for _ in range(600):
        _, _, term, trunc, info = env.step(1)
        if term or trunc:
            break
    assert info["wall_hits"] > 0 and info["wall_contacts"] >= 1
