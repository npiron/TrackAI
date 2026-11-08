# Physique : triage des écarts de réalisme

Source : `scripts/physics_check.py` (FPS=50, 1 frame = 1/50 s fixe). Mesures reproductibles (JSON identique à chaque lancement).
Constantes : `src/core/constants.py` (MAX_SPEED=32, ACCEL=0.18, BRAKE=0.5, FRICTION=0.992, TURN_SPEED=0.08, LATERAL_GRIP=0.2).
Aucun changement de code dans cette tâche : les décisions « corriger » deviennent des tâches du planner. Les décisions touchant la dynamique invalident les modèles RL déjà entraînés.

| # | Écart | Statut | Mesure | Décision |
|---|-------|--------|--------|----------|
| 1 | MAX_SPEED inatteignable | **corrigé (T14)** | vitesse terminale 22.32 px/frame (1116 px/s) = 69.75 % de MAX_SPEED=32 ; 90 % du terminal en 5.74 s | **Corriger** : rendre la constante cohérente (soit baisser MAX_SPEED à ~22-23, soit relever ACCEL/réduire la friction). Le clamp est trompeur et la normalisation de l'obs `speed_n` n'utilise jamais [0,1]. **T14** : MAX_SPEED baissé de 32 à 23 (option « baisser », qui garde la sensation de jeu : ACCEL/FRICTION inchangés) ; terminal 22.32 = 97.0 % de MAX_SPEED (scénario `terminal_reaches_max_speed`, seuil 95 %). Boost (×1.15, cap 1.2×MAX_SPEED = 27.6) reste borné : pic 26.45. `speed_n` et `speed_factor` (virage) se normalisent désormais sur 23. **Les modèles RL antérieurs sont invalidés** (aucun n'existe dans le dépôt) |
| 2 | Désynchro `speed` / `\|vel\|` après choc | confirmé | écart relatif max 0.85 (mur perpendiculaire), 0.87 (45°), seuil 0.25 ; voiture quasi à l'arrêt mais `speed` élevé (2.98 final en perpendiculaire) | **Corrigé (T13)** : après une collision, `speed` est recalé sur `\|vel\|` (`env.step`). Écart mesuré après correction : 0.0 aux frames de contact (le banc détecte un contact quand `speed` chute de >3 % d'une frame à l'autre) |
| 3 | Actions non bornées : steer | corrigé (T12) | steer=5 → `car.steering`=5.0, rotation 17.2 rad/s (5× le max) | **Corriger** : `np.clip` des actions dans `env.step` (steer, accel, brake) |
| 4 | Actions non bornées : accel | corrigé (T12) | accel=3 → 22.15 px/frame après 50 frames contre 7.38 pour accel=1 | **Corriger** : même clip que #3 |
| 5 | accel/brake négatifs | infirmé | accel=-1 et brake=-1 sans effet, pas de NaN | Rien à faire (le clip de #3 les couvre) |
| 6 | Pas de marche arrière | confirmé | `speed` borné à 0, `reverse_possible=false` | **Assumer** (choix arcade : l'agent n'en a pas besoin, l'action n'existe pas). À revoir seulement si les pistes demandent des demi-tours |
| 7 | Pas de limite d'adhérence latérale | confirmé | vitesse de rotation quasi constante : 3.81 / 3.44 / 3.18 rad/s à v=5/15/22 ; rayon 61.5 / 206.6 / 329.9 px (croît bien avec la vitesse) | **Assumer** (arcade) : le rayon croît avec la vitesse, ce qui suffit au gameplay. Pas de sous-virage physique ; on documente |
| 8 | Dérive en virage établi | confirmé, marginal | 16.8° (v=5, fail), 15.2° (v=15, fail), 14.2° (v=22, pass), seuil 15° | **Assumer** : dérive de 14-17° voulue par LATERAL_GRIP=0.2 (sensation de drift). Relever le seuil du banc à 18° plutôt que changer le jeu |
| 9 | Réaction du volant | infirmé | braquage plein en 7 frames (0.14 s), seuil 15 | Rien à faire |
| 10 | Boost dépasse MAX_SPEED | confirmé | pic 36.8 px/frame = 115 % de MAX_SPEED, cap 38.4 respecté | **Assumer** (le boost est un bonus voulu, cap explicite). Dépend de #1 : si MAX_SPEED est corrigé, vérifier que le boost reste borné |
| 11 | Pas de rebond ni dégâts au mur | confirmé | la voiture colle au mur et glisse ; 0 frame hors piste, aucune téléportation | **Assumer** (arcade, bon pour l'apprentissage) |
| 12 | Pas de dt variable | confirmé | 1 frame = 1/FPS fixe | **Assumer** : pas de rendu à dt variable pour le RL, la simulation reste déterministe. À reconsidérer seulement si l'on découple rendu et simulation |
| 13 | Freinage / roue libre | mesuré | freinage plein depuis le terminal : 39 frames, 476 px ; roue libre −0.148 px/frame² (~0.66 %/frame) | **Assumer** : plausible et monotone |
| 14 | Checkpoints, arrivée, départ, reproductibilité | infirmé (tout pass) | 8 checkpoints dans l'ordre, pas de saut, finish refusé avant les CP, départ vitesse 0, graine égale = même trajectoire | Rien à faire |
| 15 | Boost absent de `build_track` | constat | `boost_zones=[]` ; le banc injecte une zone | **Assumer** ; test dédié déjà couvert par injection |

## Tâches à convertir (« corriger »)

- #1 : MAX_SPEED cohérent avec la vitesse terminale (puis re-mesurer avec le banc ; invalide les modèles).
- #2 : resynchroniser `speed` après collision.
- #3 + #4 : clipper les actions dans `env.step`.
- Ajuster le seuil de dérive du banc (#8) à 18°.

## Bilan final (T15)

Banc `scripts/physics_check.py` : **20 scénarios, 20 pass, 0 fail** (entrée `physics_check` de `.team/metrics.json`, reproductible : 2 lancements donnent le même résumé).

- Corrigés : #1 (MAX_SPEED=23, terminal 97 %), #2 (speed=|vel| après choc), #3/#4 (clip des actions), seuil de dérive relevé à 18° (#8).
- Assumés (choix arcade, documentés ci-dessus) : #6, #7, #8, #10, #11, #12, #13, #15. Infirmés : #5, #9, #14.

## Physique façon Trackmania (2026-11-07, demandée par Nicolas)

La dynamique est maintenant dans `src/game/physics.py` (`drive`), partagée par `TimeAttackEnv.step` et le simulateur du pilote programmé (`scripts/heuristic_lap.py::_sim_step`). Constantes dans `src/core/constants.py`.

| Avant | Maintenant |
|---|---|
| La voiture pivotait sur place à l'arrêt (rotation maximale à vitesse nulle) | Rotation par le roulement (modèle bicyclette) : nulle à l'arrêt, braquage utile qui baisse avec la vitesse (`STEER_CURVATURE`, `STEER_SPEED_SENS`) ; les roues tournent quand même à l'arrêt |
| Pas de marche arrière | Frein maintenu à l'arrêt : marche arrière (`REVERSE_ACCEL`, `REVERSE_MAX`) ; la rotation s'inverse en reculant |
| Roue libre très freinée (−2,5 %/frame) | Frein moteur léger (`COAST_FRICTION` 0.994, −26 %/s) |
| Accélération plate (0→20 en 5,6 s), frein brutal (0,8 s depuis la vitesse max) | Départ vif puis plafond, façon Trackmania (`ACCEL` 0.271, `FRICTION` 0.988 : 0→8 en 0,7 s, 0→20 en 3,7 s, même vitesse terminale 22,3) ; freinage progressif (`BRAKE` 0.22, ~1,6 s depuis la vitesse max) |
| Glisse constante de 14-17° en virage | Adhérence plus forte (`LATERAL_GRIP` 0.35, ~5-8°) ; les pneus réalignent la vitesse sans perdre sa norme |
| Drift seulement mesuré | Drift : coup de frein en braquant au-dessus de `DRIFT_MIN_SPEED`, adhérence `DRIFT_GRIP` tant qu'on braque, rotation accrue, perte de vitesse par la glisse |
| Murs : glissement sur l'axe X ou Y de l'écran | Glissement le long du mur (normale lue dans le masque), perte selon sin²(angle d'impact), petit renvoi, cap réaligné sur le mur ; on ne reste jamais planté de face |
| `car.speed` = scalaire indépendant | `car.speed` = composante de `vel` le long du cap (négative en marche arrière) |

Référence remesurée après le réglage accélération/frein (20 épisodes, piste fixe, 3 tours, graine 0) : pilote programmé 20/20, 12,56 s, 10 chocs par course (réglé pour l'ancienne physique) ; best/ s5_a 20/20, 19,48 s, 22 chocs. Toutes les mesures antérieures (15,46 s, borne 13,96 s, réglages du professeur) sont invalidées. Banc `scripts/physics_check.py` : 20/20.

## Maniabilité et circuits longs (2026-11-08, réglée au clavier par Nicolas)

Vitesse ramenée à l'échelle des circuits et voiture plus maniable : `MAX_SPEED` 11.3 (terminale 11,0 px/frame, ~550 px/s au lieu de ~1 100), `ACCEL` 0.122 / `FRICTION` 0.989 (50 % en 1,25 s, 90 % en 4,2 s), `BRAKE` 0.16, roue libre `COAST_FRICTION` 0.985 (−53 %/s : il faut tenir l'accélérateur), direction plus franche (`STEER_CURVATURE` 0.016, `STEER_SPEED_SENS` 0.4, `TURN_SPEED` 0.14 : rayon ~70 px lent, ~100 px à fond). Drift plus facile et tenu : coup de frein avec ≥ 30 % de volant au-dessus de 4,5 px/frame, adhérence 0.03 en drift, rotation ×1,55, tenu tant que le volant dépasse 15 %, adhérence rétablie au-delà de ~63° (pas de tête-à-queue).

Circuits longs : `generate_procedural_track(seed, variant=2)` (contour d'une forme en cases, lignes droites + virages arrondis, route de 90 px, ~4 800 px en moyenne). Variante 1 (piste fixe, banc de 50 pistes) inchangée.

Références (piste fixe, 3 tours, 5 épisodes, graine 0) : pilote programmé 30,48 s, 0 choc (réglages de l'ancienne physique) ; best/ ft_c 32,1 s, 19 chocs. Sur circuits longs, ft_c ne finit aucun tour (10 essais). Banc `physics_check.py` : 20/20.
