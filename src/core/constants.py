
import math

# Window & Game
W, H = 1400, 1000
FPS = 50

# Physics constants
MAX_SPEED = 23.0  # ~ vitesse terminale ACCEL*FRICTION/(1-FRICTION)=22.32 (cf. docs/PHYSICS.md #1)
ACCEL = 0.18        # Reduced for smoother acceleration
BRAKE = 0.5
FRICTION = 0.992
COAST_FRICTION = 0.994  # roue libre : frein moteur léger (-26 % par seconde)
TURN_SPEED = 0.08       # vitesse de rotation max (rad/frame), plafond de sécurité
LATERAL_GRIP = 0.35     # part du glissement latéral rattrapée par frame (adhérence normale)
COLLISION_SPEED_LOSS = 0.9

# Direction façon Trackmania : la rotation vient du roulement (modèle bicyclette),
# donc rien à l'arrêt ; le braquage utile baisse avec la vitesse.
STEER_SPEED = 0.15          # montée du volant par frame (~7 frames pour braquer à fond)
STEER_CURVATURE = 0.010     # courbure max (1/px) à basse vitesse : rayon mini ~100 px
STEER_SPEED_SENS = 0.75     # perte de braquage à MAX_SPEED (0.75 = il en reste 25 %)
YAW_RESPONSE = 0.35         # vitesse à laquelle la rotation suit le volant (0-1 par frame)

# Marche arrière : frein maintenu à l'arrêt
REVERSE_ACCEL = 0.10
REVERSE_MAX = 5.0

# Drift : frein + braquage à vitesse élevée, l'adhérence chute tant qu'on braque
DRIFT_GRIP = 0.12
DRIFT_MIN_SPEED = 10.0
DRIFT_YAW_BOOST = 1.15      # la voiture pivote plus en drift
DRIFT_SCRUB = 0.006         # perte de vitesse par frame et par radian de glisse

# Murs : on glisse le long du mur, la perte dépend de l'angle d'impact
WALL_GRAZE_LOSS = 0.04      # perte minimale en frôlant
WALL_IMPACT_LOSS = 0.6      # perte supplémentaire, × sin²(angle d'impact)
WALL_BOUNCE = 0.15          # petite part de vitesse renvoyée vers la piste
WALL_ALIGN = 0.5            # part du cap réalignée sur le mur, × sin(angle d'impact)

# Track config
TRACK_WIDTH = 90
TRACK_OUTER_MARGIN = 40
TRACK_INNER_MARGIN = TRACK_OUTER_MARGIN + TRACK_WIDTH

CHECKPOINT_RADIUS = 100
FINISH_RADIUS = 100

# Fonts
FONT_SIZE = 24

# Colors
COLOR_GRASS = (34, 139, 34)       # Forest Green
COLOR_ROAD = (105, 105, 105)      # Dim Gray
COLOR_BORDER = (255, 255, 255)    # White
COLOR_CHECKPOINT = (255, 215, 0)  # Gold
