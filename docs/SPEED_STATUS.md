# Critère vitesse : bilan de décision (T41)

Tous les temps sont sur 3 tours, piste fixe (statique), 20 ép. seed 0, 8 checkpoints dans l'ordre.

## Trajectoire du temps

| étape | temps | source |
|---|---|---|
| T22 heuristique | 45,5 s | JOURNAL (T22) |
| T24 BC (best/) | 41,7 s | JOURNAL (T24) |
| T25 heuristique | 17,94 s | `docs/SPEED_T25.md` |
| T26 BC+DAgger | 17,74 s | `docs/AUDIT_T29.md` |
| T30 heuristique + BC (best/) | 15,90 s | `docs/SEARCH_T30.md`, `docs/BEST_STATUS.md` |
| T33 heuristique (fragile : 50 % à eps 0,05) | 15,68 s | `docs/SEARCH_T33.md`, T34/T36 (modèle 49 %/31 %, refusé) |
| T37 heuristique robuste | 15,80 s | `docs/ROBUST_T37.md` |
| **T38 modèle actuel `best/`** | **15,80 s** | `metrics.json` (T38) |

Robustesse de `best/` actuel (100 ép., seed 1000) : 100/100 à eps 0, 0,05 et 0,1 (18,54 s et 19,65 s en moyenne bruitée). PPO affiné (T27) : 17,48 s, donc moins bon que le BC.

Gain total : 45,5 → 15,80 s (−65 %). Les deux derniers lots (T33, T37, T39) ne gagnent plus que 0,1-0,2 s chacun.

## Borne et marge

- Borne T32 (`docs/BOUND_T32.md`) : ligne centrale 14,77 s, ligne de course 13,96 s (indicative, non rigoureuse : marge 0 au bord, pas de contrainte dynamique sur la ligne).
- Marge restante vs 15,80 s : environ 1,84 s sur la ligne de course (−11,6 %), 1,03 s sur la ligne centrale. La borne étant optimiste, la marge réellement atteignable est inférieure.
- Plafond observé : T39 (2834 candidats, départ T37) n'a trouvé aucun professeur plus rapide avec robustesse conservée (`docs/SEARCH_T39.md`).

## Coût / bénéfice de continuer

- Coût : chaque gain de ~0,1-0,2 s a demandé une recherche de ~10 min + une ré-imitation de ~4 min, avec un risque de perte de robustesse (T33 → 49 % à eps 0,05).
- Bénéfice : au mieux ~1 s, sans garantie, sur une piste fixe (surapprentissage au tracé, aucune généralisation testée).
- Recommandation : plafond proche pour le réglage actuel de l'heuristique. Pour aller plus bas, il faudrait un autre type de méthode (optimisation de ligne de course avec dynamique, ou PPO depuis le BC avec une récompense de temps), coûteux et incertain. Ne pas poursuivre la recherche locale tant qu'on ne connaît pas le temps humain.

## Ce qu'il faut de Nicolas

`data/human_best.json` est absent (`human_best_total: null` dans le banc). Le critère « plus rapide que l'humain » n'est donc pas évaluable. Action : lancer `python scripts/human_lap.py --laps 3` et jouer 3 tours (le meilleur total est enregistré). Ensuite :
- si l'humain > 15,80 s : critère atteint, clore la phase vitesse ;
- si l'humain < 15,80 s : l'écart indique l'effort à fournir ; au-delà de ~1 s sous 15,80 s, on approche la borne théorique et il faudrait changer de méthode.

## Mise à jour T56-T62 (SAFE_HORIZON = 29)

- Depuis T57, `heuristic_lap.SAFE_HORIZON` vaut **29** (au lieu de 32) : professeur 20/20, **14,62 s, 0 choc** (piste fixe, eps 0). `best/` reste le T53b (20,46 s, 0 choc) ; aucun agent imité n'a passé le critère 0 choc : t57 15,94 s/1 choc, t60 (3×256) 15,90 s/1 choc, t61 (H=30) 20,22 s/2 chocs, t61b (H=34) 19,36 s/3 chocs.
- **Robustesse H=29 (T62)** : `robust_eval.py --model heuristic --static --laps 3 --episodes 100 --seed 1000 --eps 0.05` → **65/100 finis**, 17,86 s, 0,77 choc/course (max 5), clean 0,25. À comparer à H=32 : 93/100, 1,49 chocs. Le professeur le plus rapide est donc nettement plus fragile au bruit : gain de 3 s contre ~28 points de finis.
- Doublons : `.team/metrics.json` contient 4 entrées (au lieu de 2) pour `best/best.zip` seeds 1 et 2 (relances reviewer, 23:15) ; elles sont identiques et ne sont pas supprimées. Les 3 entrées t61 sans `.zip` sont marquées `"invalid"`.
