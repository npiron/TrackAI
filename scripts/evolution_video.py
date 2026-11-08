"""Vidéo « l'IA apprend à piloter » : plusieurs générations de modèles roulent en même temps
sur le même circuit, chacune de sa couleur, avec le classement en direct. Format vertical (TikTok).

Usage :
  .venv/bin/python scripts/evolution_video.py --out videos/evolution.mp4
  .venv/bin/python scripts/evolution_video.py --models a.zip b.zip c.zip --labels "Gén 1" "Gén 2" "Gén 3" \
      --track-variant 2 --track-seed 7 --laps 1 --out videos/longs.mp4
  --preview : affiche dans une fenêtre au lieu d'enregistrer.

Les modèles sont listés du plus ancien au plus récent. Il faut ffmpeg (Homebrew) pour l'enregistrement.
"""
import argparse
import colorsys
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

# Une sélection chronologique des modèles entraînés sur la piste fixe (de « ne sait pas rouler » au meilleur).
DEFAULT_MODELS = [
    ("data/checkpoints/ppo_t19_final.zip", "PPO brut"),
    ("data/checkpoints/ppo_t24_bc.zip", "1re imitation"),
    ("data/checkpoints/ppo_t30_bc.zip", "Professeur rapide"),
    ("data/checkpoints/ppo_t38.zip", "DAgger"),
    ("data/checkpoints/ppo_t53b.zip", "Zéro choc"),
    ("data/checkpoints/ppo_t65.zip", "Chocs ciblés"),
    ("data/checkpoints/ppo_s5_a.zip", "Pistes variées"),
    ("data/checkpoints/ppo_v2_b.zip", "Nouveaux capteurs"),
    ("data/checkpoints/ppo_v2_ft_c.zip", "Renforcement"),
]

VW, VH = 1080, 1920          # format vertical 9:16
BG = (14, 17, 22)
INK = (236, 238, 242)
MUTED = (140, 146, 158)


def gen_color(i, n):
    """Du rouge (ancien) au vert puis au bleu (récent)."""
    h = (i / max(1, n - 1)) * 0.6
    r, g, b = colorsys.hsv_to_rgb(h, 0.78, 0.98)
    return int(r * 255), int(g * 255), int(b * 255)


class Runner:
    def __init__(self, path, label, color, laps, variant, seed):
        from scripts.eval import _load_model, detect_obs_version
        from src.rl.wrappers import GymTimeAttack
        self.model, self.vn = _load_model(path)
        ov = detect_obs_version(self.model)
        proc = variant == 2 or seed is not None
        self.env = GymTimeAttack(render_mode=None, procedural=proc, laps=laps, obs_version=ov,
                                 track_variant=variant)
        self.obs, _ = self.env.reset(options={"track_seed": seed} if proc else None)
        self.label, self.color, self.laps = label, color, laps
        self.done, self.result, self.hits = False, None, 0

    def act(self, o):
        if self.vn is not None:
            o = np.clip((o - self.vn.obs_rms.mean) / np.sqrt(self.vn.obs_rms.var + self.vn.epsilon),
                        -self.vn.clip_obs, self.vn.clip_obs)
        return int(self.model.predict(o, deterministic=True)[0])

    def step(self):
        if self.done:
            return
        self.obs, _, term, trunc, info = self.env.step(self.act(self.obs))
        self.hits = self.env.ta.wall_hits
        if term or trunc:
            self.done = True
            ok = info.get("laps_done", 0) >= self.laps
            self.result = ("ok", self.env.ta.t) if ok else ("crash", self.env.ta.t)

    @property
    def progress(self):
        ta = self.env.ta
        return ta.lap_count * 100 + sum(ta.cp_visited)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", default=None)
    p.add_argument("--labels", nargs="+", default=None)
    p.add_argument("--track-variant", type=int, default=1)
    p.add_argument("--track-seed", type=int, default=None, help="circuit aléatoire (défaut : piste fixe en variante 1)")
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--max-seconds", type=float, default=35.0)
    p.add_argument("--title", default="L'IA apprend à piloter")
    p.add_argument("--out", default="videos/evolution.mp4")
    p.add_argument("--fps", type=int, default=50)
    p.add_argument("--preview", action="store_true")
    a = p.parse_args(argv)
    if not a.preview:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from src.core.constants import FPS, W, H
    from src.game.rendering import draw_car, draw_track

    if a.models:
        pairs = list(zip(a.models, a.labels or [os.path.basename(m)[:-4] for m in a.models]))
    else:
        pairs = [(m, l) for m, l in DEFAULT_MODELS if os.path.exists(m)]
    n = len(pairs)
    runners = [Runner(m, l, gen_color(i, n), a.laps, a.track_variant, a.track_seed) for i, (m, l) in enumerate(pairs)]
    track = runners[-1].env.ta.track

    pygame.init()
    screen = pygame.display.set_mode((VW, VH) if a.preview else (1, 1))
    frame = pygame.Surface((VW, VH))
    world = pygame.Surface((W, H))
    font = lambda size, bold=False: pygame.font.SysFont("Avenir Next,Helvetica Neue,Arial", size, bold=bold)
    f_title, f_sub, f_row, f_tag, f_big = font(64, True), font(34), font(36), font(22, True), font(46, True)
    tw, th = VW, int(VW * H / W)
    ty = 300

    ff = None
    if not a.preview:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{VW}x{VH}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                               "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", a.out],
                              stdin=subprocess.PIPE)
    clock = pygame.time.Clock()

    def render(t, final=False):
        draw_track(world, track)
        order = sorted(range(n), key=lambda i: i)  # anciens dessous, récents dessus
        for i in order:
            r = runners[i]
            draw_car(world, r.env.ta.car, paint=r.color, skids=False)
        for i in order:  # numéro de génération au-dessus de chaque voiture
            r = runners[i]
            x, y = r.env.ta.car.pos
            tag = f_tag.render(str(i + 1), True, (255, 255, 255))
            pygame.draw.circle(world, r.color, (int(x), int(y) - 26), 13)
            world.blit(tag, tag.get_rect(center=(int(x), int(y) - 26)))
        frame.fill(BG)
        frame.blit(f_title.render(a.title, True, INK), (60, 90))
        frame.blit(f_sub.render(f"{n} générations · même circuit · {a.laps} tour{'s' if a.laps > 1 else ''}",
                                True, MUTED), (60, 175))
        frame.blit(pygame.transform.smoothscale(world, (tw, th)), (0, ty))
        # classement en direct
        y = ty + th + 50
        for i in reversed(range(n)):
            r = runners[i]
            pygame.draw.circle(frame, r.color, (84, y + 22), 16)
            num = f_tag.render(str(i + 1), True, (20, 20, 24))
            frame.blit(num, num.get_rect(center=(84, y + 22)))
            frame.blit(f_row.render(r.label, True, INK), (120, y))
            if r.result and r.result[0] == "ok":
                txt, col = f"✓ {r.result[1]:.2f} s", (120, 220, 140)
            elif r.result:
                txt, col = "crash", (235, 90, 80)
            else:
                ta = r.env.ta
                ncp = len(ta.cp_visited)
                txt = f"tour {min(ta.lap_count + 1, r.laps)} · CP {sum(ta.cp_visited)}/{ncp}" if r.laps > 1 \
                    else f"CP {sum(ta.cp_visited)}/{ncp}"
                col = MUTED
            s = f_row.render(txt, True, col)
            frame.blit(s, (VW - 60 - s.get_width(), y))
            y += 62
        clock_s = f_big.render(f"{t:05.2f} s", True, INK)
        frame.blit(clock_s, (VW - 60 - clock_s.get_width(), 95))
        if final:
            best = [r for r in runners if r.result and r.result[0] == "ok"]
            if best:
                b = min(best, key=lambda r: r.result[1])
                msg = f_big.render(f"Meilleur : {b.label} · {b.result[1]:.2f} s", True, (255, 255, 255))
                box = msg.get_rect(center=(VW // 2, ty + th // 2)).inflate(50, 30)
                pygame.draw.rect(frame, (0, 0, 0), box, border_radius=18)
                frame.blit(msg, msg.get_rect(center=box.center))

    def emit():
        if ff:
            ff.stdin.write(pygame.image.tobytes(frame, "RGB"))
        else:
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    raise SystemExit
            clock.tick(a.fps)

    t, step = 0.0, 0
    sim_per_frame = FPS / a.fps
    acc = 0.0
    while t < a.max_seconds and not all(r.done for r in runners):
        acc += sim_per_frame
        while acc >= 1.0:
            for r in runners:
                r.step()
            t += 1.0 / FPS
            acc -= 1.0
        render(t)
        emit()
    for _ in range(int(a.fps * 3)):  # 3 s sur l'image finale
        render(t, final=True)
        emit()
    if ff:
        ff.stdin.close()
        ff.wait()
        print("vidéo :", a.out)
    for r in runners:
        res = r.result or ("en course", r.env.ta.t)
        print(f"{r.label:20s} {res[0]:9s} {res[1]:6.2f} s  chocs {r.hits}")


if __name__ == "__main__":
    main()
