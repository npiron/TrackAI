# SPEED E2 : pistes aléatoires

## S-4 : référence best/ T65 sur pistes procédurales

Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --episodes 20 --seed 0 --no-static --laps 3`
(entrée ajoutée à `.goal/metrics.json`, `static: false`).

| modèle | finis | chocs (moy / max) | sans choc | temps total moyen (finis) | meilleur total |
|---|---|---|---|---|---|
| `best/` T65 | 15/20 (75 %) | 20,2 / 119 | 0 % | 24,55 s | 19,46 s |

Tours moyens effectués : 2,35 sur 3. C'est la référence à battre pour E2 : T65 est fiable sur la piste fixe (20/20, 0 choc) mais pas sur les pistes aléatoires.
