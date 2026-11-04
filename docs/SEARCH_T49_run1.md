# Recherche heuristique élargie (T33)

Hill-climbing, 3 tours, piste fixe, seed 0, 12 secteurs de spline, 2 redémarrages (graine 49+i), 250 s chacun.

| restart | graine | essais | temps (s) | paramètres |
|---|---|---|---|---|
| 0 | 49 | 1219 | 44.34 | {'SPEED_PER_RADIUS': 0.2309, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 97, 'LOOK_GAIN': 400, 'STEER_DEADZONE': 0.0247, 'INNER_OFFSET': 0.0, 'SECTOR_MULT': [0.9738, 0.9738, 1.19, 1.19, 1.0386, 1.0158, 0.9957, 0.9957, 1.0729, 1.0729, 1.1127, 1.1127]} |
| 1 | 50 | 1054 | 40.46 | {'SPEED_PER_RADIUS': 0.2833, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 117, 'LOOK_GAIN': 378, 'STEER_DEADZONE': 0.0258, 'INNER_OFFSET': 9.0485, 'SECTOR_MULT': [1.0752, 1.0446, 0.9812, 0.9622, 1.1066, 1.1534, 1.1048, 0.9889, 1.1002, 1.2485, 0.9353, 1.1197]} |

Meilleur : 40.46 s — `{'SPEED_PER_RADIUS': 0.2833, 'PREDICT_FRAMES': 9, 'LOOK_MIN': 117, 'LOOK_GAIN': 378, 'STEER_DEADZONE': 0.0258, 'INNER_OFFSET': 9.0485, 'SECTOR_MULT': [1.0752, 1.0446, 0.9812, 0.9622, 1.1066, 1.1534, 1.1048, 0.9889, 1.1002, 1.2485, 0.9353, 1.1197]}`
