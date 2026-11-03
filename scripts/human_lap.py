"""Chrono humain sur la piste fixe, avec le même chrono que le banc (1/FPS par frame de TimeAttackEnv).

Usage : python scripts/human_lap.py [--laps 3]   (flèches, R reset, ESC quitte)
Le meilleur total (tous les tours finis) est écrit dans data/human_best.json.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game.env import TimeAttackEnv
from src.game.track import build_track

HUMAN_BEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "human_best.json")


def replay(actions, laps=1):
    """Rejoue des actions (steer, accel, brake) ; renvoie (finished, total, lap_times)."""
    env = TimeAttackEnv(build_track(), procedural=False, laps=laps)
    env.reset()
    for a in actions:
        env.step(a)
        if env.done:
            break
    finished = env.done and env.lap_count >= laps
    return finished, (env.t if finished else None), list(env.lap_times)


def load_best(path=HUMAN_BEST):
    """Meilleur total humain (float) ou None."""
    try:
        with open(path) as f:
            return json.load(f).get("human_best_total")
    except (OSError, ValueError):
        return None


def record(total, lap_times, laps, path=HUMAN_BEST):
    """Écrit le résultat s'il bat le meilleur existant (même nombre de tours). Renvoie True si écrit."""
    try:
        with open(path) as f:
            cur = json.load(f)
    except (OSError, ValueError):
        cur = {}
    if cur.get("human_best_total") is not None and cur.get("laps") == laps and cur["human_best_total"] <= total:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"human_best_total": round(total, 4), "laps": laps,
                   "lap_times": [round(t, 4) for t in lap_times]}, f, indent=2)
    return True


def play(laps):
    import pygame
    from src.core.constants import FPS, W, H
    from src.game.rendering import draw_track, draw_car, fmt_time
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Menlo", 18)
    track = build_track()
    env = TimeAttackEnv(track, procedural=False, laps=laps)
    env.reset()
    msg = ""
    running = True
    while running:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                env.reset()
                msg = ""
        k = pygame.key.get_pressed()
        if not env.done:
            env.step(((1.0 if k[pygame.K_RIGHT] else 0.0) - (1.0 if k[pygame.K_LEFT] else 0.0),
                      1.0 if k[pygame.K_UP] else 0.0, 1.0 if k[pygame.K_DOWN] else 0.0))
            if env.done:
                if env.lap_count >= laps:
                    msg = "FINI " + fmt_time(env.t) + (" (record !)" if record(env.t, env.lap_times, laps) else "")
                else:
                    msg = "ECHEC - R pour recommencer"
        draw_track(screen, track)
        draw_car(screen, env.car)
        txt = f"Tour {min(env.lap_count + 1, laps)}/{laps}  {fmt_time(env.t)}  " + \
              " ".join(fmt_time(t) for t in env.lap_times) + "  " + msg
        screen.blit(font.render(txt, True, (235, 235, 245)), (14, 14))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--laps", type=int, default=1)
    play(ap.parse_args().laps)
