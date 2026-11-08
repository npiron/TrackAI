import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import os

from src.core.constants import W, H, FONT_SIZE, MAX_SPEED
from src.game.env import TimeAttackEnv
from src.game.track import build_track
from src.game.rendering import draw_track, draw_car, draw_ghost, draw_lidar

# Récompense "simple" (reward_mode="simple") : progression le long de la ligne centrale + temps + chocs
SIMPLE_LAP_REWARD = 100.0   # récompense de progression cumulée pour un tour de piste (k_prog = SIMPLE_LAP_REWARD / longueur de la ligne centrale)
SIMPLE_TIME_PENALTY = 0.01  # pénalité par pas
REWARD_MODES = ("legacy", "simple")


class GymTimeAttack(gym.Env):
    """
    Gym wrapper around TimeAttackEnv.

    Action: Discrete(9) - Complete on/off button controls
      0: Idle (no input)
      1: Accelerate
      2: Brake
      3: Left (steer only)
      4: Right (steer only)
      5: Left + Accelerate
      6: Right + Accelerate
      7: Left + Brake
      8: Right + Brake

    Obs: 14 floats (Pilot-Centric) ; obs_version=2 : 35 floats (voir TimeAttackEnv)
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, render_mode=None, procedural=True, laps=1, wall_fatal=False, wall_penalty=0.0, obs_version=1, track_variant=1,
                 reward_mode="legacy", k_prog=None, time_penalty=SIMPLE_TIME_PENALTY):
        super().__init__()
        if reward_mode not in REWARD_MODES:
            raise ValueError(f"reward_mode doit valoir l'un de {REWARD_MODES}")
        # reward_mode "simple" : k_prog * Δprogression - time_penalty + wall_penalty * nouveaux chocs (+ bonus de fin de l'env).
        # k_prog=None : SIMPLE_LAP_REWARD / longueur de la ligne centrale (un tour ≈ +SIMPLE_LAP_REWARD).
        self.reward_mode = reward_mode
        self._k_prog_arg = k_prog
        self.time_penalty = float(time_penalty)
        # Options d'entraînement (défaut : désactivées). wall_penalty : récompense ajoutée par choc (négative = pénalité).
        self.wall_fatal = bool(wall_fatal)
        self.wall_hit_penalty = float(wall_penalty)
        self.laps = max(1, int(laps))
        # Initialize with procedural config
        # If procedural=True, track=None (auto-gen). If False, we need a static track.
        if procedural:
            self.ta = TimeAttackEnv(track=None, procedural=True, laps=self.laps, obs_version=obs_version,
                                    track_variant=track_variant)
        else:
            self.ta = TimeAttackEnv(build_track(), procedural=False, laps=self.laps, obs_version=obs_version)

        # Obs: 14 floats (Pilot-Centric)
        # (obs_version=2 : 35 floats, voir TimeAttackEnv)
        n_obs = TimeAttackEnv.OBS_V2_SIZE if obs_version == 2 else 14
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(n_obs,), dtype=np.float32)
        # 9 Discrete Actions for Complete Arcade Control (on/off buttons)
        self.action_space = spaces.Discrete(9)

        self._last_progress = 0.0
        self.render_mode = render_mode
        self.screen = None
        self.clock = None
        self.font = None
        
        # Configurable Rewards
        self.config_path = os.environ.get("TRACKAI_REWARDS_CONFIG", "rewards_config.json")
        
        # Try to find process-specific config first
        self.pid = os.getpid()
        self.specific_config_path = f"rewards_config_{self.pid}.json"
        
        self.config_mtime = 0
        self.config = {
            "progress_weight": 4.0,
            "alignment_weight": 0.5,
            "checkpoint_bonus": 100.0,
            "speed_weight": 1.5,
            "track_penalty": 2.0,
            "wall_penalty": 3.0,
            "time_bonus": 200.0,
            "checkpoint_scaling": 0.0,
            "ghost_following_weight": 0.0
        }
        self._load_config()
        self.step_counter = 0

    def _load_config(self):
        try:
            import json
            import os
            
            # Determine which file to load
            target_path = self.config_path
            if os.path.exists(self.specific_config_path):
                target_path = self.specific_config_path
                
            if os.path.exists(target_path):
                mtime = os.stat(target_path).st_mtime
                if mtime > self.config_mtime:
                    with open(target_path, 'r') as f:
                        new_config = json.load(f)
                        self.config.update(new_config)
                    self.config_mtime = mtime
                    # minimal print to avoid spam
                    # print(f"Loaded rewards from {target_path}: {self.config}")
        except Exception as e:
            print(f"Error loading rewards config: {e}")

    def reset(self, seed=None, options=None):
        track_seed = (options or {}).get("track_seed")
        # This regenerates the track if procedural (track_seed fixes it)
        obs = self.ta.reset() if track_seed is None else self.ta.reset(track_seed=track_seed)
        
        # Calculate initial distance for progress tracking
        # We need raw distance to keep reward scale consistent
        next_obj = self.ta.track.checkpoints[0][:2]
        dx = next_obj[0] - self.ta.car.pos[0]
        dy = next_obj[1] - self.ta.car.pos[1]
        dist = np.sqrt(dx*dx + dy*dy)
        
        self._last_progress = -dist
        self._simple_s = self._centerline_s()
        self._last_lap_count = 0
        self._last_speed = 0.0
        self._last_cp_count = 0
        
        # Personal Best tracking logic
        # If procedural, PB is meaningless between episodes, so we set it to something high
        # But we might want "Session Best" for THIS track? No, track changes every reset.
        # So PB reward is disabled for procedural.
        if not hasattr(self, '_personal_best_time') or self.ta.procedural:
             self._personal_best_time = float('inf')
        
        # Trajectory recording for PB replay
        self._current_trajectory = []
        
        # Reset step counter for timeout
        self.episode_steps = 0
        
        # Reset wall-stuck detection
        self.wall_stuck_counter = 0
        
        self._load_config() # Reload on reset
        if self.render_mode == "human":
            self.render()
        return obs, {}

    def step(self, action):
        self.step_counter += 1
        self.episode_steps += 1
        
        # Timeout: Terminate episode after max steps (prevents infinite stuck episodes)
        # With larger tracks, we need more time, but not infinite
        # 2000 steps = 40 seconds at 50 FPS (enough for even long tracks)
        MAX_EPISODE_STEPS = 2000 * self.laps
        if self.episode_steps >= MAX_EPISODE_STEPS:
            # Force termination
            obs = self.ta._obs()
            info = {
                "checkpoints_reached": sum(self.ta.cp_visited),
                "is_success": False,
                "lap_time": 0.0
            }
            self._add_lap_info(info)
            info["end_cause"] = "timeout"
            return obs, -50.0, True, False, info  # Penalty for timeout
        if self.step_counter % 60 == 0:
            self._load_config()

        # Decode Discrete Action (Complete on/off button controls)
        # 0: Idle, 1: Acc, 2: Brake, 3: Left, 4: Right
        # 5: L+A, 6: R+A, 7: L+B, 8: R+B
        steer, accel, brake = 0.0, 0.0, 0.0
        if action == 1:
            accel = 1.0
        elif action == 2:
            brake = 1.0
        elif action == 3:
            steer = -1.0
        elif action == 4:
            steer = 1.0
        elif action == 5:
            steer = -1.0
            accel = 1.0
        elif action == 6:
            steer = 1.0
            accel = 1.0
        elif action == 7:
            steer = -1.0
            brake = 1.0
        elif action == 8:
            steer = 1.0
            brake = 1.0
            
        hits_before = self.ta.wall_hits
        obs, reward, done, info = self.ta.step((steer, accel, brake))
        new_hits = self.ta.wall_hits - hits_before

        # Extract Raw State for Reward Calculation (Observation agnostic)
        car = self.ta.car
        speed = max(0.0, car.speed) / MAX_SPEED  # [0, 1] ; la marche arrière ne rapporte rien
        on_track = 1.0 if self.ta.track.inside_track(car.pos) else 0.0
        
        # === WALL-STUCK DETECTION ===
        # If car is off-track AND nearly stationary for 3 seconds (150 frames @ 50 FPS), terminate
        # (T23) Arrêt prolongé n'importe où (y compris contre un mur "sur piste")
        if speed < 0.05:  # quasi immobile
            self.wall_stuck_counter += 1
        else:
            self.wall_stuck_counter = 0  # Reset if moving or back on track
        
        if self.wall_stuck_counter >= 150:  # 3 seconds stuck
            # Force termination with penalty
            obs = self.ta._obs()
            info = {
                "checkpoints_reached": sum(self.ta.cp_visited),
                "is_success": False,
                "lap_time": 0.0
            }
            self._add_lap_info(info)
            info["end_cause"] = "wall_stuck"
            return obs, -100.0, True, False, info  # Stuck penalty
        
        if self.wall_fatal and new_hits > 0:
            info = {
                "checkpoints_reached": sum(self.ta.cp_visited),
                "is_success": False,
                "lap_time": 0.0
            }
            self._add_lap_info(info)
            info["end_cause"] = "wall_fatal"
            return obs, -100.0, True, False, info

        # Record position for replay
        self._current_trajectory.append((float(car.pos[0]), float(car.pos[1])))
        
        if self.reward_mode == "simple":
            return self._simple_step(obs, reward, done, info, new_hits)

        # New lap just started: checkpoints were reset, target changed
        lap_started = self.ta.lap_count != self._last_lap_count
        self._last_lap_count = self.ta.lap_count

        # Find next checkpoint target
        next_obj = None
        for i, visited in enumerate(self.ta.cp_visited):
            if not visited:
                next_obj = self.ta.track.checkpoints[i][:2]
                break
        if next_obj is None:
            next_obj = self.ta.track.finish_pos[:2]
            
        dx = next_obj[0] - car.pos[0]
        dy = next_obj[1] - car.pos[1]
        dist = float(np.sqrt(dx*dx + dy*dy))
        
        # Velocity vector
        vx, vy = car.vel
        
        # === PRIORITY #1: CHECKPOINT PROGRESS ===
        
        # 1.1 Distance reduction
        progress = -dist
        progress_delta = 0.0 if lap_started else (progress - self._last_progress)
        progress_reward = progress_delta * self.config.get("progress_weight", 4.0)
        self._last_progress = progress
        
        # 1.2 Alignment (Centerline & Orientation)
        # New "Slot Car" Reward: Reward being parallel to track and centered
        alignment_reward = 0.0
        alignment = 0.0
        centering = 0.0
        
        try:
            # Get track info
            track_tangent, dist_to_center = self.ta.track.get_closest_track_info(car.pos)
            
            # Normalize velocity
            v_norm = np.linalg.norm([vx, vy])
            if v_norm > 0.1:
                v_dir = np.array([vx, vy]) / v_norm
                # Dot product: Cosine similarity
                # 1.0 = Parallel, 0.0 = Perpendicular, -1.0 = Wrong way
                alignment = float(np.dot(v_dir, track_tangent))
            
            # Centering factor (Road radius is ~60)
            # 1.0 at center, 0.0 at edge
            centering = max(0.0, 1.0 - (dist_to_center / getattr(self.ta.track, 'half_width', 60.0)))
            
            # Combine: Must be aligned AND centered to get points
            # IMPORTANT: Punish going backwards HEAVILY
            if alignment < -0.1:  # Going backwards (more than 90° wrong)
                # Severe penalty for wrong-way driving
                alignment_reward = -10.0 * abs(alignment)
            elif alignment < 0:  # Slightly wrong direction
                # Small penalty
                alignment_reward = -2.0 * abs(alignment)
            else:  # Correct direction
                # Normal reward: aligned AND centered
                raw_align_score = alignment * centering
                alignment_reward = raw_align_score * self.config.get("alignment_weight", 0.5)
            
        except Exception as e:
            # Fallback if track logic fails
            pass
        
        # 1.3 Checkpoint Bonus
        current_cp_count = sum(self.ta.cp_visited)
        if not hasattr(self, '_last_cp_count'):
            self._last_cp_count = 0
        
        checkpoint_bonus = 0.0
        if current_cp_count > self._last_cp_count:
            base_bonus = self.config.get("checkpoint_bonus", 100.0)
            
            # PROGRESSIVE SCALING: "Plus tu vas loin, plus c'est motivant"
            scaling = self.config.get("checkpoint_scaling", 0.0)
            multiplier = 1.0 + (current_cp_count * scaling)
            
            checkpoint_bonus = base_bonus * multiplier
            
            if speed > 0.5:
                checkpoint_bonus += 50.0 
        self._last_cp_count = current_cp_count
        
        # === PRIORITY #2: SPEED & TRACK ===
        
        # 2.1 Speed bonus (on track)
        speed_reward = 0.0
        if on_track > 0.5:
            # Power law makes high speed much more valuable
            w = self.config.get("speed_weight", 1.5)
            speed_reward = (speed ** 1.5) * w
            if alignment > 0.1:
                speed_reward += 0.5 
        
        # 2.2 Urgency
        urgency_penalty = 0.0
        if dist > 0.3 and speed < 0.2:
             urgency_penalty = -self.config.get("urgency_penalty", 0.3)
        
        # === PRIORITY #3: STAY ON TRACK ===
        
        # 3.1 Off-track penalty
        track_penalty = 0.0
        if on_track < 0.5:
            track_penalty = -self.config.get("track_penalty", 2.0)
        else:
            track_penalty = self.config.get("on_track_bonus", 0.0)
        
        # 3.2 Wall collision
        wall_penalty = 0.0
        if hasattr(self, '_last_speed'):
            speed_drop = self._last_speed - speed
            if speed_drop > 0.3:
                wall_penalty = -self.config.get("wall_penalty", 3.0)
        self._last_speed = speed
        
        # === BONUS: GHOST FOLLOWING (Static Tracks Only) ===
        ghost_following_reward = 0.0
        
        # Only reward ghost following on static tracks with a PB
        if not self.ta.procedural and self.ta.best_ghost and len(self.ta.best_ghost) > 10:
            ghost_weight = self.config.get("ghost_following_weight", 0.0)
            
            if ghost_weight > 0:
                # Find closest point on best_ghost trajectory
                ghost_points = np.array(self.ta.best_ghost)
                car_pos = np.array([car.pos[0], car.pos[1]])
                
                # Calculate distances to all ghost points
                distances = np.linalg.norm(ghost_points - car_pos, axis=1)
                min_dist = float(np.min(distances))
                
                # Reward being close to the optimal line
                # Exponential decay: very close = high reward, far = low reward
                # Max distance we care about: 50 pixels
                proximity_factor = np.exp(-min_dist / 30.0)  # Decay constant = 30px
                ghost_following_reward = proximity_factor * ghost_weight
        
        # === BONUS: FINISH TIME ===
        time_bonus = 0.0
        pb_improvement_bonus = 0.0
        
        if done and self.ta.lap_count >= self.laps:
            lap_time = self.ta.t
            base_bonus = self.config.get("time_bonus", 200.0)
            time_bonus = max(0, base_bonus - lap_time * 2)
            
            # PERSONAL BEST REWARD (CAPPED to prevent NaN)
            # Only valid for fixed tracks, not procedural
            if not self.ta.procedural and lap_time < self._personal_best_time:
                time_improvement = self._personal_best_time - lap_time
                # Chaque centième compte, mais on limite à 200 max
                pb_improvement_bonus = min(200, time_improvement * 50)  # 50 points/sec, max 200
                self._personal_best_time = lap_time
                
                # SAVE REPLAY
                import json
                import os
                os.makedirs("replays", exist_ok=True)
                replay_data = {
                    "time": lap_time,
                    "trajectory": self._current_trajectory,
                    "timestamp": __import__('time').time(),
                    "track_seed": self.ta.track.seed
                }
                with open("replays/personal_best.json", "w") as f:
                    json.dump(replay_data, f)
                
                print(f"🏆 NEW PB: {lap_time:.2f}s (-{time_improvement:.2f}s) +{pb_improvement_bonus:.0f} pts | 📹 Replay saved!")
        
        shaped_reward = (
            progress_reward +
            alignment_reward +
            checkpoint_bonus +
            speed_reward +
            urgency_penalty +
            track_penalty +
            wall_penalty +
            ghost_following_reward +
            time_bonus +
            pb_improvement_bonus  # NOUVEAU !
        )
        
        total_reward = float(reward + shaped_reward + self.wall_hit_penalty * new_hits)
        # Décomposition de la récompense (diagnostic) ; la somme vaut total_reward
        info["reward_components"] = {
            "progress": float(progress_reward),
            "alignment": float(alignment_reward),
            "checkpoint": float(checkpoint_bonus),
            "speed": float(speed_reward),
            "urgency": float(urgency_penalty),
            "track": float(track_penalty),
            "wall": float(wall_penalty + self.wall_hit_penalty * new_hits),
            "ghost": float(ghost_following_reward),
            "time_bonus": float(time_bonus + pb_improvement_bonus),
            "env": float(reward),
        }

        if self.render_mode == "human":
            self.render()

        info["checkpoints_reached"] = current_cp_count
        info["is_success"] = bool(done and self.ta.lap_count >= self.laps)
        info["lap_time"] = self.ta.t if info["is_success"] else 0.0
        self._add_lap_info(info)
             
        terminated = bool(done)
        truncated = False
        return obs, total_reward, terminated, truncated, info

    def _centerline_s(self):
        """Abscisse curviligne (px) du point de la ligne centrale le plus proche de la voiture."""
        sp = self.ta.track.spline_points
        cum = self.ta._arc_lengths()
        i = int(np.argmin(np.sum((sp - np.asarray(self.ta.car.pos, dtype=np.float64)) ** 2, axis=1)))
        return float(cum[i])

    def _simple_step(self, obs, reward, done, info, new_hits):
        """Récompense simple : pas de terme hérité (alignement, vitesse, fantôme, urgence, checkpoints)."""
        total_len = float(self.ta._arc_lengths()[-1])
        k_prog = self._k_prog_arg if self._k_prog_arg is not None else SIMPLE_LAP_REWARD / total_len
        s = self._centerline_s()
        ds = s - self._simple_s
        ds = (ds + total_len / 2) % total_len - total_len / 2  # bouclage : le plus court écart signé
        self._simple_s = s
        if not self.ta.track.inside_track(self.ta.car.pos):
            ds = 0.0  # pas de récompense hors piste
        progress = k_prog * ds
        wall = self.wall_hit_penalty * new_hits
        total_reward = float(progress - self.time_penalty + wall + reward)
        info["reward_components"] = {
            "progress": float(progress), "time_penalty": float(-self.time_penalty),
            "wall": float(wall), "env": float(reward),
        }
        if self.render_mode == "human":
            self.render()
        info["checkpoints_reached"] = sum(self.ta.cp_visited)
        info["is_success"] = bool(done and self.ta.lap_count >= self.laps)
        info["lap_time"] = self.ta.t if info["is_success"] else 0.0
        self._add_lap_info(info)
        return obs, total_reward, bool(done), False, info

    def _add_lap_info(self, info):
        info["laps_done"] = self.ta.lap_count
        info["lap_times"] = list(self.ta.lap_times)
        info["total_time"] = float(sum(self.ta.lap_times))
        info["wall_hits"] = int(self.ta.wall_hits)
        info["wall_contacts"] = int(self.ta.wall_contacts)

    def render(self):
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((W, H))
            pygame.display.set_caption("Trackmania Clone - Training Preview")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("Menlo", FONT_SIZE)

        # Draw content
        screen = self.screen
        track = self.ta.track
        env = self.ta
        
        # Process events to keep window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # We can't really quit here without killing the env process
                pass

        draw_track(screen, track)
        
        # Highlight checkpoints based on visited status
        # Visited = Green, Unvisited = Gold
        for i, (cx, cy, angle) in enumerate(track.checkpoints):
            visited = env.cp_visited[i]
            color = (0, 255, 0) if visited else (255, 215, 0)  # Green or Gold
            
            # Draw checkpoint circle to show status
            pygame.draw.circle(screen, color, (int(cx), int(cy)), 15, width=3)
        
        if env.best_time is not None:
             draw_ghost(screen, env.best_ghost, color=(70, 160, 220))
        draw_ghost(screen, env.ghost[-400:], color=(90, 90, 120))
        draw_car(screen, env.car)
        
        # Draw LIDAR if available
        if hasattr(env, 'lidar_dist'):
            draw_lidar(screen, env.car, env.lidar_dist)
        
        pygame.display.flip()
