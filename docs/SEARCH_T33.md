# Recherche heuristique élargie (T33)

Hill-climbing, 3 tours, piste fixe, seed 0, 6 secteurs de spline, 4 redémarrages (graine 0+i), 140 s chacun.

| restart | graine | essais | temps (s) | paramètres |
|---|---|---|---|---|
| 0 | 0 | 696 | 15.9 | {'SPEED_PER_RADIUS': 0.2836, 'PREDICT_FRAMES': 8, 'LOOK_MIN': 125, 'LOOK_GAIN': 384, 'STEER_DEADZONE': 0.0375, 'SECTOR_MULT': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]} |
| 1 | 1 | 739 | 15.9 | {'SPEED_PER_RADIUS': 0.3178, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 134, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0211, 'SECTOR_MULT': [1.0031, 0.8978, 0.7788, 1.0199, 1.1754, 1.0546]} |
| 2 | 2 | 681 | 16.38 | {'SPEED_PER_RADIUS': 0.3537, 'PREDICT_FRAMES': 7, 'LOOK_MIN': 126, 'LOOK_GAIN': 367, 'STEER_DEADZONE': 0.0548, 'SECTOR_MULT': [0.8598, 0.9585, 0.9249, 0.8925, 0.9156, 0.9259]} |
| 3 | 3 | 775 | 15.68 | {'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 139, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0345, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]} |

Meilleur : 15.68 s — `{'SPEED_PER_RADIUS': 0.2567, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 139, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0345, 'SECTOR_MULT': [0.9738, 1.19, 1.0158, 0.9957, 1.0729, 1.1127]}`
