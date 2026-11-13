"""Regarder le meilleur modèle jouer, en temps réel.

Usage : .venv/bin/python scripts/watch_best.py [--model data/models/best/best.zip] [--laps 3] [--episodes 3] [--speed 1.0] [--random | --long]
Échap ou fermer la fenêtre pour quitter.
"""
import argparse
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pygame

from scripts.eval import _load_model, detect_action_set, detect_obs_version
from src.core.constants import H, MAX_SPEED, W
from src.game.rendering import draw_keys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_hard_seeds(which, path):
    """Circuits durs de hard_tracks.json (scripts/hard_tracks.py), du plus dur au plus facile.
    which : "train", "val", "all" (les deux, dans l'ordre du classement) ou None (aucun)."""
    if which is None:
        return []
    import json
    with open(path) as f:
        d = json.load(f)
    if which != "all":
        return list(d[which])
    out = []
    for i in range(max(len(d["train"]), len(d["val"]))):
        out += d["train"][i:i + 1] + d["val"][i:i + 1]
    return out
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
    p.add_argument("--hard", nargs="?", const="train", default=None, choices=("train", "val", "all"),
                   help="enchaîne les circuits durs de --hard-file, du plus dur au plus facile "
                        "(train : ceux de l'entraînement ciblé, val : jamais vus, all : les deux)")
    p.add_argument("--hard-file", default=os.path.join(_ROOT, "data", "hard_tracks", "hard_tracks.json"))
    p.add_argument("--screenshot", default=None, help="enregistre la fenêtre après --shot-at décisions puis quitte")
    p.add_argument("--shot-at", type=int, default=400)
    p.add_argument("--mute", action="store_true", help="sans le son (M pour couper/remettre en cours de route)")
    p.add_argument("--ghost", default=None, metavar="MODELE",
                   help="un autre modèle roule en fantôme (avec --follow : la génération précédente, par défaut)")
    p.add_argument("--no-ghost", action="store_true", help="pas de fantôme")
    p.add_argument("--follow", default=None, metavar="DOSSIER",
                   help="suivre un entraînement en cours : recharge la dernière génération de DOSSIER avant chaque course")
    a = p.parse_args()
    if a.hard is not None:
        a.long = True

    import glob
    import json
    import re

    def latest_gen():
        gens = sorted(glob.glob(os.path.join(a.follow, "gen_*.zip")))
        if gens:
            return gens[-1]
        try:   # reprise : en attendant la première génération, montrer le modèle de départ
            with open(os.path.join(a.follow, "config.json")) as f:
                init = json.load(f).get("init")
            return init if init and os.path.isfile(init) else None
        except (OSError, ValueError):
            return None

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
                        obs_version=detect_obs_version(model), action_set=detect_action_set(model))
    SIDE = 400
    env.sidebar = SIDE        # panneau d'infos à gauche : chronos et touches n'empiètent plus sur le circuit
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
        _, gas, brk = env.controls(action)
        audio.update(v / MAX_SPEED, gas > 0, slip, c.is_drifting, brk > 0 and c.speed > 0.5, pan=c.pos[0] / W * 2 - 1)
        if ta.wall_contacts > sound["contacts"]:
            sound["contacts"] = ta.wall_contacts
            audio.play("hit", min(1.0, 0.25 + v / MAX_SPEED))
        cps = sum(ta.cp_visited) + ta.lap_count * len(ta.cp_visited)
        if cps > sound["cps"]:
            audio.play("chime")
        sound["cps"] = cps
    state = {"action": 0}
    vol_msg = {"text": "", "until": 0.0}
    # --- fantôme : un autre modèle (par défaut la génération précédente) a roulé sur le même circuit juste avant ---
    ghost = {"path": None, "run": None, "label": ""}
    from src.game.rendering import draw_car
    ghost_layer = pygame.Surface((W, H), pygame.SRCALPHA)

    def previous_model(path):
        """Génération qui précède `path` dans le dossier suivi (ou le modèle de départ d'une reprise)."""
        gens = sorted(glob.glob(os.path.join(a.follow, "gen_*.zip")))
        if path in gens and gens.index(path) > 0:
            return gens[gens.index(path) - 1]
        try:
            with open(os.path.join(a.follow, "config.json")) as f:
                init = json.load(f).get("init")
            return init if init and os.path.isfile(init) and init != path else None
        except (OSError, ValueError):
            return None

    def ghost_name(path):
        m = re.search(r"gen_(\d+)", os.path.basename(path))
        return f"gén. {int(m.group(1))}" if m else os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path)

    def prepare_ghost(seed):
        """Fait rouler le modèle fantôme sur ce circuit (sans affichage, moins d'une seconde par tour)."""
        ghost["run"] = None
        if a.no_ghost or not ghost["path"] or seed is None or not a.long:   # fantôme : circuits longs seulement
            return
        from scripts.human_lap import bot_run
        try:
            ghost["run"] = bot_run(seed, a.laps, True, model_path=ghost["path"])
        except Exception as e:  # modèle illisible : on continue sans fantôme
            print("fantôme impossible :", e, flush=True)

    def draw_world(screen):
        g = ghost["run"]
        if not g or not g["frames"]:
            return
        from scripts.human_lap import _GhostCar
        f = g["frames"][min(int(round(env.ta.t * FPS)), len(g["frames"]) - 1)]
        ghost_layer.fill((0, 0, 0, 0))
        draw_car(ghost_layer, _GhostCar(f), paint=(120, 230, 255), skids=False)
        ghost_layer.set_alpha(140)
        screen.blit(ghost_layer, (0, 0))
    env.world_overlay = draw_world

    def volume_step(event):
        """+ / - (quelle que soit la disposition du clavier) ou pavé numérique : ±10 % de volume."""
        if event.unicode == "+" or event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
            return 0.1
        if event.unicode == "-" or event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            return -0.1
        return 0.0
    label = {"text": ""}
    font = None
    # --- chronos : tour en cours, tours faits, PB de vitesse (génération affichée), record de vitesse (tous temps,
    #     tous circuits : la vitesse moyenne du tour se compare d'un circuit à l'autre). Les records par circuit (WR)
    #     ne sont tenus que sur un circuit fixe (--track-seed, --same-tracks) : un circuit aléatoire ne revient jamais.
    import json
    from src.game.rendering import fmt_time
    rec_path = os.path.join("data", "bot_records.json")
    try:
        with open(rec_path) as f:
            records = json.load(f)
    except (OSError, ValueError):
        records = {}
    chrono = {"pb": None, "gen": None, "seen_laps": 0, "splits": [], "seen_cps": 0, "popups": [],
              "session_best": None, "session_splits": []}
    speed_path = os.path.join("data", "bot_speed_record.json")
    try:
        with open(speed_path) as f:
            speed_rec = json.load(f)
    except (OSError, ValueError):
        speed_rec = {}
    fixed_tracks = a.track_seed is not None or a.same_tracks or a.hard is not None

    def lap_speed(lt):
        """Vitesse moyenne d'un tour en fraction de la vitesse max (longueur de la ligne centrale / temps)."""
        return float(env.ta._arc_lengths()[-1]) / lt / (MAX_SPEED * FPS) if lt > 0 else 0.0
    fonts = {}

    def track_key():
        if not fixed_tracks:
            return None                          # circuit aléatoire : pas de record par circuit
        return f"{env.ta.track.seed}-{a.laps}"   # chaque circuit (numéro + nombre de tours) a son propre WR

    def on_new_laps():
        """Met à jour PB et WR quand un tour vient d'être bouclé."""
        ta = env.ta
        for lt in ta.lap_times[chrono["seen_laps"]:]:
            v = lap_speed(lt)
            if chrono["pb"] is None or v > chrono["pb"]:
                chrono["pb"] = v                 # PB de la génération : meilleure vitesse moyenne au tour
            if v > speed_rec.get("speed", 0.0):
                speed_rec.update(speed=round(v, 4), gen=chrono["gen"], seed=ta.track.seed,
                                 run=os.path.basename(os.path.normpath(a.follow)) if a.follow else None)
                with open(speed_path, "w") as f:
                    json.dump(speed_rec, f, indent=1)
            key = track_key()
            if key:
                r = records.setdefault(key, {})
                if r.get("lap") is None or lt < r["lap"]:
                    r["lap"], r["lap_gen"] = round(lt, 3), chrono["gen"]
        chrono["seen_laps"] = len(ta.lap_times)
        key = track_key()
        if len(ta.lap_times) >= a.laps:
            total = sum(ta.lap_times)
            if chrono["session_best"] is None or total < chrono["session_best"]:
                chrono["session_best"], chrono["session_splits"] = total, list(chrono["splits"])
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
        # référence : le record (s'il a ses temps intermédiaires), sinon la meilleure course vue dans cette session
        g = ghost["run"]
        ref = (g["splits"] if g else None) or records.get(track_key(), {}).get("splits") or chrono["session_splits"]
        if sum(ta.cp_visited) == 0 and ta.lap_count > 0:       # ligne d'arrivée : on vient de finir un tour
            x, y = ta.track.finish_pos[:2]
        else:
            last = max(i for i, v in enumerate(ta.cp_visited) if v)
            x, y = ta.track.checkpoints[last][:2]
        delta = (t - ref[idx]) if idx < len(ref) else None
        chrono["popups"] = [p for p in chrono["popups"] if (p[0], p[1]) != (x, y)]   # remplace l'ancien sur cette porte
        chrono["popups"].append([x, y, t, delta, t])

    def draw_splits(screen):
        now = env.ta.t                                   # temps de jeu : même rendu à toute vitesse
        chrono["popups"] = [p for p in chrono["popups"] if 0 <= now - p[4] < 2.0]
        for x, y, t, delta, t0 in chrono["popups"]:
            age = (now - t0) / 2.0
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
            screen.blit(box, (SIDE + x - w / 2, y - 70 - rise - h / 2))

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
        h = (172 if fixed_tracks else 150) + 22 * rows + (22 if ghost["run"] else 0)
        oy = 70                                 # sous le numéro de génération
        box = pygame.Surface((SIDE - 28, h), pygame.SRCALPHA)
        pygame.draw.rect(box, (30, 33, 42, 255), box.get_rect(), border_radius=14)
        screen.blit(box, (14, 12 + oy))
        blit = lambda f, txt, col, pos: screen.blit(fonts[f].render(txt, True, col), (pos[0], pos[1] + oy))
        title = f"Circuit #{ta.track.seed}"
        blit("small", f"{title}   ·   tour {cur_lap}/{a.laps}", (190, 196, 210), (30, 22))
        blit("big", fmt_time(cur_t), (255, 255, 255), (28, 40))
        y = 92
        pct = lambda v: f"{100 * v:.1f} %".replace(".", ",")
        for i, lt in enumerate(ta.lap_times):
            v = lap_speed(lt)
            col = (225, 228, 236)
            if v >= speed_rec.get("speed", 9.0) - 1e-9:
                col = (200, 120, 255)            # violet : record de vitesse absolu
            elif chrono["pb"] is not None and v >= chrono["pb"] - 1e-9:
                col = (90, 220, 130)             # vert : meilleur tour de cette génération
            blit("small", f"T{i + 1}   {fmt_time(lt)}   {pct(v)}", col, (30, y))
            y += 22
        pb = pct(chrono["pb"]) if chrono["pb"] is not None else "—"
        rec = "—"
        if speed_rec.get("speed"):
            rec = pct(speed_rec["speed"]) + (f"  (gén. {speed_rec['gen']})" if speed_rec.get("gen") is not None else "")
        g = ghost["run"]
        if g:
            gt = fmt_time(g["total"]) if g.get("total") else "n'a pas fini"
            blit("small", f"Fantôme ({ghost_name(ghost['path'])})  {gt}", (120, 230, 255), (30, y - 2))
            y += 22
        blit("small", f"PB vitesse  {pb}", (90, 220, 130), (30, y + 4))
        blit("small", f"Record vitesse  {rec}", (200, 120, 255), (30, y + 26))
        if fixed_tracks:
            wr = f"{fmt_time(r['lap'])}  (gén. {r.get('lap_gen')})" if r.get("lap") is not None else "—"
            blit("small", f"WR tour (ce circuit)  {wr}", (230, 200, 120), (30, y + 48))

    def overlay(screen):
        nonlocal font
        if vol_msg["text"] and time.time() < vol_msg["until"]:   # niveau du volume, affiché 1,5 s après un réglage
            fv = fonts.get("mid") or pygame.font.SysFont("Avenir Next Condensed", 24, bold=True, italic=True)
            img = fv.render(vol_msg["text"], True, (255, 255, 255))
            box = pygame.Surface((img.get_width() + 24, img.get_height() + 12), pygame.SRCALPHA)
            pygame.draw.rect(box, (12, 14, 20, 200), box.get_rect(), border_radius=10)
            box.blit(img, (12, 6))
            screen.blit(box, (SIDE + W // 2 - box.get_width() // 2, 16))
        if not a.no_keys:
            draw_keys(screen, env.controls(state["action"]), env.ta.car, MAX_SPEED)
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
            screen.blit(box, (14, 12))   # en haut du panneau
    env.overlay = overlay

    def gen_label(path):
        m = re.search(r"gen_(\d+)", os.path.basename(path))
        return f"Génération {int(m.group(1))}  (en direct)" if m else ""
    if a.follow:
        label["text"] = gen_label(current)
    m_ = re.search(r"gen_(\d+)", os.path.basename(current or a.model))
    chrono["gen"] = int(m_.group(1)) if m_ else None
    import random as _random
    rng = _random.Random(None if not a.same_tracks else 12345)
    hard_seeds, hard_i = load_hard_seeds(a.hard, a.hard_file), [0]
    if hard_seeds:
        print(f"{len(hard_seeds)} circuits durs ({a.hard}), du plus dur au plus facile : {hard_seeds[:10]}...", flush=True)

    for ep in range(1, a.episodes + 1):
        if a.follow and latest_gen() != current:
            current = latest_gen()
            pygame.time.wait(1000)  # laisse l'entraînement finir d'écrire les fichiers
            model, vn = _load_model(current)
            label["text"] = gen_label(current)
            m_ = re.search(r"gen_(\d+)", os.path.basename(current))
            chrono["gen"], chrono["pb"] = (int(m_.group(1)) if m_ else None), None   # nouvelle génération : PB à zéro
        ghost["path"] = a.ghost or (previous_model(current) if a.follow else None)
        seed = None
        if a.track_seed is not None:
            seed = a.track_seed
        elif hard_seeds:
            seed = hard_seeds[hard_i[0] % len(hard_seeds)]
            hard_i[0] += 1
        elif (a.random or a.long) and not a.same_tracks:
            seed = rng.randrange(1000, 10**9)  # un nouveau circuit à chaque lancement
        elif a.long:
            seed = rng.randrange(1000, 10**9)
        prepare_ghost(seed)
        obs, _ = env.reset(options={"track_seed": seed}) if seed is not None else env.reset()
        done, info = False, {}
        while not done:
            o = obs
            if vn is not None:
                o = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + vn.epsilon), -vn.clip_obs, vn.clip_obs)
            action = int(model.predict(o, deterministic=True)[0])
            state["action"] = action
            obs, _, term, trunc, info = env.step(action)  # dessine la frame
            done = term or trunc
            shots = state.get("n", 0) + 1
            state["n"] = shots
            if a.screenshot and shots == a.shot_at:
                pygame.image.save(pygame.display.get_surface(), a.screenshot)
                if audio is not None:
                    audio.close()
                pygame.quit()
                return
            play_audio(action)
            for event in pygame.event.get(pygame.KEYDOWN):
                if event.key == pygame.K_ESCAPE:
                    if audio is not None:
                        audio.close()
                    pygame.quit()
                    return
                if event.key == pygame.K_m and audio is not None:
                    audio.toggle_mute()
                step = volume_step(event)
                if step and audio is not None:
                    vol_msg["text"], vol_msg["until"] = f"Volume {round(100 * audio.change_volume(step))} %", time.time() + 1.5
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
