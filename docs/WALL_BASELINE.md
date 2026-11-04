# T47 · Baseline des chocs murs (piste fixe, 3 tours, 20 ép., seed 0, eps 0)

| Politique | finis | temps moyen | mean_wall_hits | max_wall_hits | clean_rate |
|---|---|---|---|---|---|
| best/ (T38, BC) | 20/20 | 15,80 s | 11,0 | 11 | 0,0 |
| `heuristic_lap` (T37) | 20/20 | 15,80 s | 11,0 | 11 | 0,0 |

`wall_hits` = nombre de pas où la voiture est poussée hors piste (physique inchangée). Les 20 épisodes sont identiques
(déterministes, piste fixe) : 11 pas de choc par course. Le clone best/ reproduit exactement l'heuristique, chocs compris.

## Localisation (`scripts/wall_locate.py`, 12 secteurs de spline, cumul des 20 ép. ; /20 = chocs par course sur 3 tours)

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/wall_locate.py --model data/models/best/best.zip --static
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/wall_locate.py --model heuristic --static
```

| Secteur | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chocs (20 ép.) | 0 | 0 | 0 | 20 | 60 | 60 | 0 | 40 | 0 | 0 | 0 | 40 |
| par course | 0 | 0 | 0 | 1 | 3 | 3 | 0 | 2 | 0 | 0 | 0 | 2 |

Résultat identique pour les deux politiques. Les chocs sont concentrés sur 5 secteurs (3, 4, 5, 7, 11) ; par tour, ≈ 3,7 pas de choc,
soit les secteurs 4-5 (≈ 2 pas par tour chacun) en tête. Pistes pour T49 : plus de marge/vitesse réduite dans les secteurs 3-5, 7 et 11 (avant la ligne de départ).

Limites : un choc compte des pas, pas des contacts distincts ; secteur = spline la plus proche de la voiture (peut être légèrement décalé dans un virage serré). Mesures évaluées par `eval.py` ajoutées à `.team/metrics.json` (heuristique et best/, 20 ép.).
