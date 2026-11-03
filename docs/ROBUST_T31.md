# Robustesse de `data/checkpoints/ppo_t31a.zip` (T31)

Commande : `python scripts/robust_eval.py --model data/checkpoints/ppo_t31a.zip --static --laps 3 --episodes 100 --seed 1000 --eps 0.0 0.05 0.1`

| eps | finish | temps moyen (s) | écart-type | pire (s) |
|---|---|---|---|---|
| 0.0 | 100/100 | 15.9 | 0.0 | 15.9 |
| 0.05 | 100/100 | 18.6294 | 1.1957 | 22.22 |
| 0.1 | 99/100 | 19.1994 | 1.3443 | 23.22 |

## Échecs eps=0.1

- {"seed": 1021, "cp": 5, "laps": 2, "steps": 963, "pos": [180, 510], "info": {}}
