"""Exporte la politique d'un modèle PPO (+ sa normalisation d'observations) en JSON pour le viewer Rust.

Usage : .venv/bin/python scripts/export_policy.py data/checkpoints/f1_durs/gen_003.zip sortie.json
Le réseau exporté est la tête « politique » : obs normalisée -> Linear+tanh -> Linear+tanh -> logits (argmax = action).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def export(model_path, out_path):
    from scripts.eval import _load_model, detect_action_set, detect_obs_version
    model, vn = _load_model(model_path)
    sd = model.policy.state_dict()
    layers = []
    names = sorted({k.rsplit(".", 1)[0] for k in sd if k.startswith("mlp_extractor.policy_net.")},
                   key=lambda s: int(s.rsplit(".", 1)[1]))
    for name in names + ["action_net"]:
        w, b = sd[name + ".weight"].cpu().numpy(), sd[name + ".bias"].cpu().numpy()
        layers.append({"out": int(w.shape[0]), "in": int(w.shape[1]), "w": w.reshape(-1).tolist(), "b": b.tolist()})
    act = type(model.policy.activation_fn()).__name__.lower()
    data = {
        "obs_version": detect_obs_version(model),
        "action_set": detect_action_set(model),
        "activation": act,
        "layers": layers,
        "obs_mean": vn.obs_rms.mean.tolist() if vn is not None else None,
        "obs_var": vn.obs_rms.var.tolist() if vn is not None else None,
        "clip_obs": float(vn.clip_obs) if vn is not None else 10.0,
        "epsilon": float(vn.epsilon) if vn is not None else 1e-8,
        "source": os.path.abspath(model_path),
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, out_path)


if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
