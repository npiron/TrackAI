# État du meilleur modèle (S-19)

## Modèle
`data/models/best/best.zip` (+ `best_vecnormalize.pkl`, `best.json`), gitignoré : `ppo_v2_b` (S-18),
imitation BC + 8 tours DAgger sur le professeur heuristique, observation v2 (`obs_version: 2`, détectée
automatiquement par `scripts/eval.py`). Commandes et comparatif : `docs/IMITATION_V2.md` (« Candidats n°2 »).

Ancien best (`ppo_s5_a`, physique obsolète : 19,48 s / 22 chocs statique, 43,16 chocs au banc) archivé tel
quel dans `data/models/best_s5a_v1/`. Plus anciens : `best_t65` (voir `data/models/`).

## Promotion
Règle : statique 20/20 finis et 0 choc, banc 50/50 finis avec moins de chocs que l'ancien best. `ppo_v2_b` :
statique 20/20, 0 choc ; banc 50/50, 8 chocs au total (0,16/course) contre 43,16 : **promu**.

## Reproduction
Entraînement (~3 min 18 s) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --obs-version 2 --mix-static --laps 3 \
  --episodes 60 --epochs 8 --lr 2e-4 --wall-penalty -50 --hit-weight 10 \
  --dagger 8 --dagger-episodes 16 --dagger-eps 0 0.05 --seed 1801 --out data/checkpoints/ppo_v2_b
```
Évaluation (relancée le 2026-11-07 23:45, mêmes chiffres que `best.json`) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --bench --laps 3
```

## Mesures
| mesure | résultat |
|---|---|
| statique, 20 ép., laps 3, seed 0 | 20/20, 14,16 s, 0 choc |
| banc, 50 pistes, laps 3 | 50/50, 16,47 s, 0,16 choc/course (max 3, 6 pistes, 8 chocs) |

Pistes fautives du banc : 6, 21, 22, 25, 38 (1 choc) et 39 (3 chocs). Professeur : 14,12 s statique, 16,75 s banc, 0 choc.

## Limites
- Pas encore 0 choc au banc ; statique 14,16 s contre 14,12 s pour le professeur.
- Robustesse (eps) non mesurée pour ce modèle.
- Effet de bord : l'env réécrit `replays/personal_best.json`.
