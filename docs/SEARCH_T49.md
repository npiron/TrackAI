# T49 · Professeur sans choc (piste fixe, 3 tours)

## Diagnostic
`heuristic_lap` (T37) : 11 pas de choc par course. Trajectoire tracée : la voiture coupe les virages (cible = point de la ligne centrale à 127+400·v indices, soit une corde) et frôle le bord intérieur (demi-largeur de route 60 px, écart au centre jusqu'à 59 px).
Essais infructueux (eps 0, 20 ép. identiques car déterministe) :
- décalage latéral de la cible `INNER_OFFSET` (−30…+50 px) : 14 chocs, pire ;
- rappel vers le centre `CROSS_GAIN` : 41 chocs ou échec ;
- recherche aléatoire (1192 combinaisons SPEED_PER_RADIUS/LOOK/offset/deadzone, 400 s) : minimum 6 chocs (temps 19,5 s) ;
- hill-climbing `search_heuristic.py --wall-penalty 3` (12 secteurs, 2×500 s, `SEARCH_INNER=1`) : score 40,5 → ~8 chocs restants.
Les constantes seules ne suffisent donc pas (contrôle tout-ou-rien, corde trop longue).

## Solution : couche de sécurité par prédiction (`SAFE_HORIZON`)
`scripts/heuristic_lap.py` : `_sim_step` recopie la physique de `TimeAttackEnv.step` (hors boost/bords d'écran) ; `_rollout` joue l'action candidate puis la politique de base (`base_action`) sur N images ; si l'action de base mène à un choc dans N images, on prend l'action la plus proche (direction/accélération) qui n'en provoque pas (sinon celle qui survit le plus longtemps). `SAFE_HORIZON = 32` (0 = comportement T37 inchangé). Options de recherche ajoutées à `search_heuristic.py` : `--wall-penalty`, `SEARCH_INNER=1`.

Balayage de l'horizon (eps 0, 20 ép., seed 0) : N=15 → 8 chocs ; 25 → échec (n'arrive pas au bout) ; 28 → 1 choc (15,34 s) ; 30 → 0 choc (16,60 s) ; 32 → **0 choc (17,40 s)** ; 35 → 1 choc ; 40 → 0 choc (19,34 s) ; ≥ 45 → échec. Non monotone : N=32 retenu (bruité 20 ép. : 100 % finis ; N=30 : 95 % ; N=40 : 70 %).

## Résultats (N=32, constantes T37 inchangées)
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/heuristic_lap.py --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/robust_eval.py --model heuristic --static --laps 3 --episodes 100 --seed 1000 --eps 0.05
```
| mesure | finis | temps moyen | mean_wall_hits | max | clean_rate |
|---|---|---|---|---|---|
| eps 0, 20 ép. seed 0 | 20/20 | 17,40 s | 0,0 | 0 | **1,0** |
| eps 0,05, 100 ép. seed 1000 | 93/100 | 18,72 s | 1,49 | 18 | 0,29 |

Coût : +1,6 s (15,80 → 17,40 s) pour 0 choc ; temps d'éval ≈ 5 s/épisode (rollouts).

## Limites / reste à faire
- Critère eps 0 atteint (20/20, 0 choc). Bruité : les chocs viennent surtout des actions aléatoires (non filtrées, eps 5 % = ~1 action tous les 20 pas) : clean_rate 0,29 et 7 échecs sur 100 (T37 : 99/100) → la sécurité n'est pas robuste aux perturbations (horizon trop court pour récupérer après une action aléatoire à haute vitesse).
- Pas de recherche des constantes de base avec la couche active (chaque éval ≈ 5 s). Piste : recherche avec `SAFE_HORIZON` fixé, ou marge de sécurité (pixel voisin) dans `_sim_step`.
- Pour T50 : DAgger bruité avec ce professeur (étiquettes sûres sur états bruités) ; le professeur est lent (~5 ms/pas) : budget d'échantillons à surveiller.
