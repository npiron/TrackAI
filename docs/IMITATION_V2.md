# Candidat v2 n°1 : `ppo_v2_a` (BC + DAgger, observation v2)

Modèle imité du professeur réglé (`heuristic_lap`, obs v2 pour la politique, étiquettes via `obs_v1()`).
Fichiers : `data/checkpoints/ppo_v2_a.zip` + `ppo_v2_a_vecnormalize.pkl` (non versionnés).

## Commande exacte (1 min 52 s, une seule exécution, graines de piste ≥ 1000)

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --obs-version 2 --mix-static --laps 3 \
  --episodes 60 --epochs 8 --lr 2e-4 --wall-penalty -50 --hit-weight 10 \
  --dagger 4 --dagger-episodes 12 --dagger-eps 0 0.05 --seed 1700 \
  --out data/checkpoints/ppo_v2_a
```

BC : 60 épisodes (eps 0 / 0,1 / 0,2 / 0,3), 49 429 échantillons, précision 0,687. DAgger : 4 tours × 12 épisodes, 94 090 échantillons au total, précision finale 0,782.

## Résultats (3 tours)

| Mesure | Modèle | Temps moyen | Chocs (moy / max) | Finis |
|---|---|---|---|---|
| Statique (20 ép., graine 0) | professeur | 14,12 s | 0 / 0 | 20/20 |
| Statique | `ppo_v2_a` | 14,14 s | 0 / 0 | 20/20 |
| Banc (50 pistes) | professeur | 16,75 s | 0 / 0 | 50/50 |
| Banc | `ppo_v2_a` | 16,50 s | 0,58 / 4 | 50/50 |

Banc : 15 pistes sur 50 avec au moins un choc (29 chocs au total), `clean_rate` 0,70.

## Top 5 graines du banc fautives (chocs)

1. graine 6 : 4 chocs
2. graine 39 : 3 chocs
3. graines 1, 11, 22 : 2 chocs chacune (ex æquo ; 26, 31, 32, 36, 40, 44 aussi à 2)

## Diagnostic

Sur la piste fixe le modèle égale le professeur (+0,02 s, 0 choc) ; sur le banc il va un peu plus vite (16,50 s contre 16,75 s) mais en payant des chocs sur 30 % des pistes procédurales, très probablement dans les virages serrés/enchaînements où il coupe la trajectoire que le professeur garde propre (à confirmer en rejouant la graine 6).

# Candidats n°2 : `ppo_v2_b` et `ppo_v2_c`

Un seul levier change par rapport à la commande de `ppo_v2_a`, graines de piste d'entraînement ≥ 1000. Aucun changement de code.

## Commandes exactes

`ppo_v2_b` (plus de DAgger : 8 tours × 16 épisodes, graine 1801), entraînement 3 min 18 s :

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --obs-version 2 --mix-static --laps 3 \
  --episodes 60 --epochs 8 --lr 2e-4 --wall-penalty -50 --hit-weight 10 \
  --dagger 8 --dagger-episodes 16 --dagger-eps 0 0.05 --seed 1801 \
  --out data/checkpoints/ppo_v2_b
```

`ppo_v2_c` (chocs plus pondérés : `--hit-weight 30`, graine 1802), entraînement 1 min 49 s :

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --obs-version 2 --mix-static --laps 3 \
  --episodes 60 --epochs 8 --lr 2e-4 --wall-penalty -50 --hit-weight 30 \
  --dagger 4 --dagger-episodes 12 --dagger-eps 0 0.05 --seed 1802 \
  --out data/checkpoints/ppo_v2_c
```

Échantillons finaux : v2_b 166 269 (précision DAgger 0,828), v2_c 118 569 (précision 0,824).

## Comparatif (3 tours)

| Modèle | Statique : temps | Statique : chocs (moy / max) | Statique : finis | Banc : temps | Banc : chocs (moy / max) | Banc : finis | Pistes du banc avec choc |
|---|---|---|---|---|---|---|---|
| professeur | 14,12 s | 0 / 0 | 20/20 | 16,75 s | 0 / 0 | 50/50 | 0 |
| `ppo_v2_a` | 14,14 s | 0 / 0 | 20/20 | 16,50 s | 0,58 / 4 | 50/50 | 15 (29 chocs) |
| `ppo_v2_b` | 14,16 s | 0 / 0 | 20/20 | 16,47 s | 0,16 / 3 | 50/50 | 6 (8 chocs) |
| `ppo_v2_c` | 14,16 s | 0 / 0 | 20/20 | 16,35 s | 0,70 / 12 | 50/50 | 16 (35 chocs) |

Graines fautives de v2_b : 6, 21, 22, 25, 38 (1 choc chacune) et 39 (3 chocs). v2_c est pire que v2_a (une piste à 12 chocs, graine 12) : pondérer plus les chocs n'aide pas.

## Meilleur candidat

Règle : 0 choc statique et 20/20 finis, puis moins de chocs au banc (50/50 finis), puis temps statique le plus bas. Les trois candidats satisfont le statique ; au banc v2_b (0,16) bat v2_a (0,58) et v2_c (0,70). **Meilleur candidat : `ppo_v2_b`** (statique 14,16 s contre 14,14 s pour v2_a : écart non significatif, ±0,02 s ; critère ≤ 14,12 s non atteint). Le banc n'est pas encore à 0 choc.
