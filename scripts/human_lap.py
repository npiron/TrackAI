"""Chrono humain sur la piste fixe, avec le même chrono que le banc (1/FPS par frame de TimeAttackEnv).

Usage : python scripts/human_lap.py [--laps 3] [--long] [--seed 4821]
  flèches, WASD ou ZQSD ; Entrée retour au dernier checkpoint ; R recommencer ; N nouveau circuit (--long) ; Échap quitte.
  Le meilleur bot roule en fantôme ; médailles d'après son chrono ; records par circuit dans data/human_tracks.json.
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


TRACK_RECORDS = os.path.join(os.path.dirname(HUMAN_BEST), "human_tracks.json")
BOT_MODEL = os.path.join(os.path.dirname(HUMAN_BEST), "models", "best", "best.zip")
# Médailles : multiples du chrono du bot (« IA » = battre le bot)
MEDALS = (("IA", 1.0, (120, 230, 255)), ("Or", 1.5, (250, 200, 60)), ("Argent", 2.0, (205, 210, 220)),
          ("Bronze", 2.6, (205, 135, 75)))
COUNTDOWN = 1.6   # secondes avant le départ (3, 2, 1)


def _load_records(path=None):
    path = path or TRACK_RECORDS
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_record(key, total, splits, path=None):
    """Record par circuit (clé = graine) : garde le meilleur total et ses temps intermédiaires."""
    path = path or TRACK_RECORDS
    recs = _load_records(path)
    cur = recs.get(key)
    if cur and cur["total"] <= total:
        return False
    recs[key] = {"total": round(total, 4), "splits": [round(x, 4) for x in splits]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(recs, f, indent=1)
    return True


def bot_run(seed, laps, long_tracks, model_path=BOT_MODEL):
    """Fait rouler le meilleur bot sur le circuit : trajectoire image par image, temps intermédiaires, total."""
    if not os.path.exists(model_path):
        return None
    import contextlib
    import io
    import numpy as np
    from scripts.eval import Pilot, _load_model, detect_obs_version
    from src.rl.wrappers import GymTimeAttack
    model, vn = _load_model(model_path)
    try:
        obs_version = detect_obs_version(model)
    except ValueError:
        return None   # modèle d'une ancienne version de l'observation : pas de fantôme
    env = GymTimeAttack(render_mode=None, procedural=long_tracks, laps=laps, track_variant=2,
                        obs_version=obs_version, action_repeat=1)  # trajectoire image par image
    pilot = Pilot(model, vn)
    obs, _ = env.reset(options={"track_seed": seed} if long_tracks else None)
    frames, splits, done, info = [], [], False, {}
    with contextlib.redirect_stdout(io.StringIO()):
        while not done:
            n0 = sum(env.ta.cp_visited) + env.ta.lap_count * len(env.ta.cp_visited)
            obs, _, t, tr, info = env.step(pilot.act(obs))
            c = env.ta.car
            frames.append((float(c.pos[0]), float(c.pos[1]), float(c.heading), float(c.steering), float(c.speed)))
            if sum(env.ta.cp_visited) + env.ta.lap_count * len(env.ta.cp_visited) > n0:
                splits.append(env.ta.t)
            done = t or tr
    ok = info.get("laps_done", 0) >= laps
    return {"frames": frames, "splits": splits, "total": env.ta.t if ok else None}


class _GhostCar:
    def __init__(self, f):
        self.pos, self.heading, self.steering, self.speed = (f[0], f[1]), f[2], f[3], f[4]
        self.braking = False


def play(laps, long_tracks=False, seed=None):
    import random
    import pygame
    from src.core.constants import FPS, W, H, MAX_SPEED
    from src.game.rendering import draw_track, draw_car, fmt_time, draw_keys
    from src.game.track import generate_procedural_track
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("TrackAI")
    clock = pygame.time.Clock()
    big = pygame.font.SysFont("Avenir Next Condensed", 46, bold=True, italic=True)
    mid = pygame.font.SysFont("Avenir Next Condensed", 26, bold=True, italic=True)
    small = pygame.font.SysFont("Avenir Next,Helvetica Neue", 16)
    huge = pygame.font.SysFont("Avenir Next Condensed", 150, bold=True, italic=True)
    ghost_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    import math
    from src.game.audio import CarAudio
    audio = CarAudio()
    last_count, contacts_seen = None, 0

    def text(font, s, color, pos, anchor="topleft", shadow=True):
        img = font.render(s, True, color)
        r = img.get_rect(**{anchor: pos})
        if shadow:
            screen.blit(font.render(s, True, (0, 0, 0)), r.move(2, 2))
        screen.blit(img, r)
        return r

    def panel(rect, alpha=170):
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (12, 14, 20, alpha), surf.get_rect(), border_radius=14)
        screen.blit(surf, rect.topleft)

    def load(new_seed):
        nonlocal track, env, bot, key, best, start_t, snap, splits, msg, delta, medal
        track = generate_procedural_track(seed=new_seed, variant=2) if long_tracks else build_track()
        key = f"long-{new_seed}-{laps}" if long_tracks else f"fixe-{laps}"
        screen.fill((20, 22, 28))
        text(mid, "Le bot repère le circuit…", (235, 235, 245), (W // 2, H // 2), "center")
        pygame.display.flip()
        bot = bot_run(new_seed, laps, long_tracks)
        best = _load_records().get(key)
        restart()

    def restart():
        nonlocal env, start_t, snap, splits, msg, delta, medal, last_count, contacts_seen
        env = TimeAttackEnv(track, procedural=False, laps=laps)
        last_count, contacts_seen = None, 0
        env.reset()
        start_t = pygame.time.get_ticks()
        snap = None
        splits, msg, delta, medal = [], "", None, None

    def car_state():
        c = env.car
        return (c.pos.copy(), c.vel.copy(), c.heading, c.steering, c.angular_velocity, c.is_drifting, c.speed)

    def respawn():
        """Retour au dernier checkpoint passé, avec la vitesse qu'on y avait ; le chrono continue."""
        if snap is None:
            restart()
            return
        c = env.car
        c.pos, c.vel, c.heading, c.steering, c.angular_velocity, c.is_drifting, c.speed = \
            snap[0].copy(), snap[1].copy(), *snap[2:]
        env._frames_since_wall = 10**6

    track = env = bot = key = best = snap = delta = medal = None
    start_t, splits, msg = 0, [], ""
    seed = seed if seed is not None else random.randint(0, 99999)
    load(seed)
    running = True
    while running:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
                audio.toggle_mute()
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                restart()
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_BACKSPACE) and not env.done:
                respawn()
            elif long_tracks and ev.type == pygame.KEYDOWN and ev.key == pygame.K_n:
                seed = random.randint(0, 99999)
                load(seed)
        k = pygame.key.get_pressed()
        up = k[pygame.K_UP] or k[pygame.K_w] or k[pygame.K_z]
        down = k[pygame.K_DOWN] or k[pygame.K_s]
        left = k[pygame.K_LEFT] or k[pygame.K_a] or k[pygame.K_q]
        right = k[pygame.K_RIGHT] or k[pygame.K_d]
        countdown = COUNTDOWN - (pygame.time.get_ticks() - start_t) / 1000.0
        count = int(countdown / COUNTDOWN * 3) + 1 if countdown > 0 else 0
        if count != last_count:
            audio.play("beep" if count > 0 else "go")
            last_count = count
        if countdown <= 0 and not env.done:
            n_cp = len(env.cp_visited)
            n0 = sum(env.cp_visited) + env.lap_count * n_cp
            env.step(((1.0 if right else 0.0) - (1.0 if left else 0.0), 1.0 if up else 0.0, 1.0 if down else 0.0))
            if sum(env.cp_visited) + env.lap_count * n_cp > n0 and not env.done:
                splits.append(env.t)
                snap = car_state()
                audio.play("chime")
                ref = best["splits"] if best else (bot["splits"] if bot else [])
                if len(ref) >= len(splits) and env.t > 1.0:  # pas d'écart pour la porte collée au départ
                    delta = (env.t - ref[len(splits) - 1], pygame.time.get_ticks())
            if env.wall_contacts > contacts_seen:   # nouveau choc : volume selon la vitesse
                contacts_seen = env.wall_contacts
                audio.play("hit", min(1.0, 0.25 + math.hypot(*env.car.vel) / MAX_SPEED))
            if env.done:
                audio.silence()
                if env.lap_count >= laps:
                    audio.play("fanfare")
                    rec = _save_record(key, env.t, splits)
                    if not long_tracks:
                        record(env.t, env.lap_times, laps)
                    if bot and bot["total"]:
                        medal = next((m for m in MEDALS if env.t <= bot["total"] * m[1] + 1e-9), None)
                    msg = "Record !" if rec else ""
                    best = _load_records().get(key)
                else:
                    msg = "Échec"

        c = env.car
        v = math.hypot(c.vel[0], c.vel[1])
        slip = 0.0
        if v > 1.0:
            slip = abs(math.degrees((math.atan2(c.vel[1], c.vel[0]) - c.heading + math.pi) % (2 * math.pi) - math.pi))
            slip = min(slip, 180 - slip) if c.speed < 0 else slip
        if not env.done:
            audio.update(v / MAX_SPEED, bool(up) and countdown <= 0, slip, c.is_drifting, bool(down) and c.speed > 0.5,
                         running=countdown <= 0)
        # --- dessin ---
        nxt = next((i for i, v in enumerate(env.cp_visited) if not v), None)
        draw_track(screen, track, checkpoints=nxt)
        if bot and countdown <= 0:
            f = bot["frames"][min(int(round(env.t * FPS)), len(bot["frames"]) - 1)]
            ghost_layer.fill((0, 0, 0, 0))
            draw_car(ghost_layer, _GhostCar(f), paint=(120, 230, 255), skids=False)
            ghost_layer.set_alpha(150)
            screen.blit(ghost_layer, (0, 0))
        draw_car(screen, env.car)

        # bandeau : circuit, chrono, record, médailles
        hud = pygame.Rect(14, 12, 350, 168 if bot and bot["total"] else 110)
        panel(hud)
        name = f"Circuit #{seed}" if long_tracks else "Circuit fixe"
        text(small, f"{name}   ·   tour {min(env.lap_count + 1, laps)}/{laps}", (190, 196, 210), (30, 22), shadow=False)
        text(big, fmt_time(env.t), (255, 255, 255), (28, 40), shadow=False)
        text(small, "Record  " + (fmt_time(best["total"]) if best else "—"), (190, 196, 210), (30, 94), shadow=False)
        if bot and bot["total"]:
            for i, (mname, mult, col) in enumerate(MEDALS):
                x, y = 30 + (i % 2) * 165, 120 + (i // 2) * 24
                pygame.draw.circle(screen, col, (x + 6, y + 9), 6)
                text(small, f"{mname}  {fmt_time(bot['total'] * mult)}", (225, 228, 236), (x + 18, y), shadow=False)
        # écart au checkpoint (vert = en avance)
        if delta and pygame.time.get_ticks() - delta[1] < 2200 and not env.done:
            d = delta[0]
            text(big, f"{'+' if d > 0 else '−'}{abs(d):.2f}", (240, 90, 80) if d > 0 else (90, 220, 130),
                 (W // 2, 70), "center")
        # touches et vitesse, en bas à gauche
        act = {(0, 0): 0, (0, 1): 1, (0, 2): 2, (-1, 0): 3, (1, 0): 4, (-1, 1): 5, (1, 1): 6, (-1, 2): 7, (1, 2): 8}
        sx = (1 if right else 0) - (1 if left else 0)
        pedal = 1 if up else (2 if down else 0)
        draw_keys(screen, act.get((sx, pedal), 0), env.car, MAX_SPEED)
        hints = "Entrée : dernier checkpoint    R : recommencer    M : son" + ("    N : nouveau circuit" if long_tracks else "") + "    Échap : quitter"
        text(small, hints, (220, 224, 232), (W - 16, H - 14), "bottomright")
        # compte à rebours
        if countdown > 0:
            text(huge, str(int(countdown / COUNTDOWN * 3) + 1), (255, 255, 255), (W // 2, H // 2), "center")
        elif countdown > -0.6:
            text(huge, "GO", (90, 220, 130), (W // 2, H // 2), "center")
        # fin de course
        if env.done:
            box = pygame.Rect(0, 0, 460, 220)
            box.center = (W // 2, H // 2)
            panel(box, 200)
            if env.lap_count >= laps:
                text(mid, "Arrivée" + ("  ·  " + msg if msg else ""), (235, 235, 245), (box.centerx, box.y + 22), "midtop", False)
                text(big, fmt_time(env.t), (255, 255, 255),
                     (box.centerx, box.y + 62), "midtop", False)
                if medal:
                    pygame.draw.circle(screen, medal[2], (box.centerx - 70, box.y + 146), 12)
                    text(mid, "Médaille " + medal[0], medal[2], (box.centerx - 50, box.y + 130), "topleft", False)
                elif bot and bot["total"]:
                    text(mid, "Pas de médaille", (190, 196, 210), (box.centerx, box.y + 130), "midtop", False)
            else:
                text(mid, "Échec", (240, 90, 80), (box.centerx, box.y + 60), "midtop", False)
            text(small, "R : rejouer" + ("    N : nouveau circuit" if long_tracks else ""), (190, 196, 210),
                 (box.centerx, box.bottom - 30), "midtop", False)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--laps", type=int, default=1)
    ap.add_argument("--long", action="store_true", help="circuits longs aléatoires (N : nouveau circuit) ; pas de record")
    ap.add_argument("--seed", type=int, default=None, help="rejouer un circuit long précis (son numéro)")
    a = ap.parse_args()
    play(a.laps, a.long, a.seed)
