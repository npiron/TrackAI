# Robustesse de `heuristic` (T28)

Commande : `python scripts/robust_eval.py --model heuristic --static --laps 3 --episodes 100 --seed 1000 --eps 0.0 0.05 0.1`

| eps | finish | temps moyen (s) | écart-type | pire (s) |
|---|---|---|---|---|
| 0.0 | 100/100 | 15.8 | 0.0 | 15.8 |
| 0.05 | 99/100 | 18.4792 | 1.473 | 23.44 |
| 0.1 | 100/100 | 19.684 | 1.7591 | 25.0 |

## Échecs eps=0.05

- {"seed": 1025, "cp": 1, "laps": 2, "steps": 768, "pos": [1220, 478], "info": {}}
