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
WALL_WHITE = (226, 228, 230)
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


def _grass(surface, rng, k):
    w, h = surface.get_size()
    xs, ys = np.meshgrid(np.arange(w), np.arange(h), indexing="ij")
    band = ((xs + ys) // (46 * k)) % 2  # bandes de tonte en diagonale
    arr = np.where(band[..., None] == 0, np.array(GRASS_A, np.int16), np.array(GRASS_B, np.int16))
    arr = arr + rng.integers(-5, 6, size=(w, h, 1))
    pygame.surfarray.blit_array(surface, np.clip(arr, 0, 255).astype(np.uint8))


def _runs(flags, min_len):
    """Plages contiguës (circulaires) de True d'au moins `min_len` points : [(début, longueur)]."""
    n = len(flags)
    if flags.all():
        return [(0, n)]
    start = int(np.argmin(flags))  # on part d'un False pour gérer la boucle
    out, i = [], 0
    while i < n:
        j = (start + i) % n
        if flags[j]:
            L = 0
            while L < n and flags[(j + L) % n]:
                L += 1
            if L >= min_len:
                out.append((j, L))
            i += L
        else:
            i += 1
    return out


def _band(surface, sp, nrm, arc, i0, length, side, r_in, r_out, block, colors, step=2):
    """Bande continue le long de la piste (côté `side`), entre r_in et r_out, à damier selon l'abscisse."""
    n = len(sp)
    for k in range(0, length, step):
        i, j = (i0 + k) % n, (i0 + min(k + step, length)) % n
        col = colors[int(arc[i] // block) % len(colors)]
        quad = [sp[i] + nrm[i] * side * r_out, sp[j] + nrm[j] * side * r_out,
                sp[j] + nrm[j] * side * r_in, sp[i] + nrm[i] * side * r_in]
        pygame.draw.polygon(surface, col, [tuple(q) for q in quad])


def paint_track(track) -> pygame.Surface:
    """Peint à 2x puis réduit : bords lisses, sans escaliers."""
    k = 2
    R = float(getattr(track, 'half_width', 60)) * k
    rng = np.random.default_rng(track.seed or 0)
    sp = np.asarray(track.spline_points, dtype=float) * k
    n = len(sp)
    big = pygame.Surface((W * k, H * k), 0, 24)
    _grass(big, rng, k)
    pts = [(int(p[0]), int(p[1])) for p in sp]
    _, nrm = _normals(sp)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])

    # ombre portée et muret blanc (juste hors piste : c'est le mur physique)
    for p in pts[::2]:
        pygame.draw.circle(big, SHADOW, (p[0] + 3 * k, p[1] + 4 * k), int(R + 9 * k))
    for p in pts[::2]:
        pygame.draw.circle(big, WALL_WHITE, p, int(R + 6 * k))

    # asphalte grainé
    road = pygame.Surface(big.get_size(), pygame.SRCALPHA)
    for p in pts[::2]:
        pygame.draw.circle(road, ASPHALT_EDGE, p, int(R))
    for p in pts[::2]:
        pygame.draw.circle(road, ASPHALT, p, int(R - 6 * k))
    alpha = pygame.surfarray.pixels_alpha(road)
    rgb = pygame.surfarray.pixels3d(road)
    grain = rng.integers(-7, 8, size=alpha.shape)
    mask = alpha > 0
    for ch_i in range(3):
        ch = rgb[..., ch_i].astype(np.int16)
        ch[mask] += grain[mask]
        rgb[..., ch_i] = np.clip(ch, 0, 255).astype(np.uint8)
    del alpha, rgb
    big.blit(road, (0, 0))

    # muret : bande gris clair continue, liseré sombre côté piste
    for side in (-1.0, 1.0):
        _band(big, sp, nrm, arc, 0, n, side, R, R + 1.2 * k, 1e9, ((150, 150, 152),))

    # vibreurs : bandes continues dans les virages marqués, côté extérieur (et intérieur s'il est large)
    curv = _curvature(sp / k)
    for sign in (1.0, -1.0):
        turning = (curv * sign) > 1 / 300
        # on élargit un peu chaque virage pour que le vibreur commence avant et finisse après
        grown = turning.copy()
        for sh in range(1, 25):
            grown |= np.roll(turning, sh) | np.roll(turning, -sh)
        for i0, L in _runs(grown, 45):
            outer = -sign
            _band(big, sp, nrm, arc, i0, L, outer, R - 9 * k, R, 12 * k, (KERB_RED, KERB_WHITE))
            _band(big, sp, nrm, arc, i0, L, -outer, R - 7 * k, R, 12 * k, (KERB_RED, KERB_WHITE))

    # ligne de départ / arrivée en damier
    fx, fy, fang = track.finish_pos
    fx, fy = fx * k, fy * k
    d = np.array([math.cos(fang), math.sin(fang)])      # le long de la ligne (en travers de la route)
    t = np.array([-d[1], d[0]])                          # le long de la route
    sq = 10 * k
    half = int(R // sq)
    for a in range(-half, half):
        for b in range(-1, 2):
            col = (245, 245, 245) if (a + b) % 2 == 0 else (25, 25, 28)
            o = np.array([fx, fy]) + d * a * sq + t * b * sq
            quad = [o, o + d * sq, o + d * sq + t * sq, o + t * sq]
            pygame.draw.polygon(big, col, [tuple(q) for q in quad])
    return pygame.transform.smoothscale(big, (W, H))
