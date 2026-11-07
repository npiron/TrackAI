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

## Réglage (S-14, 2026-11-07)

Objectif : « professeur réglé » sans choc, avec la nouvelle physique, avant d'étiqueter pour E5.

| Constante | Avant (S-13) | Après |
|---|---|---|
| SPEED_PER_RADIUS | 0,2567 | 0,1242 |
| SECTOR_MULT | 6 secteurs (0,97 à 1,19) | `[]` (1 partout) |
| PREDICT_FRAMES | 9 | 3 |
| LOOK_MIN / LOOK_GAIN | 127 / 400 | 55 / 318 |
| STEER_DEADZONE | 0,0342 | 0,0759 |
| SAFE_HORIZON | 29 | 40 |

| Mesure (3 tours) | Avant | Après |
|---|---|---|
| statique, 20 ép., graine 0 | 12,56 s, 10 chocs | **14,12 s, 0 choc, 20/20 finis** |
| banc 50 pistes | 14,36 s, 13,0 chocs/course (94 % finis) | **16,75 s, 0 choc sur les 50 pistes, 50/50 finis** |

Le professeur réglé est donc ~1,6 s plus lent sur la piste fixe : 0 choc passe avant la vitesse.

Méthode : hill-climbing parallèle (8 processus, 8 candidats par génération, mutation de 1 à 3 constantes), score = temps statique 3 tours + temps moyen du banc + 10 s × (chocs statique + 3 × chocs moyens du banc) + pénalité d'échec. Trois passes (~20, 25 et 28 min) : (1) banc en 1 tour, 12,98 s / 0 choc statique mais 0,76 choc/course sur le banc en 3 tours (8 graines fautives : 2, 3, 22, 26, 30, 34, 46, 48) ; (2) banc en 3 tours dans le score : 0 choc partout. Le banc en 1 tour ne suffit pas : les chocs apparaissent dans les tours suivants. Constantes figées après la passe 2 ; le banc sert donc à la fois à la recherche et à la mesure (surapprentissage possible sur ces 50 graines, à revalider sur d'autres graines).

Essais abandonnés : balayage SPEED_PER_RADIUS × SAFE_HORIZON à la main (SECTOR_MULT vide) : ralentir seul ne supprime pas les chocs (0,14 : 4 chocs statique), SAFE_HORIZON 45 : le tour n'est plus fini (le bouclier bloque) ; SAFE_HORIZON 40 n'est utilisable qu'avec les autres constantes retouchées. Le script de recherche était un outil jetable hors dépôt (`search_heuristic.py` non modifié : sa piste unique et son banc absent ne suffisaient pas).

Commandes :
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model heuristic --static --laps 3 --episodes 20 --seed 0
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model heuristic --bench --laps 3
```
