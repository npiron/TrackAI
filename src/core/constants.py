
import math

# Window & Game
W, H = 1400, 1000
FPS = 50

# Physics constants
MAX_SPEED = 13.7  # vitesse terminale ACCEL*FRICTION/(1-FRICTION) = 13.4 px/frame (~670 px/s)
ACCEL = 0.137       # poussée : +12 % (voiture plus puissante)
BRAKE = 0.16        # freinage progressif : de la vitesse max à l'arrêt en ~1,5 s
FRICTION = 0.9899   # traînée en accélération ; vitesse terminale = 0.137*0.9899/0.0101 = 13.4
COAST_FRICTION = 0.985  # roue libre : frein moteur net (-53 % par seconde), il faut tenir l'accélérateur
TURN_SPEED = 0.14       # vitesse de rotation max (rad/frame), plafond de sécurité
LATERAL_GRIP = 0.6      # part du glissement latéral rattrapée par frame : adhérence de F1, la voiture colle
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
DRIFT_GRIP = 0.08            # volant tenu : la glisse se résorbe vite, les dérives restent courtes
DRIFT_MIN_SPEED = 8.0       # drift seulement à haute vitesse (~60 % de la vitesse max)
DRIFT_YAW_BOOST = 1.3       # la voiture pivote un peu plus en drift
DRIFT_TURN_SPEED = 0.165    # rotation max en drift (hors drift : TURN_SPEED)
DRIFT_MAX_SLIP = 0.3        # rad (~17°) : angle de glisse maximal, une dérive de F1, pas de rallye
DRIFT_RECOVER_GRIP = 0.3    # volant relâché ou contre-braquage : l'adhérence revient vite (~0,1 s)
DRIFT_EXIT_SLIP = 0.1       # rad (~6°) : de nouveau dans l'axe, le drift est fini
DRIFT_SCRUB = 0.0025        # perte de vitesse par frame et par radian de glisse
DRIFT_STEER_IN = 0.5        # braquage mini pour lancer un drift (gros coup de frein en braquant fort)
DRIFT_STEER_OUT = 0.15      # en dessous, le volant est considéré comme relâché
DRIFT_AUTO_STEER = 0.98     # sans frein : braquer à fond...
DRIFT_AUTO_SPEED = 0.95     # ... quasiment à la vitesse max fait décrocher l'arrière

# Le bot décide toutes les BOT_DECISION_FRAMES images (il garde ses touches entre deux) : conduite moins
# hachée, comme un joueur qui ne peut pas changer de touche 50 fois par seconde
BOT_DECISION_FRAMES = 2

# Murs : on glisse le long du mur ; toucher un mur coûte vraiment de la vitesse
WALL_HIT_LOSS = 0.25        # perte au premier contact : même un frôlement coûte cher
WALL_RUB_LOSS = 0.06        # perte par frame tant que le contact continue
WALL_CONTACT_GAP = 10       # un contact à moins de 10 frames du précédent prolonge le même contact
WALL_IMPACT_LOSS = 0.85     # perte en plus, × sin²(angle d'impact) : de face, presque tout
WALL_BOUNCE = 0.15          # petite part de vitesse renvoyée vers la piste
WALL_ALIGN = 0.5            # part du cap réalignée sur le mur, × sin(angle d'impact)

# Track config
TRACK_WIDTH = 90
TRACK_OUTER_MARGIN = 40
TRACK_INNER_MARGIN = TRACK_OUTER_MARGIN + TRACK_WIDTH

CHECKPOINT_RADIUS = 100  # fenêtre de franchissement d'une porte (px)
CAR_NOSE = 20            # du centre au pare-chocs avant (px)
FINISH_RADIUS = 100  # fenêtre après la ligne d'arrivée où le franchissement est compté (px)

# Fonts
FONT_SIZE = 24

# Colors
COLOR_GRASS = (34, 139, 34)       # Forest Green
COLOR_ROAD = (105, 105, 105)      # Dim Gray
COLOR_BORDER = (255, 255, 255)    # White
COLOR_CHECKPOINT = (255, 215, 0)  # Gold
