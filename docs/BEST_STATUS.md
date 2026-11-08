# État du meilleur modèle (S-24)

## Modèle
`data/models/best/best.zip` (+ `best_vecnormalize.pkl`, `best.json`), gitignoré : `ppo_v2_ft_c` (S-26),
affinage PPO + imitation auxiliaire de `ppo_v2_b` (lr 3e-5, wall-penalty -100, 3 M de pas, graine 3),
observation v2 (`obs_version: 2`). Commandes et comparatif : `docs/PPO_V2.md`.

Ancien best `ppo_v2_b` (S-18 : statique 14,16 s / 0 choc, banc 0,16 choc/course) archivé tel quel dans
`data/models/best_v2b/`. Plus anciens : `best_s5a_v1`, `best_t65` (voir `data/models/`).

## Promotion
Règle (S-23) : statique 20/20 et 0 choc, puis chocs du banc, puis temps statique. `ppo_v2_ft_c` : statique
20/20, 0 choc, 14,08 s (contre 14,16 s) ; banc 50/50, 6 chocs (0,12/course) contre 8 (0,16) : **strictement
meilleur, promu**. Réserve : gain faible (0,04 s, 2 chocs sur 50 courses) et dépendant de la graine
(`ft_d`, même réglage, graine 4 : 14,26 s, banc 0,48).

## Reproduction
Entraînement (~15 min, 3 400 pas/s ; `--init` = l'ancien best, aujourd'hui `data/models/best_v2b/best.zip`) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/ppo_finetune.py --init data/models/best_v2b/best.zip --timesteps 3000000 \
  --n-envs 4 --lr 3e-5 --wall-penalty -100 --seed 3 --max-minutes 28 --out data/checkpoints/ppo_v2_ft_c
```
Évaluation (rejouée le 2026-11-08 19:46 sur `best/`, mêmes chiffres que `best.json`) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --bench --laps 3
```

## Mesures
| mesure | résultat |
|---|---|
| statique, 20 ép., laps 3, seed 0 | 20/20, 14,08 s, 0 choc |
| banc, 50 pistes, laps 3 | 50/50, 16,22 s, 0,12 choc/course (max 1, 6 pistes, 6 chocs) |

Pistes fautives du banc (indice dans `wall_hits_by_seed`) : 4, 6, 12, 20, 21, 39 (1 choc chacune). Professeur : 14,12 s statique, 16,75 s banc, 0 choc.

## Limites
- Pas encore 0 choc au banc (6 pistes sur 50) ; critère A (< 1 choc/course) atteint, voir `docs/PPO_V2.md`.
- Gain de 0,04 s sur le professeur dépendant de la graine, statique déterministe.
- Robustesse (eps) non mesurée pour ce modèle.
- Effet de bord : l'env réécrit `replays/personal_best.json`.
