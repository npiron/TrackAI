
import math

# Window & Game
W, H = 1400, 1000
FPS = 50

# Physics constants
MAX_SPEED = 12.7  # vitesse terminale ACCEL*FRICTION/(1-FRICTION) = 12.4 px/frame (~620 px/s), à l'échelle des circuits
ACCEL = 0.122       # poussée douce : 50 % de la vitesse max en ~1,3 s, 90 % en ~4,2 s
BRAKE = 0.16        # freinage progressif : de la vitesse max à l'arrêt en ~1,5 s
FRICTION = 0.9903   # traînée en accélération ; vitesse terminale = 0.122*0.9903/0.0097 = 12.4 (allonge en fond de rapport)
COAST_FRICTION = 0.985  # roue libre : frein moteur net (-53 % par seconde), il faut tenir l'accélérateur
TURN_SPEED = 0.14       # vitesse de rotation max (rad/frame), plafond de sécurité
LATERAL_GRIP = 0.35     # part du glissement latéral rattrapée par frame (adhérence normale)
COLLISION_SPEED_LOSS = 0.9

# Direction façon Trackmania : la rotation vient du roulement (modèle bicyclette),
# donc rien à l'arrêt ; le braquage utile baisse avec la vitesse.
STEER_SPEED = 0.15          # montée du volant par frame (~7 frames pour braquer à fond)
STEER_CURVATURE = 0.016     # courbure max (1/px) à basse vitesse : rayon mini ~62 px
STEER_SPEED_SENS = 0.4      # perte de braquage à MAX_SPEED (il en reste 60 % : rayon ~105 px à fond)
YAW_RESPONSE = 0.35         # vitesse à laquelle la rotation suit le volant (0-1 par frame)

# Marche arrière : frein maintenu à l'arrêt
REVERSE_ACCEL = 0.08
REVERSE_MAX = 3.5

# Drift : frein + braquage à vitesse élevée, l'adhérence chute tant qu'on braque
DRIFT_GRIP = 0.03            # la glisse se résorbe lentement : on reste en travers
DRIFT_MIN_SPEED = 4.1       # drift possible un peu plus tôt
DRIFT_YAW_BOOST = 1.65      # la voiture pivote plus en drift
DRIFT_TURN_SPEED = 0.165    # rotation max en drift (hors drift : TURN_SPEED)
DRIFT_MAX_SLIP = 1.1        # rad (~63°) : au-delà l'adhérence revient (pas de tête-à-queue)
DRIFT_SCRUB = 0.0025        # perte de vitesse par frame et par radian de glisse
DRIFT_STEER_IN = 0.26       # braquage mini pour lancer un drift (coup de frein)
DRIFT_STEER_OUT = 0.15      # le drift tient tant qu'on braque au-delà
DRIFT_AUTO_STEER = 0.92     # sans frein : braquer presque à fond...
DRIFT_AUTO_SPEED = 0.75     # ... au-dessus de 75 % de la vitesse max fait décrocher l'arrière

# Murs : on glisse le long du mur ; toucher un mur coûte vraiment de la vitesse
WALL_HIT_LOSS = 0.15        # perte au premier contact (frôlement)
WALL_RUB_LOSS = 0.04        # perte par frame tant que le contact continue
WALL_CONTACT_GAP = 10       # un contact à moins de 10 frames du précédent prolonge le même contact
WALL_IMPACT_LOSS = 0.85     # perte en plus, × sin²(angle d'impact) : de face, presque tout
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
