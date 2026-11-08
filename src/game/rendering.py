
import pygame
import pygame.gfxdraw
import math
from typing import List, Tuple
from src.core.constants import *
from src.game.track import Track
from src.game.car import Car
from src.utils.math_utils import vec

def draw_track(screen, track: Track):
    # Procédural (Surface pré-rendue)
    if getattr(track, 'spline_points', None) is not None and len(track.spline_points):
        if track.visual_surface is None:
            from src.game.track_art import paint_track
            track.visual_surface = paint_track(track)
        _skids["surface"] = track.visual_surface  # les traces de pneus y sont peintes
        screen.blit(track.visual_surface, (0, 0))
    else:
        # Fallback Legacy (Rectangles)
        screen.fill(COLOR_GRASS)
        if track.rect_outer:
            pygame.draw.rect(screen, COLOR_ROAD, track.rect_outer, border_radius=20)
            pygame.draw.rect(screen, COLOR_BORDER, track.rect_outer, width=4, border_radius=20)
            pygame.draw.rect(screen, COLOR_BORDER, track.rect_inner, width=4, border_radius=20)
            pygame.draw.rect(screen, COLOR_GRASS, track.rect_inner, border_radius=20)

    painted = getattr(track, 'visual_surface', None) is not None
    # Checkpoints : deux piliers de part et d'autre de la route (arche vue de dessus) + trait discret
    for cx, cy, angle_or_orient in track.checkpoints:
        if isinstance(angle_or_orient, str):
            angle = math.pi / 2 if angle_or_orient == 'V' else 0
        else:
            angle = angle_or_orient
        c, s_ = math.cos(angle), math.sin(angle)
        if painted:
            half_w = getattr(track, 'half_width', 60) + 2
            p1 = (cx - c * half_w, cy - s_ * half_w)
            p2 = (cx + c * half_w, cy + s_ * half_w)
            pygame.draw.line(screen, (90, 170, 230), p1, p2, width=2)
            for p in (p1, p2):
                pygame.draw.circle(screen, (20, 30, 45), (int(p[0]), int(p[1])), 8)
                pygame.draw.circle(screen, (70, 160, 235), (int(p[0]), int(p[1])), 6)
        else:
            half_w = 50
            pygame.draw.line(screen, COLOR_CHECKPOINT, (cx - c * half_w, cy - s_ * half_w),
                             (cx + c * half_w, cy + s_ * half_w), width=8)

    if painted:
        return  # départ/arrivée déjà peints (damier)

    if track.finish_pos:
        if len(track.finish_pos) == 3:
            fx, fy, f_angle = track.finish_pos
            half_w = 50
            c, s_ = math.cos(f_angle), math.sin(f_angle)
            p1 = (fx - c * half_w, fy - s_ * half_w)
            p2 = (fx + c * half_w, fy + s_ * half_w)
            pygame.draw.line(screen, (255, 255, 255), p1, p2, width=12)
            pygame.draw.line(screen, (0, 0, 0), p1, p2, width=4)
        else:
            fx, fy = track.finish_pos
            pygame.draw.circle(screen, (255, 255, 255), (int(fx), int(fy)), 12)
    if track.start_pos:
        sx, sy = track.start_pos
        pygame.draw.circle(screen, (255, 255, 0), (int(sx), int(sy)), 8)


def draw_ghost(screen, pts: List[Tuple[float, float]], color=(110, 110, 140)):
    if len(pts) < 2:
        return
    pygame.draw.lines(screen, color, False, [(int(x), int(y)) for x, y in pts], width=2)


# Voiture vue de dessus façon monoplace (F1 / Trackmania) : coordonnées locales,
# x vers l'avant, y vers la droite, en px.
_CAR_NOSE = [(21, 0), (18, -1.8), (8, -3.2), (8, 3.2), (18, 1.8)]
_CAR_BODY = [(8, -3.4), (3, -4.2), (0, -7.6), (-9, -7.8), (-15, -4.2), (-19, -2.4), (-19, 2.4),
             (-15, 4.2), (-9, 7.8), (0, 7.6), (3, 4.2), (8, 3.4)]
_CAR_FRONT_WING = [(21.5, -11.5), (18.5, -11.5), (18.5, 11.5), (21.5, 11.5)]
_CAR_REAR_WING = [(-18.5, -9.5), (-21.5, -9.5), (-21.5, 9.5), (-18.5, 9.5)]
_CAR_COCKPIT = [(6, -2.4), (6, 2.4), (-3, 2.6), (-5, 0), (-3, -2.6)]
_CAR_STRIPE = [(21, -0.6), (21, 0.6), (-19, 0.6), (-19, -0.6)]
_CAR_WHEELS = [(12, -9.2), (12, 9.2), (-12, -9.6), (-12, 9.6)]  # avant gauche/droite, arrière
_WHEEL_FRONT = [(-3.6, -2.2), (3.6, -2.2), (3.6, 2.2), (-3.6, 2.2)]
_WHEEL_REAR = [(-4.4, -2.6), (4.4, -2.6), (4.4, 2.6), (-4.4, 2.6)]
CAR_PAINT = (28, 110, 220)
CAR_PAINT_DARK = (16, 64, 140)
CAR_CARBON = (32, 32, 38)


def _place(pts, p, c, s_, dx=0.0, dy=0.0, rot=0.0):
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for x, y in pts:
        x, y = x * cr - y * sr + dx, x * sr + y * cr + dy
        out.append((p[0] + x * c - y * s_, p[1] + x * s_ + y * c))
    return out


def _poly(screen, pts, color):
    import pygame.gfxdraw
    ip = [(round(x), round(y)) for x, y in pts]
    pygame.gfxdraw.filled_polygon(screen, ip, color)
    pygame.gfxdraw.aapolygon(screen, ip, color)


_skids = {"surface": None, "prev": None}


def _draw_skids(screen, car, c, s_):
    """Traces de pneus des roues arrière quand on freine fort ou qu'on glisse.
    Elles sont peintes directement sur le décor du circuit (elles y restent)."""
    import pygame.gfxdraw
    target = _skids["surface"]
    p = car.pos
    rear = [(p[0] - 12 * c - y * s_, p[1] - 12 * s_ + y * c) for y in (-9.6, 9.6)]
    speed = math.hypot(car.vel[0], car.vel[1])
    slip = 0.0
    if speed > 1.0:
        slip = abs((math.atan2(car.vel[1], car.vel[0]) - car.heading + math.pi) % (2 * math.pi) - math.pi)
        if car.speed < 0:
            slip = abs(math.pi - slip)
    marking = target is not None and speed > 2.0 and (
        getattr(car, "braking", False) or car.is_drifting or slip > math.radians(11))
    prev = _skids["prev"]
    if marking and prev is not None and prev[0] is target:
        alpha = 95 if (car.is_drifting or slip > math.radians(20)) else 60
        for a, b in zip(prev[1], rear):
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            if 0 < n < 40:
                ox, oy = -dy / n * 1.5, dx / n * 1.5
                quad = [(a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)]
                pygame.gfxdraw.filled_polygon(target, [(round(x), round(y)) for x, y in quad], (15, 15, 17, alpha))
    _skids["prev"] = (target, rear) if marking else None


def draw_car(screen, car: Car):
    p = (float(car.pos[0]), float(car.pos[1]))
    c, s_ = math.cos(car.heading), math.sin(car.heading)
    _draw_skids(screen, car, c, s_)
    # ombre portée (carrosserie + ailerons)
    for part in (_CAR_BODY, _CAR_NOSE, _CAR_FRONT_WING, _CAR_REAR_WING):
        _poly(screen, _place(part, (p[0] + 3, p[1] + 4), c, s_), (0, 0, 0, 60))
    # bras de suspension
    for wx, wy in _CAR_WHEELS:
        inner = (wx, 3.0 if wy > 0 else -3.0) if wx > 0 else (wx, 6.5 if wy > 0 else -6.5)
        a_, b_ = _place([inner, (wx, wy)], p, c, s_)
        pygame.draw.aaline(screen, (60, 60, 66), a_, b_)
    # roues : celles de devant suivent le volant (même à l'arrêt) ; des rainures défilent quand elles roulent
    steer = getattr(car, "steering", 0.0) * 0.55
    _skids["roll"] = (_skids.get("roll", 0.0) + getattr(car, "speed", 0.0)) % 3.0
    for i, (wx, wy) in enumerate(_CAR_WHEELS):
        rot = steer if i < 2 else 0.0
        shape = _WHEEL_FRONT if i < 2 else _WHEEL_REAR
        hl = shape[1][0]
        _poly(screen, _place(shape, p, c, s_, wx, wy, rot), (20, 20, 22))
        for k in range(3):
            x = hl - ((_skids["roll"] + k * 3.0) % (2 * hl))
            hw = shape[2][1] - 0.3
            _poly(screen, _place([(x - 0.45, -hw), (x + 0.45, -hw), (x + 0.45, hw), (x - 0.45, hw)],
                                 p, c, s_, wx, wy, rot), (68, 68, 74))
        side = shape[2][1]
        rim = [(-1.3, side - 0.8), (1.3, side - 0.8), (1.3, side), (-1.3, side)]
        if wy < 0:
            rim = [(x, -y) for x, y in rim]
        _poly(screen, _place(rim, p, c, s_, wx, wy, rot), (190, 190, 196))
    # ailerons, carrosserie, nez, bande, cockpit et casque
    _poly(screen, _place(_CAR_REAR_WING, p, c, s_), CAR_CARBON)
    _poly(screen, _place([(-18.5, -9.5), (-21.5, -9.5), (-21.5, -7.5), (-18.5, -7.5)], p, c, s_), CAR_PAINT)
    _poly(screen, _place([(-18.5, 7.5), (-21.5, 7.5), (-21.5, 9.5), (-18.5, 9.5)], p, c, s_), CAR_PAINT)
    _poly(screen, _place(_CAR_BODY, p, c, s_), CAR_PAINT)
    _poly(screen, _place([(-1, -6.4), (-9, -6.6), (-13, -3.6), (-13, 3.6), (-9, 6.6), (-1, 6.4)], p, c, s_),
          CAR_PAINT_DARK)  # pontons
    _poly(screen, _place(_CAR_NOSE, p, c, s_), CAR_PAINT)
    _poly(screen, _place(_CAR_FRONT_WING, p, c, s_), CAR_CARBON)
    for y0 in (-11.5, 9.5):
        _poly(screen, _place([(21.5, y0), (18.5, y0), (18.5, y0 + 2), (21.5, y0 + 2)], p, c, s_), CAR_PAINT)
    _poly(screen, _place(_CAR_STRIPE, p, c, s_), (245, 245, 245))
    _poly(screen, _place(_CAR_COCKPIT, p, c, s_), (18, 22, 30))
    hx, hy = _place([(0.5, 0)], p, c, s_)[0]
    pygame.gfxdraw.filled_circle(screen, round(hx), round(hy), 2, (250, 200, 40))  # casque
    pygame.gfxdraw.aacircle(screen, round(hx), round(hy), 2, (250, 200, 40))
    # feux arrière (rouges vifs en marche arrière ou au freinage)
    lit = getattr(car, "speed", 0.0) < -0.1 or getattr(car, "braking", False)
    _poly(screen, _place([(-19.2, -1), (-18.2, -1), (-18.2, 1), (-19.2, 1)], p, c, s_),
          (255, 60, 50) if lit else (120, 20, 20))


def draw_lidar(screen, car: Car, readings: List[float]):
    """Draw LIDAR rays."""
    if not readings:
        return
        
    RAY_LENGTH = 150.0
    angles = [-math.pi/2, -math.pi/4, 0, math.pi/4, math.pi/2]
    
    cx, cy = car.pos
    
    for i, dist_norm in enumerate(readings):
        rel_angle = angles[i]
        abs_angle = car.heading + rel_angle
        
        val = max(0.0, min(1.0, dist_norm))
        color = (int(255 * (1-val)), int(255 * val), 0)
        
        rx = math.cos(abs_angle)
        ry = math.sin(abs_angle)
        
        end_x = cx + rx * (dist_norm * RAY_LENGTH)
        end_y = cy + ry * (dist_norm * RAY_LENGTH)
        
        pygame.draw.line(screen, color, (cx, cy), (end_x, end_y), 1)
        pygame.draw.circle(screen, color, (int(end_x), int(end_y)), 3)

def fmt_time(t: float) -> str:
    m = int(t // 60)
    s = t - 60 * m
    return f"{m:02d}:{s:06.3f}"
