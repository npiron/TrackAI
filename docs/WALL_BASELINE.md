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

## T55 · Repli « politique + garde-fou » (NON conforme à « agent seul »)

`eval.py --model shield:<zip>` : l'action du modèle est filtrée par `_safe_action` (T49/T51, rollouts de 32 images sur la physique simulée) ; si elle mène à un choc, une alternative est choisie.
```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model shield:data/models/best_t38/best.zip --static --laps 3 --episodes 20 --seed 0
```

| Politique | finis | temps moyen | mean_wall_hits | clean_rate |
|---|---|---|---|---|
| T38 seul | 20/20 | 15,80 s | 11,0 | 0,0 |
| **T38 + garde-fou** | 20/20 | **16,42 s** | **0,0** | **1,0** |
| T53b (best/ actuel) seul | 20/20 | 20,46 s | 0,0 | 1,0 |

Borne : T38 + garde-fou donne 0 choc 20/20 en 16,42 s, soit 4 s de mieux que T53b (agent seul), mais le garde-fou simule la physique (pas un agent pur). T53b + garde-fou échoue (0/20 finis, bloqué vers 306 pas) : le garde-fou perturbe un modèle déjà prudent. Décision pour l'humain : accepter ou non le garde-fou dans le critère.

## T58 · Pistes aléatoires jamais vues (`--no-static`, bonus)

`SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model <zip> --laps 3 --episodes 20 --seed 0` (sans `--static`) ; professeur : `heuristic_lap.py --laps 3 --episodes 20 --seed 0` (SAFE_HORIZON=29).

| Politique | finis | temps moyen | mean_wall_hits | max | clean_rate |
|---|---|---|---|---|---|
| best/ T53b | 18/20 (90 %) | 26,27 s | 36,9 | 202 | 0,0 |
| best_t38 | 14/20 (70 %) | 24,08 s | 116,5 | 227 | 0,0 |
| heuristique (professeur 0 choc) | 18/20 (90 %) | 15,61 s | 0,0 | 0 | 0,9 |

Verdict : le bonus (agent généraliste, 0 choc, pistes inconnues) n'est PAS atteint. L'agent T53b finit 90 % des pistes aléatoires mais touche ~37 murs/course (clean 0) : l'imitation sur la piste fixe ne transfère pas la prudence. Le professeur lui-même ne finit que 90 % (clean 0,9 = chocs nuls sur les finis). Faisabilité : plausible mais demande un DAgger sur pistes aléatoires (`imitate.py` sans `--static`, professeur rapide ~0,6 s/ép.), non tenté ici ; une seule graine (0).

## T62 · Mise à jour SAFE_HORIZON = 29 (T56-T61)

L'heuristique/professeur utilise désormais `SAFE_HORIZON = 29` (T57). Les sections T49/T51/T55 ci-dessus décrivent H=32 (17,40 s, 0 choc) ; à H=29 : 14,62 s, 0 choc, 20/20 (eps 0).

Robustesse bruitée (`robust_eval.py --model heuristic --static --laps 3 --episodes 100 --seed 1000 --eps 0.05`) :

| Horizon | finis | temps moyen | chocs/course | clean |
|---|---|---|---|---|
| H=32 | 93/100 | — | 1,49 | — |
| **H=29** | **65/100** | 17,86 s | 0,77 | 0,25 |

Note : `metrics.json` contient 4 entrées (au lieu de 2) pour `best/` seeds 1 et 2 (doublons identiques, relances du reviewer).

## T64 — où et pourquoi t57 / t60 touchent 1 mur

Script : `scripts/diagnose_hits.py` (rejoue l'agent sur piste statique, 3 tours, déterministe ; à chaque pas calcule aussi l'action du professeur `heuristic_action`, H=29, au même état ; ne modifie ni physique ni env).
Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/diagnose_hits.py --model data/checkpoints/ppo_t57.zip --laps 3` (idem `ppo_t60.zip`). La sortie JSON est la dernière ligne (précédée d'une ligne « NEW PB » de l'env).

| agent | durée | pas | chocs | tour | pas du choc | indice spline (/2400) | position | vitesse avant | action agent / prof. au choc | pas où l'agent diffère ≥ 1re fois (30 derniers pas) | écarts d'action totaux |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t57 | 15,94 s | 797 | **1** | 3 | 593 | 704 (29,3 %) | (565,3 ; 818,1) | 11,86 | 1 / 1 | pas 571, idx 514 : agent 1 (tout droit) vs prof. 6 (droite+accélère) ; 13 écarts sur 30 pas | 103/797 (12,9 %) |
| t60 | 15,90 s | 795 | **1** | 3 | 606 | 701 (29,2 %) | (568,8 ; 818,1) | 10,43 | 5 / 5 | pas 582, idx 511 : agent 1 vs prof. 6 ; 7 écarts sur 30 pas | 77/795 (9,7 %) |

Conclusions :
- **Même virage** pour les deux agents (spline ≈ 701-704, ~29 % de la piste, position quasi identique à 3 px près), **au 3ᵉ tour seulement** (0 choc aux tours 1 et 2). Un seul point à corriger.
- Au moment du choc, l'action de l'agent est **identique** à celle du professeur (1/1 et 5/5) : le choc n'est pas une dernière action erronée. Le professeur serait aussi en danger à cet état ; l'écart vient de **~190 points de spline plus tôt** (idx 511-514), où l'agent va tout droit (action 1) alors que le professeur tourne à droite en accélérant (6), puis 8-12 pas de décalage (3-5 pas d'action différents) amènent trop vite/trop large dans le virage.
- Les agents diffèrent du professeur sur 10-13 % des pas, mais un seul de ces écarts (entrée de virage ~idx 511-514) est fatal ; zone cible pour T65 : pas ~ [choc − 30 ; choc], soit spline ~480-710 au tour 3. Limite : le choc n'apparaît qu'au tour 3 (états/vitesses d'entrée différents), donc un suréchantillonnage doit couvrir la zone aux 3 tours.

## T68 · Robustesse de best/ T65 au bruit d'action (static, laps 3, 100 ép., seed 1000)
Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --seed 1000 --eps E` (E = 0 et 0,05).

| Agent | eps | finis | temps moyen | chocs/course | max | clean |
|---|---|---|---|---|---|---|
| best/ T65 | 0 | 100/100 | 15,84 s | 0,0 | 0 | 1,00 |
| best/ T65 | 0,05 | **24/100** | 20,02 s | 1,02 | 31 | 0,03 |
| T53b (T53b, réf.) | 0,05 | 68/100 | – | – | – | – |
| Professeur H=29 | 0,05 | 65/100 | 17,86 s | 0,77 | 5 | 0,25 |
| T38 (réf.) | 0,05 | 97 % | – | – | – | – |

Verdict : T65 est parfait sans bruit mais nettement moins robuste que T53b et H=29 (24 % finis, clean 0,03) : le gain de vitesse s'est payé en robustesse. Une graine (1000), eps 0 déterministe (std 0).
