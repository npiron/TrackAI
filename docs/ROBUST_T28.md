# Robustesse de `data/models/best/best.zip` (T28)

Commande : `python scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --seed 1000 --eps 0.0 0.05 0.1`

| eps | finish | temps moyen (s) | écart-type | pire (s) |
|---|---|---|---|---|
| 0.0 | 100/100 | 15.9 | 0.0 | 15.9 |
| 0.05 | 97/100 | 18.5944 | 1.4038 | 22.78 |
| 0.1 | 91/100 | 19.9363 | 1.7 | 25.72 |

## Échecs eps=0.05

- {"seed": 1009, "cp": 5, "laps": 2, "steps": 1031, "pos": [181, 510], "info": {}}
- {"seed": 1028, "cp": 5, "laps": 0, "steps": 341, "pos": [181, 510], "info": {}}
- {"seed": 1078, "cp": 5, "laps": 0, "steps": 491, "pos": [180, 510], "info": {}}

## Échecs eps=0.1

- {"seed": 1013, "cp": 1, "laps": 2, "steps": 1009, "pos": [1220, 475], "info": {}}
- {"seed": 1014, "cp": 5, "laps": 2, "steps": 1180, "pos": [180, 510], "info": {}}
- {"seed": 1016, "cp": 5, "laps": 1, "steps": 814, "pos": [181, 510], "info": {}}
- {"seed": 1029, "cp": 5, "laps": 0, "steps": 325, "pos": [181, 510], "info": {}}
- {"seed": 1037, "cp": 5, "laps": 0, "steps": 336, "pos": [180, 510], "info": {}}
- {"seed": 1047, "cp": 5, "laps": 0, "steps": 340, "pos": [181, 510], "info": {}}
- {"seed": 1060, "cp": 5, "laps": 0, "steps": 470, "pos": [180, 510], "info": {}}
- {"seed": 1063, "cp": 5, "laps": 2, "steps": 1131, "pos": [181, 510], "info": {}}
- {"seed": 1068, "cp": 5, "laps": 0, "steps": 481, "pos": [180, 510], "info": {}}

## Analyse

- eps=0 : 100/100 mais écart-type 0 : piste statique + politique déterministe, les graines ne changent rien (preuve de déterminisme, pas de robustesse).
- Avec bruit (action aléatoire avec proba eps par frame) : 97 % à eps 0,05 ; 91 % à eps 0,1 ; temps moyen +2,7 s / +4 s.
- Cause principale : 11 échecs sur 12 s'arrêtent à la même position (≈ 181, 510) après 5 checkpoints atteints, en général tôt (325-491 steps, tour 1) : le virage serré après le checkpoint 5 (mur, arrêt `wall_stuck`) où le modèle roule en bord de piste à vitesse élevée (l'audit T29 donnait une marge de ≈ -1 à -2 px). Une perturbation avant ce virage suffit à le faire sortir. Un échec isolé (seed 1013, eps 0,1) à cp 1 vers (1220, 475).
- Pistes : pénaliser la vitesse dans ce virage (SPEED_PER_RADIUS plus bas localement) ou DAgger avec bruit d'action pour apprendre à récupérer.
