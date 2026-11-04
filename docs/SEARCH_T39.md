# Recherche heuristique élargie (T33)

Hill-climbing, 3 tours, piste fixe, seed 0, 6 secteurs de spline, 2 redémarrages (graine 0+i), 270 s chacun.

| restart | graine | essais | temps (s) | paramètres |
|---|---|---|---|---|
| 0 | 0 | 1425 | 17.619999999999713 | {'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 127, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0342, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]} |
| 1 | 1 | 1409 | 17.619999999999713 | {'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 127, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0342, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]} |

Meilleur : 17.619999999999713 s — `{'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 127, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0342, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]}`

## Conclusion T39

Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/search_heuristic.py --sectors 6 --restarts 2 --max-seconds 540 --budget 100000 --noise-eps 0.05 --noise-episodes 8 --t0-max 15.7 --start <paramètres T37> --out docs/SEARCH_T39.md` (9 min). 2834 candidats évalués (2 redémarrages), aucun ne tient à la fois t0 ≤ 15,7 s et un temps bruité < 17,62 s (départ T37). Le professeur T37 (15,80 s, 99 % à eps 0,05) est conservé : plafond local pour ce score. Secteurs : 6 (8 aurait cassé le départ T37 dont SECTOR_MULT a 6 valeurs).
