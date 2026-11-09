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
    p.add_argument("--mute", action="store_true", help="sans le son (M pour couper/remettre en cours de route)")
    p.add_argument("--follow", default=None, metavar="DOSSIER",
                   help="suivre un entraînement en cours : recharge la dernière génération de DOSSIER avant chaque course")
    a = p.parse_args()

    import glob
    import re

    def latest_gen():
        gens = sorted(glob.glob(os.path.join(a.follow, "gen_*.zip")))
        return gens[-1] if gens else None

    current = None
    if a.follow:
        a.episodes = 10**9
        pygame.init()
        while latest_gen() is None:  # l'entraînement n'a pas encore sauvé de génération
            print("En attente de la première génération dans", a.follow, flush=True)
            pygame.time.wait(5000)
        current = latest_gen()
        a.model = current
    model, vn = _load_model(a.model)
    env = GymTimeAttack(render_mode="human", procedural=a.random or a.long, laps=a.laps,
                        track_variant=2 if a.long else 1,
                        obs_version=detect_obs_version(model))
    clock = pygame.time.Clock()
    import math
    from src.game.audio import CarAudio
    audio = None if a.mute else CarAudio()
    sound = {"contacts": 0, "cps": 0}

    def play_audio(action):
        """Son de la voiture du bot : moteur, pneus, chocs, carillon aux checkpoints."""
        if audio is None:
            return
        ta = env.ta
        c = ta.car
        v = math.hypot(c.vel[0], c.vel[1])
        slip = 0.0
        if v > 1.0:
            slip = abs(math.degrees((math.atan2(c.vel[1], c.vel[0]) - c.heading + math.pi) % (2 * math.pi) - math.pi))
            slip = min(slip, 180 - slip) if c.speed < 0 else slip
        audio.update(v / MAX_SPEED, action in (1, 5, 6), slip, c.is_drifting, action in (2, 7, 8) and c.speed > 0.5)
        if ta.wall_contacts > sound["contacts"]:
            sound["contacts"] = ta.wall_contacts
            audio.play("hit", min(1.0, 0.25 + v / MAX_SPEED))
        cps = sum(ta.cp_visited) + ta.lap_count * len(ta.cp_visited)
        if cps > sound["cps"]:
            audio.play("chime")
        sound["cps"] = cps
    state = {"action": 0}
    label = {"text": ""}
    font = None

    def overlay(screen):
        nonlocal font
        if not a.no_keys:
            draw_keys(screen, state["action"], env.ta.car, MAX_SPEED)
        if label["text"]:
            font = font or pygame.font.SysFont("Avenir Next Condensed", 34, bold=True, italic=True)
            img = font.render(label["text"], True, (255, 255, 255))
            box = pygame.Surface((img.get_width() + 28, img.get_height() + 14), pygame.SRCALPHA)
            pygame.draw.rect(box, (12, 14, 20, 180), box.get_rect(), border_radius=12)
            box.blit(img, (14, 7))
            screen.blit(box, (screen.get_width() - box.get_width() - 14, 12))
    env.overlay = overlay

    def gen_label(path):
        m = re.search(r"gen_(\d+)", os.path.basename(path))
        return f"Génération {int(m.group(1))}  (en direct)" if m else ""
    if a.follow:
        label["text"] = gen_label(current)
    import random as _random
    rng = _random.Random(None if not a.same_tracks else 12345)

    for ep in range(1, a.episodes + 1):
        if a.follow and latest_gen() != current:
            current = latest_gen()
            pygame.time.wait(1000)  # laisse l'entraînement finir d'écrire les fichiers
            model, vn = _load_model(current)
            label["text"] = gen_label(current)
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
            play_audio(action)
            for event in pygame.event.get(pygame.KEYDOWN):
                if event.key == pygame.K_ESCAPE:
                    if audio is not None:
                        audio.close()
                    pygame.quit()
                    return
                if event.key == pygame.K_m and audio is not None:
                    audio.toggle_mute()
            clock.tick(FPS * a.speed / env.action_repeat)  # une décision = action_repeat images
        status = "terminé" if info.get("is_success") else "échec"
        print(f"Course {ep} : {status}, {info.get('laps_done', 0)} tour(s), {env.ta.t:.2f} s")
        if audio is not None and info.get("is_success"):
            audio.play("fanfare")
        for _ in range(75):           # pause de 1,5 s ; le son continue (fanfare), moteur coupé
            if audio is not None:
                audio.silence()
            pygame.event.pump()
            clock.tick(50)
        sound["contacts"], sound["cps"] = 0, 0
    if audio is not None:
        audio.close()
    pygame.quit()


if __name__ == "__main__":
    main()
