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


def _font(size, bold=False):
    import pygame
    return pygame.font.SysFont("Avenir Next,Helvetica Neue,Arial", size, bold=bold)


NEON_THEMES = {
    # fond (teinte ajoutée), bords gauche/droite, titre, sous-titre, fond de page
    "cyber": dict(tint=(6, 8, 18), dim=0.18, edges=((0, 230, 255), (255, 60, 200)), title=(0, 230, 255),
                  sub=(255, 120, 220), page=(6, 8, 16), grid=None),
    "synthwave": dict(tint=(26, 6, 34), dim=0.16, edges=((255, 140, 40), (255, 40, 160)), title=(255, 120, 60),
                      sub=(255, 80, 190), page=(22, 6, 30), grid=(120, 30, 140)),
    "tron": dict(tint=(2, 4, 8), dim=0.06, edges=((0, 220, 255), (0, 220, 255)), title=(0, 220, 255),
                 sub=(150, 230, 255), page=(2, 4, 8), grid=(0, 60, 80)),
    "ice": dict(tint=(8, 16, 30), dim=0.22, edges=((180, 230, 255), (120, 160, 255)), title=(200, 235, 255),
                sub=(130, 170, 255), page=(8, 14, 26), grid=None),
}


def _neon_track(surface, track, theme="cyber"):
    """Version nuit du circuit : décor assombri, bords de piste lumineux (thème NEON_THEMES)."""
    import pygame
    th = NEON_THEMES[theme]
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    lum = arr.mean(axis=2, keepdims=True)
    arr = arr * th["dim"] + lum * th["dim"] * 0.5 + np.array(th["tint"], np.float32)
    out = pygame.surfarray.make_surface(np.clip(arr, 0, 255).astype(np.uint8))
    w, h = out.get_size()
    if th["grid"]:
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(0, w, 50):
            pygame.draw.line(g, (*th["grid"], 70), (x, 0), (x, h), 1)
        for y in range(0, h, 50):
            pygame.draw.line(g, (*th["grid"], 70), (0, y), (w, y), 1)
        out.blit(g, (0, 0))
    sp = np.asarray(track.spline_points, float)
    t = np.roll(sp, -3, axis=0) - np.roll(sp, 3, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    R = getattr(track, "half_width", 60)
    glow = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    for side, col in zip((1, -1), th["edges"]):
        pts = [tuple(p) for p in (sp + nrm * side * R)[::3]]
        for wd, al in ((11, 30), (6, 80), (2, 255)):
            pygame.draw.lines(glow, (*col, al), True, pts, wd)
    out.blit(glow, (0, 0))
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", default=None)
    p.add_argument("--labels", nargs="+", default=None)
    p.add_argument("--track-variant", type=int, default=1)
    p.add_argument("--track-seed", type=int, default=None, help="circuit aléatoire (défaut : piste fixe en variante 1)")
    p.add_argument("--laps", type=int, default=1)
    p.add_argument("--max-seconds", type=float, default=35.0)
    p.add_argument("--title", default="L'IA apprend à piloter")
    p.add_argument("--subtitle", default=None)
    p.add_argument("--style", default="classic", choices=("classic", "trails", "neon", "chart"),
                   help="classic : classement ; trails : trajectoires de chaque génération ; "
                        "neon : nuit + caméra qui suit la tête ; chart : courbe d'apprentissage en bas")
    p.add_argument("--theme", default="cyber", choices=tuple(NEON_THEMES), help="pour --style neon")
    p.add_argument("--cam", default="follow", choices=("follow", "full"), help="neon : caméra qui suit la tête ou circuit entier")
    p.add_argument("--glow-trails", action="store_true", help="neon : traînées lumineuses de chaque génération")
    p.add_argument("--progress-csv", default="data/checkpoints/long/progress.csv", help="pour --style chart")
    p.add_argument("--still", type=float, default=None, help="image fixe à T secondes (PNG dans --out)")
    p.add_argument("--out", default="videos/evolution.mp4")
    p.add_argument("--fps", type=int, default=50)
    p.add_argument("--preview", action="store_true")
    a = p.parse_args(argv)
    if not a.preview:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    import pygame.gfxdraw
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
    f_title, f_sub, f_row, f_tag, f_big = _font(64, True), _font(34), _font(36), _font(22, True), _font(46, True)
    f_huge = _font(150, True)
    tw, th = VW, int(VW * H / W)
    ty = 300
    trails = [[] for _ in runners]
    base_bg = None
    if a.style == "neon":
        draw_track(world, track)
        base_bg = _neon_track(world.copy(), track, a.theme)
    chart = None
    if a.style == "chart" and os.path.exists(a.progress_csv):
        import csv
        with open(a.progress_csv) as f:
            chart = [r for r in csv.DictReader(f)]
    subtitle = a.subtitle or f"{n} générations · même circuit · {a.laps} tour{'s' if a.laps > 1 else ''}"

    ff = None
    if not a.preview and a.still is None:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{VW}x{VH}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                               "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", a.out],
                              stdin=subprocess.PIPE)
    clock = pygame.time.Clock()

    def status(r):
        if r.result and r.result[0] == "ok":
            return f"{r.result[1]:.2f} s", (120, 220, 140)
        if r.result:
            return "crash", (235, 90, 80)
        ta = r.env.ta
        return f"CP {sum(ta.cp_visited)}/{len(ta.cp_visited)}", MUTED

    def draw_world():
        if base_bg is not None:
            world.blit(base_bg, (0, 0))
        else:
            draw_track(world, track)
        if a.style == "trails":
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            for i, r in enumerate(runners):
                if len(trails[i]) > 1:
                    pygame.draw.lines(layer, (*r.color, 170), False, trails[i], 3)
            world.blit(layer, (0, 0))
        elif a.style == "neon" and a.glow_trails:
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            for i, r in enumerate(runners):
                tr_ = trails[i][-160:]  # traînée de lumière (dernières ~3 s)
                if len(tr_) > 1:
                    for wd, al in ((9, 35), (5, 90), (2, 230)):
                        pygame.draw.lines(layer, (*r.color, al), False, tr_, wd)
            world.blit(layer, (0, 0))
        for i, r in enumerate(runners):
            draw_car(world, r.env.ta.car, paint=r.color, skids=False)
        for i, r in enumerate(runners):
            x, y = r.env.ta.car.pos
            tag = f_tag.render(str(i + 1), True, (255, 255, 255))
            pygame.draw.circle(world, r.color, (int(x), int(y) - 26), 13)
            world.blit(tag, tag.get_rect(center=(int(x), int(y) - 26)))

    def header(t, dark=False):
        frame.blit(f_title.render(a.title, True, INK), (60, 90))
        frame.blit(f_sub.render(subtitle, True, MUTED), (60, 175))
        c = f_big.render(f"{t:05.2f} s", True, INK)
        frame.blit(c, (VW - 60 - c.get_width(), 95))

    def leaderboard(y, rows=None):
        for i in reversed(range(n)) if rows is None else rows:
            r = runners[i]
            pygame.draw.circle(frame, r.color, (84, y + 22), 16)
            num = f_tag.render(str(i + 1), True, (20, 20, 24))
            frame.blit(num, num.get_rect(center=(84, y + 22)))
            frame.blit(f_row.render(r.label, True, INK), (120, y))
            txt, col = status(r)
            s_ = f_row.render(txt, True, col)
            frame.blit(s_, (VW - 60 - s_.get_width(), y))
            y += 62
        return y

    def best_banner(cy):
        best = [r for r in runners if r.result and r.result[0] == "ok"]
        if best:
            b = min(best, key=lambda r: r.result[1])
            msg = f_big.render(f"Meilleur : {b.label} · {b.result[1]:.2f} s", True, (255, 255, 255))
            box = msg.get_rect(center=(VW // 2, cy)).inflate(50, 30)
            pygame.draw.rect(frame, (0, 0, 0), box, border_radius=18)
            frame.blit(msg, msg.get_rect(center=box.center))

    def render(t, final=False):
        draw_world()
        frame.fill(BG)
        if a.style == "neon":
            th_ = NEON_THEMES[a.theme]
            frame.fill(th_["page"])
            lead = max(runners, key=lambda r: (r.result is not None and r.result[0] == "ok", r.progress,
                                               -(r.result[1] if r.result else 0)))
            if a.cam == "follow":
                # caméra qui suit la voiture en tête, zoom x1,8, mini-carte en haut à droite
                cx, cy = lead.env.ta.car.pos
                vw_, vh_ = int(W / 1.8), int(W / 1.8 * 1.25)
                x0 = int(min(max(cx - vw_ / 2, 0), W - vw_))
                y0 = int(min(max(cy - vh_ / 2, 0), H - vh_))
                view = world.subsurface(pygame.Rect(x0, y0, vw_, min(vh_, H - y0))).copy()
                vh2 = int(VW * view.get_height() / view.get_width())
                frame.blit(pygame.transform.smoothscale(view, (VW, vh2)), (0, 260))
                mini = pygame.transform.smoothscale(world, (360, int(360 * H / W)))
                pygame.draw.rect(frame, th_["edges"][0], pygame.Rect(VW - 390, 278, 364, mini.get_height() + 4), 2,
                                 border_radius=6)
                frame.blit(mini, (VW - 388, 280))
            else:
                vh2 = th
                frame.blit(pygame.transform.smoothscale(world, (tw, th)), (0, 300))
                vh2 += 40
            gen = f_huge.render(f"GÉN {runners.index(lead) + 1}", True, lead.color)
            frame.blit(gen, (60, 260 + vh2 + 20))
            frame.blit(f_row.render(f"en tête · {lead.label}", True, INK), (66, 260 + vh2 + 190))
            leaderboard(260 + vh2 + 270, rows=list(reversed(range(n)))[:5 if a.cam == "follow" else 7])
            frame.blit(f_title.render(a.title, True, th_["title"]), (60, 90))
            frame.blit(f_sub.render(subtitle, True, th_["sub"]), (60, 175))
            c = f_big.render(f"{t:05.2f} s", True, INK)
            frame.blit(c, (VW - 60 - c.get_width(), 95))
            if final:
                best_banner(260 + vh2 // 2)
            return
        header(t)
        frame.blit(pygame.transform.smoothscale(world, (tw, th)), (0, ty))
        if a.style == "chart" and chart:
            # courbe d'apprentissage : part des tours finis (vert) et chocs (rouge) par génération
            x0, y0, cw, ch = 70, ty + th + 60, VW - 140, 420
            pygame.draw.rect(frame, (24, 28, 36), pygame.Rect(x0 - 20, y0 - 20, cw + 40, ch + 90), border_radius=16)
            gens = [int(r["gen"]) for r in chart]
            fin = [float(r["taux_tour_fini"]) for r in chart]
            hits = [float(r["chocs_moy"]) for r in chart]
            hmax = max(hits) or 1
            def pt(k, v):
                return (x0 + cw * k / max(1, len(gens) - 1), y0 + ch * (1 - v))
            for vals, col in ((fin, (120, 220, 140)), ([h / hmax for h in hits], (235, 90, 80))):
                pts = [pt(k, v) for k, v in enumerate(vals)]
                if len(pts) > 1:
                    pygame.draw.lines(frame, col, False, pts, 5)
                for q in pts:
                    pygame.draw.circle(frame, col, (int(q[0]), int(q[1])), 7)
            frame.blit(f_row.render("tours finis", True, (120, 220, 140)), (x0, y0 + ch + 20))
            lbl = f_row.render("chocs", True, (235, 90, 80))
            frame.blit(lbl, (x0 + cw - lbl.get_width(), y0 + ch + 20))
            frame.blit(f_sub.render("générations", True, MUTED), (VW // 2 - 90, y0 + ch + 22))
            leaderboard(y0 + ch + 110, rows=list(reversed(range(n)))[:4])
        else:
            leaderboard(ty + th + 50)
        if final:
            best_banner(ty + th // 2)

    def emit():
        if ff:
            ff.stdin.write(pygame.image.tobytes(frame, "RGB"))
        elif a.preview:
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    raise SystemExit
            clock.tick(a.fps)

    t = 0.0
    sim_per_frame = FPS / a.fps
    acc = 0.0
    end = a.max_seconds if a.still is None else a.still
    while t < end and not all(r.done for r in runners):
        acc += sim_per_frame
        while acc >= 1.0:
            for i, r in enumerate(runners):
                r.step()
                if not r.done:
                    x, y = r.env.ta.car.pos
                    if not trails[i] or abs(trails[i][-1][0] - x) + abs(trails[i][-1][1] - y) > 4:
                        trails[i].append((float(x), float(y)))
            t += 1.0 / FPS
            acc -= 1.0
        if a.still is None:
            render(t)
            emit()
    if a.still is not None:
        render(t, final=all(r.done for r in runners))
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        pygame.image.save(frame, a.out)
        print("image :", a.out)
        return
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
