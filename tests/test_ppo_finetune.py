import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pytest

BEST = "data/models/best/best.zip"


def _tiny_v2_model(tmp_path):
    from scripts import imitate
    out = str(tmp_path / "init")
    imitate.main(["--obs-version", "2", "--episodes", "2", "--epochs", "1", "--static", "--out", out])
    return out + ".zip"


def test_finetune_smoke_and_aux_coef(tmp_path):
    from scripts import ppo_finetune
    init = _tiny_v2_model(tmp_path)  # indépendant des modèles sauvés (la taille d'observation évolue)
    out = str(tmp_path / "ft")
    model = ppo_finetune.main(["--init", init, "--timesteps", "1000", "--n-envs", "1", "--aux-episodes", "2",
                               "--laps", "1", "--out", out])
    assert os.path.exists(out + ".zip") and os.path.exists(out + "_vecnormalize.pkl")
    assert model.aux_coef_hist[0] > 0  # coef0 = 1 : non nul au début, décroissant
    out0 = str(tmp_path / "ft0")
    model0 = ppo_finetune.main(["--init", init, "--timesteps", "1000", "--n-envs", "1", "--aux-episodes", "2",
                                "--laps", "1", "--aux-coef0", "0", "--out", out0])
    assert model0.aux_coef_hist and all(c == 0.0 for c in model0.aux_coef_hist)


def test_mix_env_alternates_and_avoids_bench():
    from scripts.ppo_finetune import _make_env_class
    env = _make_env_class()(rank=0, seed=0, laps=1)
    kinds = []
    for _ in range(6):
        env.reset()
        kinds.append((env.ta.procedural, env.ta.track.seed if env.ta.procedural else None))
    for k, (proc, s) in enumerate(kinds):
        assert proc == (k % 2 == 1)
        if proc:
            assert s >= 1000
