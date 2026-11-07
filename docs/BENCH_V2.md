# Banc procédural fixe (v2)

> Baseline périmée (ancienne physique) : voir `docs/TEACHER_V2.md` pour les mesures de référence actuelles.

50 pistes inconnues : l'épisode k utilise `generate_procedural_track(seed=k)`, k = 0..49, sans autre hasard (résultat identique à chaque lancement).

Commande :
`SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --bench --laps 3`

## Baseline best/best.zip (2026-11-07 21:36, 3 tours)

| finish_rate | mean_total_time | best_total_time | mean_wall_hits | max_wall_hits | clean_rate |
|---|---|---|---|---|---|
| 0.92 | 20.50 s | 15.46 s | 3.18 | 13 | 0.10 |

Mesuré deux fois : chiffres identiques. Entrée ajoutée à `.goal/metrics.json` (clé `wall_hits_by_seed` = chocs par graine).

Top 5 des graines où best/ choque le plus : 36 (13 chocs), 2 (10), 14 (10), 5 (9), 10 (9).
