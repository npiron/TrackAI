
import math
import numpy as np
import random
from typing import Optional, List, Tuple

from src.core.constants import *
from src.game.track import Track, generate_procedural_track
from src.game.car import Car
from src.game.physics import drive
from src.utils.math_utils import vec
from src.utils.jit_ops import cast_rays_jit

class TimeAttackEnv:
    """
    Minimal env:
      obs = 14 floats (Pilot-Centric):
            [speed_n, local_vx, local_vy, ang_vel, prev_steer, 
             target_dist, target_dir_x, target_dir_y, on_track, 
             lidar_1, lidar_2, lidar_3, lidar_4, lidar_5]
      action = (steer, accel, brake) in [-1..1], [0..1], [0..1]

    obs_version=2 : 44 floats (v1 inchangée par défaut) :
      0-8   : identiques à v1 (speed_n, local_vx, local_vy, ang_vel, prev_steer,
              target_dist, target_dir_x, target_dir_y, on_track)
      9     : car.steering (position réelle du volant, [-1, 1])
      10-33 : 8 points de la ligne centrale à venir, à V2_POINT_DISTANCES px d'arc (serrés près de la
              voiture, jusqu'à 560 px : la distance de freinage depuis la vitesse max), 3 valeurs chacun
              dans le repère de la voiture : distance normalisée [0,1], sin, cos de l'angle
              (cos>0 : devant, sin>0 : à droite)
      34    : courbure à venir (changement de cap moyen entre points, / (pi/4), clip [-1, 1], >0 : à droite)
      35-43 : 9 lidars (-pi/2 à pi/2 par pas de pi/8), portée V2_RAY_LENGTH px, normalisés [0,1]

    obs_version=3 : 50 floats = v2 + 6 :
      44    : écart latéral à la ligne centrale / demi-largeur de route (>0 : à droite, ±1 : bord), clip [-1.5, 1.5]
      45-47 : virage proche (0-150 px), moyen (150-300 px), lointain (300-560 px) : changement de cap
              cumulé / (pi/2), clip [-1, 1], >0 : à droite (pour savoir quand freiner)
      48    : en drift (0/1)
      49    : angle de glisse (entre la vitesse et le cap) / (pi/4), clip [-1, 1]
    ta.obs_v1() renvoie toujours l'observation v1 courante (pour le professeur heuristique).
    """
    V2_POINT_DISTANCES = (30.0, 60.0, 100.0, 150.0, 220.0, 300.0, 420.0, 560.0)
    V2_RAY_LENGTH = 400.0
    V2_LIDAR_ANGLES = [-math.pi / 2 + i * math.pi / 8 for i in range(9)]
    OBS_V2_SIZE = 10 + 3 * len(V2_POINT_DISTANCES) + 1 + 9
    OBS_V3_SIZE = OBS_V2_SIZE + 6

    def __init__(self, track: Optional[Track] = None, procedural: bool = True, laps: int = 1, obs_version: int = 1,
                 track_variant: int = 1):
        if obs_version not in (1, 2, 3):
            raise ValueError("obs_version doit valoir 1, 2 ou 3")
        self.obs_version = obs_version
        self.track_variant = int(track_variant)  # 1 : tracé historique, 2 : circuits longs (src/game/track.py)
        self._arc_cache = None
        self.laps = max(1, int(laps))
        self.lap_count = 0
        self.lap_times: List[float] = []
        self._lap_start_t = 0.0
        self.procedural = procedural
        if track:
            self.track = track
            self.procedural = False # Force static if track provided explicitly
        else:
            self.track = generate_procedural_track(variant=self.track_variant)
            
        self.car: Optional[Car] = None

        self.t = 0.0
        self.done = False

        self.best_time: Optional[float] = None
        self.best_ghost: List[Tuple[float, float]] = []

        self.ghost: List[Tuple[float, float]] = []
        self.cp_visited = [False] * len(self.track.checkpoints)
        self.off_track_counter = 0  # NEW: Track how long car is off-road

        self.reset()

    def reset(self, track_seed: Optional[int] = None):
        # Regenerate track if procedural mode is active (track_seed fixes it)
        if self.procedural:
            self.track = generate_procedural_track(seed=track_seed, variant=self.track_variant)
            self.best_time = None   # nouveau circuit : le fantôme du meilleur tour ne vaut plus
            self.best_ghost = []
            # print(f"DEBUG: Track generated with {len(self.track.checkpoints)} CPs")
            
        sx, sy = self.track.start_pos
        self.car = Car(
            pos=vec(sx, sy),
            vel=vec(0, 0),
            heading=self.track.start_heading,
            speed=0.0
        )
        self.t = 0.0
        self.done = False
        self.lap_count = 0
        self.lap_times = []
        self._lap_start_t = 0.0
        self.cp_visited = [False] * len(self.track.checkpoints)
        self.ghost = []
        self.off_track_counter = 0  # Reset timeout counter
        self.prev_steer = 0.0       # Track previous action
        self.wall_hits = 0          # pas avec choc mur (new_pos hors piste)
        self.wall_contacts = 0      # nouveaux contacts (pas précédent sans choc)
        self._wall_prev = False
        self._frames_since_wall = 10**6
        
        return self._obs()

    def step(self, action: Tuple[float, float, float]):
        # action: steer, accel, brake
        steer, accel, brake = action
        steer = float(np.clip(steer, -1.0, 1.0))
        accel = float(np.clip(accel, 0.0, 1.0))
        brake = float(np.clip(brake, 0.0, 1.0))
        
        # ========== PHYSIQUE (inspirée de Trackmania, voir src/game/physics.py) ==========
        car = self.car
        car.vel, car.heading, car.steering, car.angular_velocity, car.is_drifting = drive(
            car.vel, car.heading, car.steering, car.angular_velocity, car.is_drifting, steer, accel, brake)
        car.speed = float(car.vel @ np.array([math.cos(car.heading), math.sin(car.heading)]))
        self.prev_steer = steer
        car.braking = bool(brake > 0 and car.speed > 0.5)

        # 6. Position et murs : on glisse le long du mur, perte selon l'angle d'impact
        new_pos = car.pos + car.vel
        wall_now = False
        if self.track.inside_track(new_pos):
            car.pos = new_pos
            self.off_track_counter = 0
        else:
            self.wall_hits += 1
            if not self._wall_prev:
                self.wall_contacts += 1
            wall_now = True
            inward = self._wall_normal(car.pos)          # normale locale, vers la piste
            tangent = np.array([-inward[1], inward[0]])
            norm_v = float(np.linalg.norm(car.vel))
            v_t = float(car.vel @ tangent)
            impact = math.sqrt(max(0.0, 1.0 - (v_t / norm_v) ** 2)) if norm_v > 1e-6 else 0.0
            first = self._frames_since_wall > WALL_CONTACT_GAP
            keep = 1.0 - (WALL_HIT_LOSS if first else WALL_RUB_LOSS) - WALL_IMPACT_LOSS * impact * impact
            self._frames_since_wall = 0
            car.vel = tangent * v_t * max(0.0, keep) + inward * norm_v * impact * WALL_BOUNCE
            # le choc remet en partie la caisse dans l'axe du mur (comme dans Trackmania) ;
            # on prend le sens du mur le plus proche du cap, pour ne jamais rester planté de face
            along = math.atan2(tangent[1], tangent[0])
            diff = (along - car.heading + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) > math.pi / 2:
                diff = (diff + 2 * math.pi) % (2 * math.pi) - math.pi
            nose_in = max(impact, 1.0 - min(norm_v / 2.0, 1.0))  # quasi à l'arrêt contre le mur
            car.heading += diff * WALL_ALIGN * nose_in
            car.angular_velocity *= 1.0 - nose_in
            # glisser le long du mur ; le masque est au pixel près, donc on se décolle d'1 px si besoin
            for push in (0.0, 1.0, 2.0):
                moved = car.pos + car.vel + inward * push
                if self.track.inside_track(moved):
                    car.pos = moved
                    break
            else:
                car.vel = np.zeros(2)
            self.off_track_counter = 0
            car.speed = float(car.vel @ np.array([math.cos(car.heading), math.sin(car.heading)]))

        self._wall_prev = wall_now
        if not wall_now:
            self._frames_since_wall += 1

        # 4b. Check screen boundaries (backup safety)
        if self.track.hits_wall(self.car.pos):
            self.car.vel *= 0.3
            self.car.speed *= 0.3
            self.car.pos[0] = max(5, min(W - 5, self.car.pos[0]))
            self.car.pos[1] = max(5, min(H - 5, self.car.pos[1]))
        
        # 4c. BOOST ZONES - Speed boost!
        if self.track.on_boost(self.car.pos):
            norm_v = float(np.linalg.norm(self.car.vel))
            if norm_v > 1e-6:
                boosted = min(norm_v * 1.15, MAX_SPEED * 1.2)  # +15 %, plafond 120 %
                self.car.vel *= boosted / norm_v
                self.car.speed *= boosted / norm_v
        
        # 4d. DRIFT MECHANICS
        # Calculate drift angle (difference between heading and velocity direction)
        if self.car.speed > 0.1:
            vel_angle = np.arctan2(self.car.vel[1], self.car.vel[0])
            drift_angle = abs(self.car.heading - vel_angle)
            # Normalize to [0, pi]
            while drift_angle > np.pi:
                drift_angle -= 2 * np.pi
            drift_angle = abs(drift_angle)
            
            # Drifting if angle > 15° and turning
            is_drifting = drift_angle > 0.26 and abs(self.car.angular_velocity) > 0.01  # 15 degrees
            
            # Track max speed
            if not hasattr(self.car, 'max_speed_reached'):
                self.car.max_speed_reached = 0.0
            self.car.max_speed_reached = max(self.car.max_speed_reached, self.car.speed)

        # 5. Checkpoints
        self._update_checkpoints()
        
        # 6. Finish
        lap_finished = False
        if self._check_finish():
            # Time at the end of this frame (same clock as the single-lap case)
            t_end = self.t + 1.0 / FPS
            self.lap_times.append(t_end - self._lap_start_t)
            self.lap_count += 1
            if self.lap_count < self.laps:
                # Next lap: checkpoints must be validated again
                lap_finished = True
                self._lap_start_t = t_end
                self.cp_visited = [False] * len(self.track.checkpoints)
            else:
                self.done = True
                if self.best_time is None or self.t < self.best_time:
                    self.best_time = self.t
                    self.best_ghost = list(self.ghost)

        # Record ghost
        if len(self.ghost) == 0 or np.linalg.norm(self.car.pos - vec(*self.ghost[-1])) > 5.0:
            self.ghost.append((self.car.pos[0], self.car.pos[1]))

        # Time
        self.t += 1.0 / FPS

        reward = 0.0
        # If done (win) -> Big Reward?
        # Typically handled in wrapper.
        if self.done or lap_finished:
            reward = 100.0

        return self._obs(), reward, self.done, {}

    _WALL_DIRS = [np.array([math.cos(a), math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]

    def _wall_normal(self, pos: np.ndarray) -> np.ndarray:
        """Normale du mur au point de contact, orientée vers la piste (lue dans le masque de collision)."""
        acc = np.zeros(2)
        for r in (4.0, 8.0):
            for d in self._WALL_DIRS:
                if self.track.inside_track(pos + d * r):
                    acc += d
        n = float(np.linalg.norm(acc))
        if n > 1e-6:
            return acc / n
        pts = self.track.spline_points
        to_c = pts[int(np.argmin(np.sum((pts - pos) ** 2, axis=1)))] - pos
        n = float(np.linalg.norm(to_c))
        return to_c / n if n > 1e-6 else np.zeros(2)

    def _update_checkpoints(self):
        # We need to enforce order? 
        # Yes, usually CP 1 then 2...
        # Next expected CP index
        next_cp_idx = 0
        for i, visited in enumerate(self.cp_visited):
            if not visited:
                next_cp_idx = i
                break
        else:
            # All visited
            return

        # la porte est franchie quand le pare-chocs avant touche sa ligne (et pas à 100 px avant)
        cx, cy, ang = self.track.checkpoints[next_cp_idx]
        if isinstance(ang, str):  # anciens circuits fixes : porte horizontale/verticale
            ang = math.pi / 2 if ang == 'V' else 0.0
        tx, ty = self._cp_direction(next_cp_idx, cx, cy, ang)
        rel = self.car.pos - vec(cx, cy)
        along = float(rel[0] * tx + rel[1] * ty)
        across = float(rel[0] * math.cos(ang) + rel[1] * math.sin(ang))
        half = getattr(self.track, "half_width", 60.0) + 10.0
        nose = CAR_NOSE * max(0.0, math.cos(self.car.heading - math.atan2(ty, tx)))
        if -CHECKPOINT_RADIUS < along + nose and along + nose >= 0.0 and abs(across) <= half:
            self.cp_visited[next_cp_idx] = True

    def _cp_direction(self, i, cx, cy, ang):
        """Sens de la course au niveau de la porte i (perpendiculaire à la porte, orienté comme la piste)."""
        cache = getattr(self, "_cp_dir_cache", None)
        if cache is None or cache[0] is not self.track:
            cache = (self.track, {})
            self._cp_dir_cache = cache
        if i not in cache[1]:
            tx, ty = -math.sin(ang), math.cos(ang)
            sp = getattr(self.track, "spline_points", None)
            if sp is not None and len(sp) > 2:
                sp = np.asarray(sp)
                j = int(np.argmin(np.sum((sp - np.array([cx, cy])) ** 2, axis=1)))
                d = sp[(j + 1) % len(sp)] - sp[j]
                if d[0] * tx + d[1] * ty < 0:
                    tx, ty = -tx, -ty
            else:
                # sans tracé : on s'oriente vers la porte suivante (ou l'arrivée)
                nxt = self.track.checkpoints[i + 1][:2] if i + 1 < len(self.track.checkpoints) else self.track.finish_pos[:2]
                if (nxt[0] - cx) * tx + (nxt[1] - cy) * ty < 0:
                    tx, ty = -tx, -ty
            cache[1][i] = (tx, ty)
        return cache[1][i]

    def _check_finish(self) -> bool:
        if not all(self.cp_visited):
            return False
        
        # la voiture doit franchir la ligne (son centre passe sur le damier), pas seulement s'en approcher
        fx, fy, fang = self.track.finish_pos
        rel = self.car.pos - vec(fx, fy)
        along = float(rel[0] * math.sin(fang) - rel[1] * math.cos(fang))   # sens de la course
        across = float(rel[0] * math.cos(fang) + rel[1] * math.sin(fang))  # en travers de la route
        half = getattr(self.track, "half_width", 60.0) + 10.0
        return 0.0 <= along < FINISH_RADIUS and abs(across) <= half

    def obs_v1(self):
        """Observation v1 (14 valeurs) courante, quelle que soit obs_version."""
        return self._obs_v1()

    def _obs(self):
        if self.obs_version == 3:
            return self._obs_v3()
        if self.obs_version == 2:
            return self._obs_v2()
        return self._obs_v1()

    def _obs_v3(self):
        v2 = self._obs_v2()
        i0, dh = self._v2_ctx
        sp = self.track.spline_points
        n = len(sp)
        a, b = sp[i0], sp[(i0 + 1) % n]
        t = b - a
        tl = math.hypot(t[0], t[1]) or 1.0
        rel = np.asarray(self.car.pos, dtype=np.float64) - a
        lateral = (t[0] * rel[1] - t[1] * rel[0]) / tl  # >0 : à droite de la ligne centrale (repère écran, y vers le bas)
        half = float(getattr(self.track, "half_width", 60.0))
        offset = float(np.clip(lateral / half, -1.5, 1.5))
        bends = [float(np.clip(np.sum(dh[sl]) / (math.pi / 2), -1.0, 1.0))
                 for sl in (slice(0, 3), slice(3, 5), slice(5, None))]
        vx, vy = float(self.car.vel[0]), float(self.car.vel[1])
        if math.hypot(vx, vy) > 0.5:
            h = self.car.heading
            v_long = vx * math.cos(h) + vy * math.sin(h)
            v_lat = -vx * math.sin(h) + vy * math.cos(h)
            slip = math.atan2(v_lat, abs(v_long))
        else:
            slip = 0.0
        extra = [offset, *bends, 1.0 if self.car.is_drifting else 0.0,
                 float(np.clip(slip / (math.pi / 4), -1.0, 1.0))]
        return np.concatenate([v2, np.array(extra, dtype=np.float32)])

    def _arc_lengths(self):
        sp = self.track.spline_points
        if self._arc_cache is None or self._arc_cache[0] is not sp:
            seg = np.linalg.norm(np.roll(sp, -1, axis=0) - sp, axis=1)
            cum = np.concatenate(([0.0], np.cumsum(seg)))  # cum[-1] = longueur totale (boucle fermée)
            self._arc_cache = (sp, cum)
        return self._arc_cache[1]

    def _obs_v2(self):
        base = self._obs_v1()[:9]
        sp = self.track.spline_points
        cum = self._arc_lengths()
        total = float(cum[-1])
        n = len(sp)
        pos = np.asarray(self.car.pos, dtype=np.float64)
        i0 = int(np.argmin(np.sum((sp - pos) ** 2, axis=1)))
        h = self.car.heading
        ch, sh = math.cos(h), math.sin(h)
        pts = []
        for dist_ahead in self.V2_POINT_DISTANCES:
            target = (cum[i0] + dist_ahead) % total
            j = int(np.searchsorted(cum[:-1], target, side="right") - 1) % n
            pts.append(sp[j])
        pts = np.array(pts, dtype=np.float64)
        feats = []
        for p in pts:
            dx, dy = p[0] - pos[0], p[1] - pos[1]
            lx = dx * ch + dy * sh
            ly = -dx * sh + dy * ch
            d = math.hypot(lx, ly)
            dn = min(1.0, d / (self.V2_POINT_DISTANCES[-1] * 1.25))
            ang = math.atan2(ly, lx)
            feats += [dn, math.sin(ang), math.cos(ang)]
        chain = np.vstack([sp[i0][None, :], pts])
        seg = np.diff(chain, axis=0)
        heads = np.arctan2(seg[:, 1], seg[:, 0])
        dh = (np.diff(heads) + math.pi) % (2 * math.pi) - math.pi
        curv = float(np.clip(np.mean(dh) / (math.pi / 4), -1.0, 1.0))
        self._v2_ctx = (i0, dh)  # réutilisé par l'observation v3
        lidar = self._cast_rays(self.V2_LIDAR_ANGLES, self.V2_RAY_LENGTH)
        return np.array([*base, float(self.car.steering), *feats, curv, *lidar], dtype=np.float32)

    def _obs_v1(self):
        # PILOT-CENTRIC OBSERVATION (Local Coordinates)
        # We want the AI to learn "Driving", not "Map Memorization".
        
        # 1. Car Physics State
        speed_n = self.car.speed / MAX_SPEED
        
        # Local Velocity (Body Frame)
        # Project global velocity onto car's heading vectors
        head_x = math.cos(self.car.heading)
        head_y = math.sin(self.car.heading)
        
        # Global vel
        vx, vy = self.car.vel
        
        # Dot product
        # Forward vel: vel dot heading
        local_vx = (vx * head_x + vy * head_y) / MAX_SPEED
        # Lateral vel (Drift): vel dot (heading rotated 90 deg)
        # Rotated 90 deg vector is (-head_y, head_x)
        local_vy = (vx * -head_y + vy * head_x) / MAX_SPEED
        
        # Angular Velocity & Action History
        ang_vel = self.car.angular_velocity
        prev_steer = self.prev_steer
        # 2. Navigation (Next Checkpoint/Finish)
        next_obj = None
        for i, visited in enumerate(self.cp_visited):
            if not visited:
                next_obj = self.track.checkpoints[i][:2]
                break
        
        if next_obj is None:
            next_obj = self.track.finish_pos[:2]
            
        # Global vector to target
        tx, ty = next_obj
        dx_global = tx - self.car.pos[0]
        dy_global = ty - self.car.pos[1]
        
        dist = math.sqrt(dx_global**2 + dy_global**2)
        dist_n = min(1.0, dist / (W * 1.4)) # Normalize by approximate max diagonal
        
        # Local vector to target (Rotate global vector by -heading)
        # x' = x cos(-h) - y sin(-h)
        # y' = x sin(-h) + y cos(-h)
        # cos(-h) = cos(h), sin(-h) = -sin(h)
        
        target_local_x = dx_global * head_x + dy_global * head_y  # Forward distance
        target_local_y = -dx_global * head_y + dy_global * head_x # Rightward distance
        
        # Normalize target direction (Unit vector pointing to target in local frame)
        if dist > 0.1:
            tgt_dir_x = target_local_x / dist
            tgt_dir_y = target_local_y / dist
        else:
            tgt_dir_x, tgt_dir_y = 1.0, 0.0
            
        on_track = 1.0 if self.track.inside_track(self.car.pos) else 0.0

        # === LIDAR SENSORS ===
        lidar_readings = self._cast_rays([
            -math.pi/2, 
            -math.pi/4, 
            0, 
            math.pi/4, 
            math.pi/2
        ])
        
        # Store for rendering
        self.lidar_dist = lidar_readings
        
        # TOTAL SIZE: 
        # 0: Speed
        # 1: Local Vx (Forward)
        # 2: Local Vy (Lateral Drift)
        # 3: Angular Vel
        # 4: Prev Steer
        # 5: Target Dist
        # 6: Target Dir X (Forward)
        # 7: Target Dir Y (Right)
        # 8: On Track
        # 9-13: LIDAR (5)
        # = 14 Floats

        return np.array([
            speed_n,
            local_vx,
            local_vy,
            ang_vel,
            prev_steer,
            dist_n,
            tgt_dir_x,
            tgt_dir_y,
            on_track,
            *lidar_readings
        ], dtype=np.float32)

    def _cast_rays(self, angles: List[float], ray_length: float = 150.0) -> List[float]:
        """
        Cast rays from car center to detect wall/track boundaries.
        Optimized using Numba JIT.
        """
        RAY_LENGTH = ray_length # pixels (v1 : 150)
        
        # Prepare inputs for JIT
        px, py = self.car.pos
        h = self.car.heading
        
        # Convert angles to numpy array
        angles_np = np.array(angles, dtype=np.float32)
        
        # Call JIT function
        # This will be compiled on first run (might lag for 0.5s once)
        readings = cast_rays_jit(
            float(px), float(py), float(h),
            angles_np,
            float(RAY_LENGTH),
            self.track.occupancy_grid
        )
            
        return readings.tolist()

