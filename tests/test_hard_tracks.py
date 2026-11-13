import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from scripts.hard_tracks import difficulty_key, split_hard
from src.rl.wrappers import GymTimeAttack


def _env(**kw):
    return GymTimeAttack(render_mode=None, procedural=True, obs_version=3, track_variant=2, action_set=2, **kw)


def _seeds_drawn(env, n, seed=0):
    out = []
    for k in range(n):
        env.reset(seed=seed if k == 0 else None)
        out.append(env.ta.track.seed)
    return out


def test_track_seeds_toujours_dans_la_liste():
    env = _env(track_seeds=[3, 11], track_mix=1.0)
    assert set(_seeds_drawn(env, 6)) <= {3, 11}


def test_track_mix_melange_liste_et_aleatoire():
    env = _env(track_seeds=[3], track_mix=0.5)
    drawn = _seeds_drawn(env, 20)
    assert 3 in drawn and any(s != 3 for s in drawn)


def test_tirage_reproductible_avec_la_graine():
    a = _seeds_drawn(_env(track_seeds=[1, 2, 3, 4], track_mix=1.0), 5, seed=42)
    b = _seeds_drawn(_env(track_seeds=[1, 2, 3, 4], track_mix=1.0), 5, seed=42)
    assert a == b


def test_option_track_seed_prioritaire():
    env = _env(track_seeds=[3], track_mix=1.0)
    env.reset(options={"track_seed": 9})
    assert env.ta.track.seed == 9


def test_tri_et_coupe_train_val():
    rows = [
        {"seed": 0, "finished": True, "hits": 0, "hits_per_lap": 0.0, "speed": 0.9},
        {"seed": 1, "finished": True, "hits": 2, "hits_per_lap": 0.4, "speed": 0.8},
        {"seed": 2, "finished": False, "hits": 1, "hits_per_lap": 0.5, "speed": 0.0},
        {"seed": 3, "finished": True, "hits": 5, "hits_per_lap": 1.0, "speed": 0.85},
        {"seed": 4, "finished": True, "hits": 1, "hits_per_lap": 0.2, "speed": 0.7},
    ]
    rows.sort(key=difficulty_key)
    assert [r["seed"] for r in rows] == [2, 3, 1, 4, 0]
    assert split_hard(rows, top=10) == {"train": [2, 1], "val": [3, 4]}
    assert split_hard(rows, top=2) == {"train": [2], "val": [3]}
