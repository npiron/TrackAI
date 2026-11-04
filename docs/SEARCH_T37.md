# Recherche heuristique élargie (T33)

Hill-climbing, 3 tours, piste fixe, seed 0, 6 secteurs de spline, 2 redémarrages (graine 0+i), 270 s chacun.

| restart | graine | essais | temps (s) | paramètres |
|---|---|---|---|---|
| 0 | 0 | 570 | 17.619999999999713 | {'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 127, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0342, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]} |
| 1 | 1 | 670 | 23.119999999999745 | {'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 139, 'LOOK_GAIN': 381, 'STEER_DEADZONE': 0.0231, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]} |

Meilleur : 17.619999999999713 s — `{'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 127, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0342, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]}`
