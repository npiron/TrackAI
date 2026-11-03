# Physique : triage des écarts de réalisme

Source : `scripts/physics_check.py` (FPS=50, 1 frame = 1/50 s fixe). Mesures reproductibles (JSON identique à chaque lancement).
Constantes : `src/core/constants.py` (MAX_SPEED=32, ACCEL=0.18, BRAKE=0.5, FRICTION=0.992, TURN_SPEED=0.08, LATERAL_GRIP=0.2).
Aucun changement de code dans cette tâche : les décisions « corriger » deviennent des tâches du planner. Les décisions touchant la dynamique invalident les modèles RL déjà entraînés.

| # | Écart | Statut | Mesure | Décision |
|---|-------|--------|--------|----------|
| 1 | MAX_SPEED inatteignable | confirmé | vitesse terminale 22.32 px/frame (1116 px/s) = 69.75 % de MAX_SPEED=32 ; 90 % du terminal en 5.74 s | **Corriger** : rendre la constante cohérente (soit baisser MAX_SPEED à ~22-23, soit relever ACCEL/réduire la friction). Le clamp est trompeur et la normalisation de l'obs `speed_n` n'utilise jamais [0,1] |
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
