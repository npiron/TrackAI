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
    p.add_argument("--track-seed", type=int, default=None, help="toujours ce circuit (son numéro)")
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
    # --- chronos : tour en cours, tours faits, PB (génération affichée), WR (tous temps, sur ce circuit) ---
    import json
    from src.game.rendering import fmt_time
    rec_path = os.path.join("data", "bot_records.json")
    try:
        with open(rec_path) as f:
            records = json.load(f)
    except (OSError, ValueError):
        records = {}
    chrono = {"pb": None, "gen": None, "seen_laps": 0, "splits": [], "seen_cps": 0, "popups": []}
    fonts = {}

    def track_key():
        return f"{env.ta.track.seed}-{a.laps}"   # chaque circuit (numéro + nombre de tours) a son propre WR

    def on_new_laps():
        """Met à jour PB et WR quand un tour vient d'être bouclé."""
        ta = env.ta
        for lt in ta.lap_times[chrono["seen_laps"]:]:
            if chrono["pb"] is None or lt < chrono["pb"]:
                chrono["pb"] = lt
            key = track_key()
            if key:
                r = records.setdefault(key, {})
                if r.get("lap") is None or lt < r["lap"]:
                    r["lap"], r["lap_gen"] = round(lt, 3), chrono["gen"]
        chrono["seen_laps"] = len(ta.lap_times)
        key = track_key()
        if key and len(ta.lap_times) >= a.laps:
            r = records.setdefault(key, {})
            total = sum(ta.lap_times)
            if r.get("total") is None or total < r["total"]:
                r["total"], r["total_gen"] = round(total, 3), chrono["gen"]
                r["splits"] = [round(x, 3) for x in chrono["splits"]]   # temps intermédiaires du record
        if key:
            with open(rec_path, "w") as f:
                json.dump(records, f, indent=1)

    def check_splits():
        """À chaque porte (ou ligne d'arrivée) franchie : temps intermédiaire + écart au record, au-dessus du portail."""
        ta = env.ta
        n_cp = len(ta.cp_visited)
        passed = sum(ta.cp_visited) + ta.lap_count * n_cp
        if passed <= chrono["seen_cps"]:
            return
        chrono["seen_cps"] = passed
        t = ta.t
        chrono["splits"].append(t)
        idx = len(chrono["splits"]) - 1
        ref = records.get(track_key(), {}).get("splits", [])
        if sum(ta.cp_visited) == 0 and ta.lap_count > 0:       # ligne d'arrivée : on vient de finir un tour
            x, y = ta.track.finish_pos[:2]
        else:
            last = max(i for i, v in enumerate(ta.cp_visited) if v)
            x, y = ta.track.checkpoints[last][:2]
        delta = (t - ref[idx]) if idx < len(ref) else None
        chrono["popups"].append([x, y, t, delta, pygame.time.get_ticks()])

    def draw_splits(screen):
        now = pygame.time.get_ticks()
        chrono["popups"] = [p for p in chrono["popups"] if now - p[4] < 2500]
        for x, y, t, delta, t0 in chrono["popups"]:
            age = (now - t0) / 2500
            rise = 18 * age
            lines = [(fmt_time(t), (255, 255, 255))]
            if delta is not None:
                lines.append((f"{'+' if delta > 0 else '−'}{abs(delta):.2f}",
                              (240, 90, 80) if delta > 0 else (90, 220, 130)))
            imgs = [fonts["mid"].render(txt, True, col) for txt, col in lines]
            w = max(i.get_width() for i in imgs) + 16
            h = sum(i.get_height() for i in imgs) + 8
            box = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(box, (12, 14, 20, int(190 * (1 - age * 0.6))), box.get_rect(), border_radius=10)
            yy = 4
            for im in imgs:
                box.blit(im, ((w - im.get_width()) // 2, yy))
                yy += im.get_height()
            screen.blit(box, (x - w / 2, y - 70 - rise - h / 2))

    def draw_chrono(screen):
        if not fonts:
            fonts["big"] = pygame.font.SysFont("Avenir Next Condensed", 40, bold=True, italic=True)
            fonts["mid"] = pygame.font.SysFont("Avenir Next Condensed", 24, bold=True, italic=True)
            fonts["small"] = pygame.font.SysFont("Avenir Next,Helvetica Neue", 16)
        ta = env.ta
        r = records.get(track_key() or "", {})
        cur_lap = min(ta.lap_count + 1, a.laps)
        cur_t = ta.t - ta._lap_start_t if ta.lap_count < a.laps else 0.0
        rows = len(ta.lap_times)
        h = 150 + 22 * rows
        box = pygame.Surface((300, h), pygame.SRCALPHA)
        pygame.draw.rect(box, (12, 14, 20, 180), box.get_rect(), border_radius=14)
        screen.blit(box, (14, 12))
        blit = lambda f, txt, col, pos: screen.blit(fonts[f].render(txt, True, col), pos)
        title = f"Circuit #{ta.track.seed}"
        blit("small", f"{title}   ·   tour {cur_lap}/{a.laps}", (190, 196, 210), (30, 22))
        blit("big", fmt_time(cur_t), (255, 255, 255), (28, 40))
        y = 92
        best_all = r.get("lap")
        for i, lt in enumerate(ta.lap_times):
            col = (225, 228, 236)
            if best_all is not None and lt <= best_all + 1e-9:
                col = (200, 120, 255)            # violet : record absolu
            elif chrono["pb"] is not None and lt <= chrono["pb"] + 1e-9:
                col = (90, 220, 130)             # vert : meilleur tour de cette génération
            blit("small", f"T{i + 1}   {fmt_time(lt)}", col, (30, y))
            y += 22
        pb = fmt_time(chrono["pb"]) if chrono["pb"] is not None else "—"
        wr = f"{fmt_time(r['lap'])}  (gén. {r.get('lap_gen')})" if r.get("lap") is not None else "—"
        blit("small", f"PB tour  {pb}", (90, 220, 130), (30, y + 4))
        blit("small", f"WR tour  {wr}", (200, 120, 255), (30, y + 26))
        if a.laps > 1:
            tot = f"{fmt_time(r['total'])}  (gén. {r.get('total_gen')})" if r.get("total") is not None else "—"
            blit("small", f"Record {a.laps} tours  {tot}", (230, 200, 120), (30, y + 48))

    def overlay(screen):
        nonlocal font
        if not a.no_keys:
            draw_keys(screen, state["action"], env.ta.car, MAX_SPEED)
        check_splits()
        if len(env.ta.lap_times) > chrono["seen_laps"]:
            on_new_laps()
        draw_chrono(screen)
        draw_splits(screen)
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
        m_ = re.search(r"gen_(\d+)", os.path.basename(current))
        chrono["gen"] = int(m_.group(1)) if m_ else None
    import random as _random
    rng = _random.Random(None if not a.same_tracks else 12345)

    for ep in range(1, a.episodes + 1):
        if a.follow and latest_gen() != current:
            current = latest_gen()
            pygame.time.wait(1000)  # laisse l'entraînement finir d'écrire les fichiers
            model, vn = _load_model(current)
            label["text"] = gen_label(current)
            m_ = re.search(r"gen_(\d+)", os.path.basename(current))
            chrono["gen"], chrono["pb"] = (int(m_.group(1)) if m_ else None), None   # nouvelle génération : PB à zéro
        if a.track_seed is not None:
            obs, _ = env.reset(options={"track_seed": a.track_seed})
        elif (a.random or a.long) and not a.same_tracks:
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
        chrono["seen_laps"], chrono["seen_cps"], chrono["splits"] = 0, 0, []
    if audio is not None:
        audio.close()
    pygame.quit()


if __name__ == "__main__":
    main()
