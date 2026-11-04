# État du meilleur modèle (T35)

## Modèle
`data/models/best/best.zip` (+ `best_vecnormalize.pkl`, `best.json`), gitignoré : issu de T31 = `ppo_t31a`,
clonage de comportement + 5 tours DAgger bruités (eps 0 / 0,05 / 0,1, 30 ép./tour) sur le professeur
heuristique T30 (`scripts/heuristic_lap.py`, 15,90 s à l'époque). Piste statique, 3 tours.

## Reproduction
Le professeur actuel dans le dépôt est celui de T37 (15,80 s) : ré-imiter donnera un modèle proche mais
pas identique à `best/` (T31 a été entraîné sur le professeur T30). Pour mesurer `best/` tel quel, passer
directement à l'évaluation.

Entraînement (~4 min, commande T31, sur le professeur courant) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --dagger 5 \
  --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40 --out data/checkpoints/ppo_t31a
```
Évaluation (20 ép., seed 0) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0
```
Robustesse (100 ép., seed 1000) :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --seed 1000 --eps 0 0.05 0.1
```
Audit :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/audit_lap.py --static --laps 3 --models data/models/best/best.zip --out /tmp/audit.md
```

## Mesures (relancées le 2026-11-04 01:14)
| mesure | résultat |
|---|---|
| eval 20 ép., laps 3, seed 0 | 20/20, 15,90 s (795 steps) |
| robustesse eps 0 | 100/100, 15,9 s |
| robustesse eps 0,05 | 100/100, 18,63 s moy, pire 22,22 s |
| robustesse eps 0,1 | 99/100, 19,20 s moy, pire 23,22 s |
| audit | 8 cp dans l'ordre à chaque tour, 0 frame hors piste, 0 contact mur, bord au pire -2,2 px (précision spline) |

Autres jalons : heuristique T33 15,68 s mais fragile (50 % à eps 0,05) ; heuristique T37 15,80 s et robuste
(99-100 %) ; PPO affiné (T27) 17,48 s, donc dégrade le BC. Borne théorique indicative T32 : ~13,96 s
(non rigoureuse, voir `BOUND_T32.md`).

## Limites
- Piste fixe (statique) : surapprentissage au tracé ; pas de généralisation testée.
- Professeur = heuristique à spline : le modèle ne peut guère dépasser son professeur.
- PPO en affinage dégrade le modèle BC (T27).
- Gains restants plausibles : ≤ ~1-2 s (voir T32) ; ré-imiter le professeur T37 pourrait donner < 15,90 s.
- Effet de bord : l'env réécrit `replays/personal_best.json`.

## Action humaine
Le critère vitesse vs humain n'est pas évaluable : `data/human_best.json` est absent
(`human_best_total: null`). Jouer `python scripts/human_lap.py --laps 3` pour le créer.
