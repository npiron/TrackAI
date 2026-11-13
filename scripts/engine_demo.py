"""Démo du son moteur, sans fenêtre : une séquence de conduite simulée avec la vraie physique, enregistrée en WAV.

Usage : .venv/bin/python scripts/engine_demo.py [--engine v10|electric|both] [--out-dir data/audio]
La voiture se promène de gauche à droite dans l'image stéréo (comme à l'écran). Séquence : ralenti et coups de gaz, départ plein gaz jusqu'à la vitesse max, lâcher de gaz (détonations),
gros freinage (rétrogradages), relance, puis virage serré en glisse.
"""
import argparse
import math
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.core.constants import FPS, MAX_SPEED  # noqa: E402
from src.game.audio import SR, CarAudio  # noqa: E402
from src.game.physics import drive  # noqa: E402

# (durée en s, volant, gaz, frein)
SCRIPT = [(1.0, 0, 0, 0), (0.25, 0, 1, 0), (0.4, 0, 0, 0), (0.25, 0, 1, 0), (0.5, 0, 0, 0),
          (9.0, 0, 1, 0), (1.6, 0, 0, 0), (1.4, 0, 0, 1), (4.0, 0, 1, 0), (1.5, 1, 0, 1), (1.5, 0.5, 1, 0),
          (1.0, 0, 0, 0)]


def render(engine):
    audio = CarAudio(engine=engine, offline=True)
    vel, heading, steering, av, drifting = np.zeros(2), 0.0, 0.0, 0.0, False
    frames = [f for dur, *ctl in SCRIPT for f in [ctl] * int(dur * FPS)]
    per_chunk = int(round(CarAudio.CHUNK * FPS))
    out = []
    for i in range(0, len(frames), per_chunk):
        pan = math.sin(2 * math.pi * i / FPS / 8.0)   # la voiture traverse l'écran de gauche à droite et revient
        for st, gas, brk in frames[i:i + per_chunk]:
            vel, heading, steering, av, drifting = drive(vel, heading, steering, av, drifting, st, gas, brk)
            v = math.hypot(*vel)
            slip = 0.0
            if v > 1.0:
                slip = abs(math.degrees((math.atan2(vel[1], vel[0]) - heading + math.pi) % (2 * math.pi) - math.pi))
            audio.update(v / MAX_SPEED, gas > 0, slip, drifting, brk > 0 and v > 0.5, pan=pan)
        out.append(audio.render())
    return np.concatenate(out)


def save(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--engine", default="both", choices=("v10", "electric", "both"))
    p.add_argument("--out-dir", default="data/audio")
    a = p.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    for eng in (("v10", "electric") if a.engine == "both" else (a.engine,)):
        x = render(eng)
        path = os.path.join(a.out_dir, f"engine_{eng}.wav")
        save(path, x)
        print(f"{path} : {len(x) / SR:.1f} s, crête {np.max(np.abs(x)):.2f}, RMS {np.sqrt(np.mean(x ** 2)):.3f}")


if __name__ == "__main__":
    main()
