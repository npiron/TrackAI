
import pygame
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


def draw_car(screen, car: Car):
    p = car.pos
    ang = car.heading
    f = vec(math.cos(ang), math.sin(ang))
    r = vec(-math.sin(ang), math.cos(ang))

    nose = p + f * 18
    left = p - f * 12 - r * 10
    right = p - f * 12 + r * 10

    pygame.draw.polygon(
        screen,
        (230, 50, 50),
        [(int(nose[0]), int(nose[1])), (int(left[0]), int(left[1])), (int(right[0]), int(right[1]))],
    )

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
