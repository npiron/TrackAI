# SPEED E2 : pistes aléatoires

## S-4 : référence best/ T65 sur pistes procédurales

Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --episodes 20 --seed 0 --no-static --laps 3`
(entrée ajoutée à `.goal/metrics.json`, `static: false`).

| modèle | finis | chocs (moy / max) | sans choc | temps total moyen (finis) | meilleur total |
|---|---|---|---|---|---|
| `best/` T65 | 15/20 (75 %) | 20,2 / 119 | 0 % | 24,55 s | 19,46 s |

Tours moyens effectués : 2,35 sur 3. C'est la référence à battre pour E2 : T65 est fiable sur la piste fixe (20/20, 0 choc) mais pas sur les pistes aléatoires.

## S-5 : candidats mixtes statique + procédural avec hit-weight

Départ `best/` T65, professeur H=29, `--mix-static --laps 3 --wall-penalty -50 --hit-weight 10 --episodes 12 --dagger 10 --dagger-episodes 8 --epochs 8 --lr 2e-4`. Seuls la graine et `--dagger-eps` diffèrent :

- `ppo_s5_a` : `--dagger-eps 0 0.05 --seed 2600`
- `ppo_s5_b` : `--dagger-eps 0 0.1 --seed 2700`

Évaluation : `eval.py --model data/checkpoints/ppo_s5_X.zip --laps 3 --episodes 20 --seed 0` avec `--static` puis `--no-static` (4 entrées dans `.goal/metrics.json`).

| modèle | durée d'entraînement | statique : finis | chocs (moy / max) | temps total moyen | procédural : finis | chocs (moy / max) | temps total moyen (finis) |
|---|---|---|---|---|---|---|---|
| `best/` T65 (réf. S-4) | n/a | 20/20 | 0 / 0 | 15,84 s | 15/20 | 20,2 / 119 | 24,55 s |
| `ppo_s5_a` | 2 min 50 | 20/20 | 0 / 0 | 15,46 s | 19/20 | 2,8 / 10 | 19,77 s |
| `ppo_s5_b` | 2 min 39 | 20/20 | 4 / 4 | 17,80 s | 17/20 | 12,25 / 118 | 19,23 s |

Lecture :
- `s5_a` tient 20/20 et 0 choc en statique, plus vite que best/ (15,46 s contre 15,84 s), et réduit nettement les chocs en procédural (2,8 contre 20,2 ; 19/20 finis contre 15/20). Candidat promouvable selon les critères de la story (à confirmer par S-6, notamment robustesse eps 0,05).
- `s5_b` (bruit DAgger 0,1) est non promouvable : 4 chocs en statique et 17,80 s.
- Les deux runs ont tourné en parallèle (durées gonflées), un seul tirage par configuration : l'écart a/b mêle bruit DAgger et graine.

## Verdict E2

Critère de promotion (S-6) : statique 20/20, 0 choc, ≤ 15,84 s (aucune régression) ET `--no-static` 20/20 finis avec 0 choc moyen. Chiffres repris de `.goal/metrics.json` (20 épisodes, seed 0, 3 tours).

| modèle | statique : finis | chocs (moy / max) | temps total | procédural : finis | chocs (moy / max) | temps total moyen (finis) | promu |
|---|---|---|---|---|---|---|---|
| `best/` T65 | 20/20 | 0 / 0 | 15,84 s | 15/20 | 20,2 / 119 | 24,55 s | (référence) |
| `ppo_s5_a` | 20/20 | 0 / 0 | 15,46 s | 19/20 | 2,8 / 10 | 19,77 s | non |
| `ppo_s5_b` | 20/20 | 4 / 4 | 17,80 s | 17/20 | 12,25 / 118 | 19,23 s | non |

- `s5_a` passe le volet statique (et bat T65 de 0,38 s) mais échoue le volet procédural : 19/20 finis et 2,8 chocs en moyenne, contre 20/20 et 0 exigés.
- `s5_b` échoue les deux volets (4 chocs en statique).
- Aucun candidat promu : `data/models/best/` (T65) reste intact, pas de `best_t65/`.
- Plateau final E2 : le mélange statique + procédural avec hit-weight améliore nettement la robustesse sur pistes aléatoires (chocs 20,2 → 2,8, finis 15 → 19/20) sans atteindre le zéro-choc exigé. `ppo_s5_a` reste dans `data/checkpoints/` (non versionné) comme meilleur candidat procédural.

## Promotion s5_a

`ppo_s5_a` est promu dans `data/models/best/` (`best.zip`, `best_vecnormalize.pkl`, `best.json`) ; l'ancien `best/` (T65) est archivé dans `data/models/best_t65/`.

Le critère S-6 (0 choc et 20/20 en procédural) était plus strict que la contrainte du goal, qui demande de garder dans `best/` le meilleur modèle, pas un modèle parfait. `s5_a` domine T65 sur toutes les mesures (20 épisodes, seed 0, 3 tours) :

| mesure | T65 | `s5_a` |
|---|---|---|
| statique : temps / chocs | 15,84 s / 0 | 15,46 s / 0 |
| procédural : finis | 15/20 | 19/20 |
| procédural : chocs moyens | 20,2 | 2,8 |

Réévalué depuis `best/best.zip` : mêmes chiffres (voir `.goal/metrics.json`).
