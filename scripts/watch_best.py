"""Regarder le meilleur modèle jouer, en temps réel.

Usage : .venv/bin/python scripts/watch_best.py [--model data/models/best/best.zip] [--laps 3] [--episodes 3] [--speed 1.0] [--random | --long]
Échap ou fermer la fenêtre pour quitter.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pygame

from scripts.eval import _load_model, detect_obs_version
from src.core.constants import MAX_SPEED
from src.game.rendering import draw_keys
from src.core.constants import FPS
from src.rl.wrappers import GymTimeAttack


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="data/models/best/best.zip")
    p.add_argument("--laps", type=int, default=3)
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--speed", type=float, default=1.0, help="2.0 = deux fois plus vite que le temps réel")
    p.add_argument("--random", action="store_true", help="circuits aléatoires (un nouveau à chaque course)")
    p.add_argument("--long", action="store_true", help="circuits longs aléatoires (tracé variante 2)")
    p.add_argument("--same-tracks", action="store_true", help="toujours la même série de circuits (pour comparer des modèles)")
    p.add_argument("--no-keys", action="store_true", help="ne pas afficher les touches du bot")
    a = p.parse_args()

    model, vn = _load_model(a.model)
    env = GymTimeAttack(render_mode="human", procedural=a.random or a.long, laps=a.laps,
                        track_variant=2 if a.long else 1,
                        obs_version=detect_obs_version(model))
    clock = pygame.time.Clock()
    state = {"action": 0}
    if not a.no_keys:
        env.overlay = lambda screen: draw_keys(screen, state["action"], env.ta.car.speed, MAX_SPEED)
    import random as _random
    rng = _random.Random(None if not a.same_tracks else 12345)

    for ep in range(1, a.episodes + 1):
        if (a.random or a.long) and not a.same_tracks:
            obs, _ = env.reset(options={"track_seed": rng.randrange(1000, 10**9)})  # un nouveau circuit à chaque lancement
        else:
            obs, _ = env.reset()
        done, info = False, {}
        while not done:
            o = obs
            if vn is not None:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -vn.clip_obs, vn.clip_obs)
            action = int(model.predict(o, deterministic=True)[0])
            state["action"] = action
            obs, _, term, trunc, info = env.step(action)  # dessine la frame
            done = term or trunc
            for event in pygame.event.get(pygame.KEYDOWN):
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
            clock.tick(FPS * a.speed)
        status = "terminé" if info.get("is_success") else "échec"
        print(f"Course {ep} : {status}, {info.get('laps_done', 0)} tour(s), {env.ta.t:.2f} s")
        pygame.time.wait(1500)
    pygame.quit()


if __name__ == "__main__":
    main()
