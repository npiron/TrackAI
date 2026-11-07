# SPEED E1 : vitesse depuis best/ T65

## S-1 : DAgger depuis T65, professeur H=29

Commande (identique pour les deux runs, seule la graine change) :
`scripts/imitate.py --init data/models/best/best.zip --static --laps 3 --teacher-horizon 29 --hit-weight 10 --wall-penalty -50 --dagger 6 --dagger-eps 0 0.05 --seed <graine> --out data/checkpoints/ppo_s1_<a|b>`

Évaluation : `scripts/eval.py --episodes 20 --seed 0 --static --laps 3` (piste fixe, déterministe : 20 épisodes identiques).

| run | graine | durée | finis | chocs (moy / max) | temps total |
|---|---|---|---|---|---|
| référence best/ T65 | - | - | 20/20 | 0 / 0 | 15,84 s |
| `ppo_s1_a` | 2300 | 5 min 15 | 20/20 | 2 / 2 | 22,76 s |
| `ppo_s1_b` | 2400 | 4 min 22 | 20/20 | 4 / 4 | 16,76 s |

Verdict :
- Aucun des deux runs n'atteint la cible (≤ 15,30 s sans choc) : tous deux finissent mais touchent des murs (a : 2, b : 4), donc fiabilité perdue.
- `s1_a` est aussi plus lent que T65 (22,76 s) ; `s1_b` est plus lent (16,76 s contre 15,84 s).
- Pendant les DAgger, la politique a pourtant fait des courses jusqu'à 15,34 s (run b, dernier tour), mais le modèle final (BC sur l'ensemble agrégé) n'en conserve pas la performance.
- Aucun candidat n'est promu ; `data/models/best/` est intact.

Note : `eval.py` écrit par défaut dans `.team/metrics.json` ; les deux entrées ont été déplacées dans `.goal/metrics.json` (`.team/` reste inchangé).

## S-2 : variantes de réglage depuis T65

Aucun candidat S-1 n'est 20/20, 0 choc, ≤ 15,30 s (a : 2 chocs, b : 4 chocs), donc les variantes sont lancées. Aucun candidat S-1 n'a 0 choc : le point de départ est `best/` T65 (0 choc, 15,84 s). Professeur H=29, `--wall-penalty -50`, `--dagger 6 --dagger-eps 0 0.05`, graine 2500, un seul paramètre change par rapport à la base S-1 (`--hit-weight 10`, `--lr 1e-3`, `--epochs 30`).

| run | paramètre changé | durée | finis | chocs (moy / max) | temps total |
|---|---|---|---|---|---|
| référence best/ T65 | - | - | 20/20 | 0 / 0 | 15,84 s |
| `ppo_s1_a` (graine 2300) | - | 5 min 15 | 20/20 | 2 / 2 | 22,76 s |
| `ppo_s1_b` (graine 2400) | - | 4 min 22 | 20/20 | 4 / 4 | 16,76 s |
| `ppo_s2_a` | `--hit-weight 20` | 7 min 35 | 20/20 | 25 / 25 | 18,20 s |
| `ppo_s2_b` | `--lr 3e-4 --epochs 60` | 9 min 14 | 20/20 | 3 / 3 | 16,82 s |

(a et b ont tourné en parallèle ; évaluation `eval.py --episodes 20 --seed 0 --static --laps 3`.)

Verdict :
- Aucune variante n'atteint la cible : toutes deux touchent des murs et sont plus lentes que T65.
- `hit-weight 20` dégrade fortement (25 chocs, 18,20 s) ; `lr 3e-4 --epochs 60` est proche de S-1 b (3 chocs, 16,82 s) sans gain.
- Le DAgger depuis T65 ne tient pas son niveau en fin de BC ; aucun candidat promu, `best/` intact.
