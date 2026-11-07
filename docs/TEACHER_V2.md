# Mesures de référence, physique Trackmania (étape 0)

Date : 2026-11-07, 3 tours, aucun changement de code. Résultats dans `.goal/metrics.json`.

| Modèle | Piste | Finis | Chocs moy. | Chocs max | Temps moy. | clean_rate |
|---|---|---|---|---|---|---|
| heuristic | statique (20 ép., graine 0) | 1,00 | 10,0 | 10 | 12,56 s | 0,00 |
| heuristic | banc 50 pistes | 0,94 | 13,0 | 36 | 14,36 s | 0,00 |
| best/ (s5_a, obs v1) | statique (20 ép., graine 0) | 1,00 | 22,0 | 22 | 19,48 s | 0,00 |
| best/ (s5_a, obs v1) | banc 50 pistes | 0,92 | 43,16 | 88 | 20,77 s | 0,00 |

Conforme aux attentes de `docs/PHYSICS.md` (12,56 s / 10 chocs ; 19,48 s / 22 chocs).

Top 5 des graines du banc où heuristic choque le plus : 37 (36 chocs), 44 (34), 22 (28), 11 (22), 47 (21). 6e : 26 (20, ex æquo avec 29 et 31).
Chocs par graine : clé `wall_hits_by_seed` de l'entrée métrique.

## Commandes

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model heuristic --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model heuristic --bench --laps 3
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --bench --laps 3
```
