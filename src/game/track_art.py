"""Peinture du circuit, façon Trackmania (visuel seulement : la physique lit le masque de collision).

Gazon tondu en bandes, asphalte grainé, murets blancs et rouges en bord de piste,
vibreurs rouge et blanc dans les virages, damier sur la ligne d'arrivée.
"""
import math

import numpy as np
import pygame

from src.core.constants import W, H

GRASS_A = (58, 112, 50)
GRASS_B = (66, 124, 56)
SHADOW = (40, 78, 36)
ASPHALT = (74, 76, 82)
ASPHALT_EDGE = (62, 64, 70)
WALL_WHITE = (236, 236, 232)
WALL_RED = (200, 46, 46)
KERB_RED = (214, 52, 48)
KERB_WHITE = (240, 240, 236)


def _normals(sp):
    t = np.roll(sp, -3, axis=0) - np.roll(sp, 3, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    return t, np.stack([-t[:, 1], t[:, 0]], axis=1)


def _curvature(sp, k=12):
    """Courbure signée (1/px) de la ligne centrale, lissée."""
    t, _ = _normals(sp)
    ang = np.arctan2(t[:, 1], t[:, 0])
    d = (np.roll(ang, -k) - np.roll(ang, k) + math.pi) % (2 * math.pi) - math.pi
    seg = np.linalg.norm(np.roll(sp, -k, axis=0) - np.roll(sp, k, axis=0), axis=1)
    return d / np.maximum(seg, 1e-9)


def _grass(surface, rng):
    arr = np.zeros((W, H, 3), dtype=np.int16)
    xs, ys = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
    band = ((xs + ys) // 46) % 2  # bandes de tonte en diagonale
    arr[:] = np.where(band[..., None] == 0, GRASS_A, GRASS_B)
    arr += rng.integers(-5, 6, size=(W, H, 1))
    pygame.surfarray.blit_array(surface, np.clip(arr, 0, 255).astype(np.uint8))


def paint_track(track) -> pygame.Surface:
    R = int(getattr(track, 'half_width', 60))

    rng = np.random.default_rng(track.seed or 0)
    sp = np.asarray(track.spline_points, dtype=float)
    n = len(sp)
    surface = pygame.Surface((W, H))
    _grass(surface, rng)
    pts = [(int(p[0]), int(p[1])) for p in sp]

    # ombre portée et muret (juste hors piste : c'est le mur physique)
    for p in pts:
        pygame.draw.circle(surface, SHADOW, (p[0] + 3, p[1] + 4), R + 9)
    for p in pts:
        pygame.draw.circle(surface, WALL_WHITE, p, R + 6)
    # muret rouge et blanc par tronçons
    road_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(0, n, 2):
        if (i // 40) % 2 == 0:
            pygame.draw.circle(road_layer, WALL_RED, pts[i], R + 6)
    for p in pts:
        pygame.draw.circle(road_layer, (0, 0, 0, 0), p, R)  # creuse l'intérieur
    surface.blit(road_layer, (0, 0))

    # asphalte grainé : on peint la route dans un calque puis on ajoute du grain
    road = pygame.Surface((W, H), pygame.SRCALPHA)
    for p in pts:
        pygame.draw.circle(road, ASPHALT_EDGE, p, R)
    for p in pts:
        pygame.draw.circle(road, ASPHALT, p, R - 6)
    alpha = pygame.surfarray.pixels_alpha(road)
    rgb = pygame.surfarray.pixels3d(road)
    grain = rng.integers(-7, 8, size=alpha.shape)
    mask = alpha > 0
    for c in range(3):
        ch = rgb[..., c].astype(np.int16)
        ch[mask] += grain[mask]
        rgb[..., c] = np.clip(ch, 0, 255).astype(np.uint8)
    del alpha, rgb
    surface.blit(road, (0, 0))

    # vibreurs : à l'extérieur et à l'intérieur des virages marqués
    _, nrm = _normals(sp)
    curv = _curvature(sp)
    step = 6
    for i in range(0, n, step):
        c = curv[i]
        if abs(c) < 1 / 260:
            continue
        j = (i + step) % n
        color = KERB_RED if (i // step) % 2 == 0 else KERB_WHITE
        outer = -np.sign(c)  # côté extérieur du virage
        for side, depth in ((outer, 10), (-outer, 8)):
            if side == -outer and abs(c) > 1 / 110:
                continue  # intérieur trop serré : on ne dessine que l'extérieur
            a0 = sp[i] + nrm[i] * side * R
            a1 = sp[j] + nrm[j] * side * R
            b1 = sp[j] + nrm[j] * side * (R - depth)
            b0 = sp[i] + nrm[i] * side * (R - depth)
            pygame.draw.polygon(surface, color, [tuple(a0), tuple(a1), tuple(b1), tuple(b0)])

    # ligne de départ / arrivée en damier
    fx, fy, fang = track.finish_pos
    d = np.array([math.cos(fang), math.sin(fang)])      # le long de la ligne (en travers de la route)
    t = np.array([-d[1], d[0]])                          # le long de la route
    sq = 10
    for a in range(-R // sq, R // sq):
        for b in range(-1, 2):
            col = (245, 245, 245) if (a + b) % 2 == 0 else (25, 25, 28)
            o = np.array([fx, fy]) + d * a * sq + t * b * sq
            quad = [o, o + d * sq, o + d * sq + t * sq, o + t * sq]
            pygame.draw.polygon(surface, col, [tuple(q) for q in quad])
    return surface
