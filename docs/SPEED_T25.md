# Balayage heuristique (T25)

3 tours, piste fixe (--static), seed 0, 1 épisode par combinaison (piste et physique déterministes : les 20 épisodes sont identiques). Point de départ T22 : SPEED_PER_RADIUS 0.06, PREDICT 18, LOOK 25/40 → 45,46 s.

Cinq balayages successifs (`scripts/sweep_heuristic.py`), la grille glissant tant que le meilleur était au bord. Tables triées par temps ; les 8 meilleures lignes de chacune :

## Balayage 1

| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |
|---|---|---|---|---|---|---|
| 0.15 | 18 | 35 | 40 | 1.0 | 33.74 | 8.0 |
| 0.2 | 18 | 35 | 40 | 1.0 | 34.38 | 8.0 |
| 0.15 | 24 | 35 | 40 | 1.0 | 34.46 | 8.0 |
| 0.2 | 24 | 35 | 40 | 1.0 | 34.6 | 8.0 |
| 0.12 | 24 | 35 | 40 | 1.0 | 34.74 | 8.0 |
| 0.1 | 18 | 35 | 40 | 1.0 | 34.86 | 8.0 |
| 0.12 | 18 | 35 | 40 | 1.0 | 34.94 | 8.0 |
| 0.2 | 18 | 35 | 20 | 1.0 | 35.28 | 8.0 |

## Balayage 2

| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |
|---|---|---|---|---|---|---|
| 0.3 | 14 | 60 | 80 | 1.0 | 29.04 | 8.0 |
| 0.5 | 14 | 60 | 80 | 1.0 | 29.04 | 8.0 |
| 0.15 | 14 | 60 | 80 | 1.0 | 29.68 | 8.0 |
| 0.2 | 14 | 60 | 80 | 1.0 | 29.72 | 8.0 |
| 0.15 | 14 | 60 | 60 | 1.0 | 30.04 | 8.0 |
| 0.2 | 14 | 60 | 60 | 1.0 | 30.46 | 8.0 |
| 0.15 | 14 | 45 | 80 | 1.0 | 30.48 | 8.0 |
| 0.15 | 18 | 45 | 80 | 1.0 | 30.48 | 8.0 |

## Balayage 3

| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |
|---|---|---|---|---|---|---|
| 0.3 | 10 | 100 | 160 | 1.0 | 23.72 | 8.0 |
| 0.3 | 10 | 80 | 160 | 1.0 | 23.92 | 8.0 |
| 0.3 | 10 | 80 | 120 | 1.0 | 24.74 | 8.0 |
| 0.3 | 10 | 100 | 120 | 1.0 | 24.76 | 8.0 |
| 0.3 | 14 | 100 | 160 | 1.0 | 25.34 | 8.0 |
| 0.3 | 10 | 60 | 160 | 1.0 | 25.48 | 8.0 |
| 0.3 | 10 | 100 | 80 | 1.0 | 25.78 | 8.0 |
| 0.3 | 14 | 80 | 160 | 1.0 | 25.98 | 8.0 |

## Balayage 4

| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |
|---|---|---|---|---|---|---|
| 0.2 | 10 | 200 | 240 | 1.0 | 17.94 | 8.0 |
| 0.3 | 10 | 200 | 160 | 1.0 | 18.1 | 8.0 |
| 0.2 | 10 | 200 | 160 | 1.0 | 18.76 | 8.0 |
| 0.3 | 10 | 140 | 240 | 1.0 | 19.54 | 8.0 |
| 0.2 | 10 | 140 | 240 | 1.0 | 19.66 | 8.0 |
| 0.1 | 10 | 200 | 240 | 1.0 | 19.84 | 8.0 |
| 0.1 | 10 | 200 | 160 | 1.0 | 19.88 | 8.0 |
| 0.1 | 10 | 140 | 240 | 1.0 | 20.2 | 8.0 |

## Balayage 5

| SPEED_PER_RADIUS | PREDICT | LOOK_MIN | LOOK_GAIN | finish | total (s) | cp |
|---|---|---|---|---|---|---|
| 0.2 | 10 | 200 | 240 | 1.0 | 17.94 | 8.0 |
| 0.2 | 10 | 200 | 160 | 1.0 | 18.76 | 8.0 |
| 0.2 | 14 | 200 | 240 | 1.0 | 20.4 | 8.0 |
| 0.2 | 6 | 200 | 160 | 1.0 | 20.94 | 8.0 |
| 0.2 | 14 | 200 | 160 | 1.0 | 21.72 | 8.0 |
| 0.2 | 6 | 200 | 240 | 0.0 | None | 5.0 |
| 0.2 | 6 | 200 | 400 | 0.0 | None | 3.0 |
| 0.2 | 6 | 300 | 160 | 0.0 | None | 2.0 |

## Résultat

Retenu : SPEED_PER_RADIUS 0.2, PREDICT_FRAMES 10, LOOK_MIN 200, LOOK_GAIN 240 → 17,94 s (3 tours, 8/8 cp). Gain principal : visée beaucoup plus lointaine (trajectoire tendue). Au-delà (LOOK 300-400) le temps remonte ou l'échec apparaît : plafond local du réglage. Limite : politique utilisant la spline, piste fixe.
