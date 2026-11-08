
from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
import math
import numpy as np
import random

from src.core.constants import W, H, CHECKPOINT_RADIUS, COLOR_ROAD, COLOR_GRASS, COLOR_BORDER

def catmull_rom_spline(P0, P1, P2, P3, n_points=20):
    """
    Calcule n_points sur le segment P1->P2 en utilisant P0 et P3 comme points de contrôle.
    """
    P0, P1, P2, P3 = map(np.array, [P0, P1, P2, P3])
    alpha = 0.5
    
    def tj(ti, Pi, Pj):
        return (np.linalg.norm(Pi - Pj))**alpha + ti

    t0 = 0
    t1 = tj(t0, P0, P1)
    t2 = tj(t1, P1, P2)
    t3 = tj(t2, P2, P3)

    t = np.linspace(t1, t2, n_points)
    t = t.reshape(len(t), 1)
    
    A1 = (t1-t)/(t1-t0)*P0 + (t-t0)/(t1-t0)*P1
    A2 = (t2-t)/(t2-t1)*P1 + (t-t1)/(t2-t1)*P2
    A3 = (t3-t)/(t3-t2)*P2 + (t-t2)/(t3-t2)*P3
    
    B1 = (t2-t)/(t2-t0)*A1 + (t-t0)/(t2-t0)*A2
    B2 = (t3-t)/(t3-t1)*A2 + (t-t1)/(t3-t1)*A3
    
    C = (t2-t)/(t2-t1)*B1 + (t-t1)/(t2-t1)*B2
    return list(map(tuple, C)) # Retourne liste de tuples (x,y)

@dataclass
class Track:
    # Propriétés de base
    start_pos: Tuple[float, float]
    start_heading: float
    finish_pos: Tuple[float, float, float] # (x, y, angle) like checkpoints

    # Checkpoints : (x, y, angle_rad) -> Angle remplace 'H'/'V'
    checkpoints: List[Tuple[float, float, float]]
    
    # Masque de collision (Road = 1, Grass = 0)
    collision_mask: pygame.Mask
    
    # Optimisation Numba
    occupancy_grid: np.ndarray # bool 2D array
    
    # Surface visuelle pré-rendue (pour la performance)
    visual_surface: Optional[pygame.Surface]  # peinte à la demande (src/game/track_art.py)
    
    # Mathematical representation for alignment reward
    spline_points: np.ndarray # Shape (N, 2)
    
    # Reproducibility
    seed: Optional[int] = None
    
    # Legacy support (optionnel)
    rect_outer: Optional[pygame.Rect] = None
    rect_inner: Optional[pygame.Rect] = None
    walls: Optional[List[pygame.Rect]] = None
    boost_zones: Optional[List[pygame.Rect]] = None
    half_width: float = 60.0  # demi-largeur de route (px)

    def get_closest_track_info(self, pos: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Retourne (tangent_vector, distance_to_center) pour le point de la piste le plus proche.
        Optimisé avec Numpy.
        """
        # 1. Trouver le point le plus proche
        # Broadcasting: pos (2,) - spline_points (N, 2) -> (N, 2)
        diff = self.spline_points - pos
        dists_sq = np.sum(diff * diff, axis=1)
        idx = np.argmin(dists_sq)
        
        # 2. Distance exacte
        dist_to_center = np.sqrt(dists_sq[idx])
        
        # 3. Calculer la tangente à cet endroit
        # On prend le point suivant vs le point actuel (ou précédent)
        # Gestion des indices cycliques
        n_points = len(self.spline_points)
        p_next = self.spline_points[(idx + 1) % n_points]
        p_prev = self.spline_points[(idx - 1 + n_points) % n_points]
        
        # Vecteur tangent centré (plus stable que next - curr)
        tangent = p_next - p_prev
        norm = np.linalg.norm(tangent)
        if norm > 0:
            tangent /= norm
            
        return tangent, float(dist_to_center)

    def inside_track(self, p: np.ndarray) -> bool:
        """Vérifie si le point est sur la route via le masque."""
        x, y = int(p[0]), int(p[1])
        if 0 <= x < W and 0 <= y < H:
            # Mask.get_at retourne 1 si set, 0 sinon
            return self.collision_mask.get_at((x, y)) == 1
        return False
    
    def on_boost(self, p: np.ndarray) -> bool:
        if not self.boost_zones:
            return False
        x, y = float(p[0]), float(p[1])
        for zone in self.boost_zones:
            if zone.collidepoint(x, y):
                return True
        return False
    
    def hits_wall(self, p: np.ndarray) -> bool:
        """Collision avec les bords de l'écran ou zones interdites."""
        # Dans le mode procédural, si on n'est pas sur la route, c'est un mur (herbe)
        # Mais pour être permissif, disons que hits_wall c'est sortir de l'écran
        x, y = float(p[0]), float(p[1])
        return x < 0 or x > W or y < 0 or y > H

ROAD_HALF_WIDTH = 60


def _spline(points):
    """Catmull-Rom fermé, 150 points par segment."""
    pts = points[-1:] + points + points[:2]
    out = []
    for i in range(len(pts) - 3):
        out.extend(catmull_rom_spline(pts[i], pts[i + 1], pts[i + 2], pts[i + 3], n_points=150))
    return out


def _track_ok(sp, min_radius=85.0, half_width=ROAD_HALF_WIDTH):
    """Tracé valide : virages pas plus serrés que `min_radius` (ligne centrale) et
    aucune portion de piste qui en touche une autre (sauf ses voisines)."""
    clearance = 2 * half_width + 30
    a = np.asarray(sp, dtype=float)
    n = len(a)
    if n < 100:
        return False
    k = 10
    p0, p1, p2 = a, np.roll(a, -k, axis=0), np.roll(a, -2 * k, axis=0)
    ab = np.linalg.norm(p1 - p0, axis=1)
    bc = np.linalg.norm(p2 - p1, axis=1)
    ca = np.linalg.norm(p2 - p0, axis=1)
    cross = np.abs((p1[:, 0] - p0[:, 0]) * (p2[:, 1] - p0[:, 1]) - (p1[:, 1] - p0[:, 1]) * (p2[:, 0] - p0[:, 0]))
    with np.errstate(divide="ignore", invalid="ignore"):
        r = ab * bc * ca / (2 * cross)
    if np.nanmin(np.where(cross < 1e-9, np.inf, r)) < min_radius:
        return False
    if a[:, 0].min() < half_width + 5 or a[:, 0].max() > W - half_width - 5:
        return False
    if a[:, 1].min() < half_width + 5 or a[:, 1].max() > H - half_width - 5:
        return False
    sub = a[::8]
    seg = np.linalg.norm(np.diff(a, axis=0), axis=1).sum() / len(a) * 8  # longueur moyenne entre deux sous-points
    m = len(sub)
    d = np.linalg.norm(sub[:, None, :] - sub[None, :, :], axis=2)
    idx = np.arange(m)
    gap = np.abs(idx[:, None] - idx[None, :])
    gap = np.minimum(gap, m - gap) * seg  # distance le long de la piste
    near_on_track = gap < 3 * clearance
    return bool(np.all(d[~near_on_track] >= clearance))


GRID_COLS, GRID_ROWS, CELL = 7, 5, 172
V2_HALF_WIDTH = 45  # route plus étroite : plus de place pour un tracé long


def _has_hole_or_pinch(cells):
    for x in range(-1, GRID_COLS):
        for y in range(-1, GRID_ROWS):
            q = [(x, y) in cells, (x + 1, y) in cells, (x, y + 1) in cells, (x + 1, y + 1) in cells]
            if q == [True, False, False, True] or q == [False, True, True, False]:
                return True  # deux cases qui ne se touchent que par un coin
    outside, todo = set(), [(-1, -1)]
    while todo:
        c = todo.pop()
        if c in outside or c in cells or not (-1 <= c[0] <= GRID_COLS and -1 <= c[1] <= GRID_ROWS):
            continue
        outside.add(c)
        todo += [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]
    return (GRID_COLS + 2) * (GRID_ROWS + 2) - len(outside) - len(cells) != 0


def _polyomino(rng, n_cells):
    """Forme aléatoire de cases connexes, sans trou ni pincement (son contour sera le circuit).
    La croissance préfère les cases qui ne touchent qu'une case : des « bras » fins, donc un contour long."""
    cells = {(rng.randrange(GRID_COLS), rng.randrange(GRID_ROWS))}
    nb = lambda c: [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]
    banned = set()
    while len(cells) < n_cells:
        cand = sorted({c for x in cells for c in nb(x) if c not in cells and c not in banned
                       and 0 <= c[0] < GRID_COLS and 0 <= c[1] < GRID_ROWS})
        if not cand:
            break
        w = [1.0 if sum(n in cells for n in nb(c)) == 1 else 0.12 for c in cand]
        c = rng.choices(cand, weights=w)[0]
        cells.add(c)
        if _has_hole_or_pinch(cells):
            cells.discard(c)
            banned.add(c)
    return cells if len(cells) >= 6 else None


def _outline(cells):
    """Contour du polyomino : liste ordonnée des coins (coordonnées de grille)."""
    edges = {}
    for (x, y) in cells:
        for a, b, n in (((x, y), (x + 1, y), (x, y - 1)), ((x + 1, y), (x + 1, y + 1), (x + 1, y)),
                        ((x + 1, y + 1), (x, y + 1), (x, y + 1)), ((x, y + 1), (x, y), (x - 1, y))):
            if n not in cells:
                edges[a] = b  # sens horaire, une seule arête sortante par sommet si sans pincement
    if len(edges) != sum(1 for _ in edges):
        return None
    start = min(edges)
    loop, v = [start], edges[start]
    while v != start:
        if v not in edges or len(loop) > 400:
            return None
        loop.append(v)
        v = edges[v]
    if len(loop) != len(edges):
        return None  # pincement (deux cases qui ne se touchent que par un coin)
    corners = [loop[i] for i in range(len(loop))
               if (loop[i][0] - loop[i - 1][0], loop[i][1] - loop[i - 1][1])
               != (loop[(i + 1) % len(loop)][0] - loop[i][0], loop[(i + 1) % len(loop)][1] - loop[i][1])]
    return corners


def _fillet_path(corners, rng, spacing=1.5):
    """Lignes droites entre les coins, chaque coin arrondi par un arc de rayon aléatoire."""
    P = [np.array(c, dtype=float) for c in corners]
    n = len(P)
    arcs = []
    for i in range(n):
        a, v, b = P[i - 1], P[i], P[(i + 1) % n]
        u1, u2 = (v - a) / np.linalg.norm(v - a), (b - v) / np.linalg.norm(b - v)
        turn = math.acos(max(-1.0, min(1.0, float(u1 @ u2))))
        r = rng.uniform(72, 200)
        d = r * math.tan(turn / 2)
        dmax = 0.5 * min(np.linalg.norm(v - a), np.linalg.norm(b - v))
        if d > dmax:
            d, r = dmax, dmax / math.tan(turn / 2)
        arcs.append((v - u1 * d, v + u2 * d, r, u1, u2))
    out = []
    for i in range(n):
        p_in, p_out, r, u1, u2 = arcs[i]
        # arc du coin i : centre à distance r de p_in, perpendiculaire à u1, côté du virage
        side = 1.0 if (u1[0] * u2[1] - u1[1] * u2[0]) > 0 else -1.0
        nrm = np.array([-u1[1], u1[0]]) * side
        c = p_in + nrm * r
        a0 = math.atan2(p_in[1] - c[1], p_in[0] - c[0])
        a1 = math.atan2(p_out[1] - c[1], p_out[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        k = max(2, int(abs(da) * r / spacing))
        for t in range(k):
            ang = a0 + da * t / k
            out.append((c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)))
        # ligne droite jusqu'au coin suivant
        q = arcs[(i + 1) % n][0]
        L = float(np.linalg.norm(q - p_out))
        k = max(1, int(L / spacing))
        for t in range(k):
            out.append(tuple(p_out + (q - p_out) * t / k))
    return out


def _track_v2(rng):
    """Circuit long et lisible : contour d'une forme aléatoire (L, U, S, escaliers…),
    lignes droites et virages arrondis de rayons variés."""
    n_cells = rng.randint(12, 24)
    cells = _polyomino(rng, n_cells)
    if not cells:
        return None
    corners = _outline(cells)
    if not corners or len(corners) < 4:
        return None
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    ox = (W - (max(xs) + min(xs)) * CELL) / 2  # forme centrée à l'écran
    oy = (H - (max(ys) + min(ys)) * CELL) / 2
    pts = []
    for (gx, gy) in corners:
        jx, jy = rng.uniform(-5, 5), rng.uniform(-5, 5)  # angles pas toujours droits
        pts.append((ox + gx * CELL + jx, oy + gy * CELL + jy))
    return _fillet_path(pts, rng)


def generate_procedural_track(seed: Optional[int] = None, variant: int = 1) -> Track:
    """Génère un circuit aléatoire basé sur des splines.

    variant=1 : tracé historique (piste fixe build_track et banc de 50 pistes inchangés).
    variant=2 : tracé plus varié (épingles, chicanes, lignes droites), validé géométriquement.
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    random.seed(seed)
    np.random.seed(seed)

    if variant == 2:
        rng = random.Random(seed)
        for _ in range(2000):
            spline_points = _track_v2(rng)
            if spline_points and _track_ok(spline_points, min_radius=78, half_width=V2_HALF_WIDTH):
                break
        else:
            raise RuntimeError(f"aucun tracé valide pour la graine {seed}")
        return _finish_track(spline_points, seed, V2_HALF_WIDTH)
    
    # 1. Générer points de contrôle pour un VRAI circuit de course
    # On crée un tracé avec des sections variées (lignes droites, virages serrés, courbes rapides)
    center = (W/2, H/2)
    base_radius_x = W * 0.38  # Légèrement plus grand pour avoir de la place
    base_radius_y = H * 0.38
    n_points = 16  # Plus de points = circuit plus long et complexe
    
    points = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        
        # Variation stratégique du rayon pour créer des sections différentes
        # On alterne entre sections rapides (grand rayon) et techniques (petit rayon)
        section_type = i % 4
        
        if section_type == 0:  # Ligne droite / Courbe rapide
            r_var_x = random.uniform(1.1, 1.3)
            r_var_y = random.uniform(1.1, 1.3)
        elif section_type == 1:  # Transition
            r_var_x = random.uniform(0.95, 1.05)
            r_var_y = random.uniform(0.95, 1.05)
        elif section_type == 2:  # Virage serré (épingle)
            r_var_x = random.uniform(0.7, 0.85)
            r_var_y = random.uniform(0.7, 0.85)
        else:  # Courbe moyenne
            r_var_x = random.uniform(0.9, 1.1)
            r_var_y = random.uniform(0.9, 1.1)
        
        px = center[0] + math.cos(angle) * base_radius_x * r_var_x
        py = center[1] + math.sin(angle) * base_radius_y * r_var_y
        
        # Clamp to screen with margins
        px = max(120, min(W-120, px))
        py = max(120, min(H-120, py))
        points.append((px, py))
        
    spline_points = _spline(points)
    return _finish_track(spline_points, seed)


def _finish_track(spline_points, seed, half_width=ROAD_HALF_WIDTH) -> Track:
    """Masque de collision, checkpoints, départ et arrivée à partir de la ligne centrale."""
    # Create mask surface for occupancy grid generation
    mask_surf = pygame.Surface((W, H))
    mask_surf.fill((0, 0, 0))
    for p in spline_points:
        pygame.draw.circle(mask_surf, (255, 255, 255), (int(p[0]), int(p[1])), int(half_width))
    
    # Random obstacles removed for clean racing

    # Convertir en mask pygame
    collision_mask = pygame.mask.from_threshold(mask_surf, (255, 255, 255), (10, 10, 10))
    
    # === OPTIMISATION NUMBA ===
    # Convertir en grille Numpy (C-contiguous, bool) pour le JIT
    # surfarray est (W, H), on veut (H, W) pour l'accès [row, col] -> [y, x]
    # Ou on garde (W, H) et on accède [x, y]. JIT ops utilise [py, px]. 
    # Mon jit_ops utilise grid[py, px], donc il attend (H, W).
    # Pygame surfarray.array3d retourne (Width, Height, 3).
    # Donc arr[x, y].
    # Je vais transpose pour avoir (Height, Width) -> arr[y, x].
    arr = pygame.surfarray.array3d(mask_surf)
    # Blanc = (255,255,255) => Route. Noir = (0,0,0) => Mur.
    # On prend canal rouge > 128.
    occupancy_grid = (arr[:, :, 0] > 128).T.astype(np.bool_)
     
    # 3. Placer Checkpoints
    
    # 3. Placer Checkpoints
    # On en place régulièremet sur la spline
    checkpoints = []
    step = len(spline_points) // 8 # 8 Checkpoints
    
    for i in range(0, len(spline_points), step):
        if len(checkpoints) >= 8: break
        
        p = spline_points[i]
        
        # Calcul de la tangente pour l'orientation
        # Next point
        next_p = spline_points[(i + 5) % len(spline_points)]
        dx = next_p[0] - p[0]
        dy = next_p[1] - p[1]
        angle = math.atan2(dy, dx)
        
        checkpoints.append((p[0], p[1], angle + math.pi/2)) # checkpoint perpendiculaire route
        
    start_idx = 0
    start_pos = spline_points[start_idx]
    
    # Heading initial: vers le point suivant
    p_next = spline_points[5]
    start_heading = math.atan2(p_next[1]-start_pos[1], p_next[0]-start_pos[0])
    
    # Finish Line
    f_idx = -10
    p_finish = spline_points[f_idx]
    
    # Calculate orientation for finish line
    # Depending on list length, f_idx+5 might wrap or be valid. 
    # spline_points is a list. Negative index works if valid range.
    # To be safe, we use modulo logic relative to length.
    L = len(spline_points)
    idx_next = (L + f_idx + 5) % L
    
    p_finish_next = spline_points[idx_next]
    
    dx_f = p_finish_next[0] - p_finish[0]
    dy_f = p_finish_next[1] - p_finish[1]
    finish_angle = math.atan2(dy_f, dx_f) + math.pi/2
    
    finish_pos = (p_finish[0], p_finish[1], finish_angle)
    
    # Boost zones? On verra plus tard
    
    return Track(
        start_pos=start_pos,
        start_heading=start_heading,
        finish_pos=finish_pos,
        checkpoints=checkpoints,
        collision_mask=collision_mask,
        occupancy_grid=occupancy_grid,
        visual_surface=None,  # peinte à la demande par src/game/track_art.py
        spline_points=np.array(spline_points), # Store raw points for alignment logic
        seed=seed, # Store the seed used for generation
        walls=[], # Pas de murs physiques explicites, le hors-piste est géré par mask
        boost_zones=[],
        half_width=float(half_width),
    )

def build_track(seed: int = 42) -> Track:
    """Wrapper pour conserver la compatibilité, mais appelle le procedural par défaut."""
    # Note: On utilise une seed fixe ici pour que 'manual play' soit constant au début
    # Mais le training pourra appeler generate_procedural_track(seed=None)
    return generate_procedural_track(seed=seed)
