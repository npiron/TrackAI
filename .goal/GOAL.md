# Goal

Un agent qui roule vite et propre sur les circuits longs aléatoires (`generate_procedural_track(seed, variant=2)` : lignes droites, épingles, chicanes, route de 90 px), jamais vus à l'entraînement. Physique et circuits ont été refaits le 2026-11-08 (voir `docs/PHYSICS.md`, section « Maniabilité et circuits longs ») : tous les modèles et le pilote programmé sont à recaler.

Plan, dans l'ordre :

0. Banc circuits longs : `scripts/eval.py` accepte la variante de tracé (`--track-variant 2`) ; banc fixe de 50 circuits longs (graines 0 à 49), 1 tour chacun ; mesurer le pilote programmé et best/ actuel.
1. Recaler le pilote programmé sur la nouvelle physique et les circuits longs (vitesses en virage, horizon du bouclier, éventuellement drift) : il doit finir tous les circuits du banc sans choc, le plus vite possible. Il sert de professeur.
2. Ré-imitation (BC + DAgger, observation v2) sur un mélange de circuits longs (variante 2) et de pistes variante 1.
3. Affinage PPO sans oubli (`scripts/ppo_finetune.py`) sur circuits longs, pour battre le professeur.

Priorité : finir 50/50 circuits longs avec < 1 choc par course, puis la vitesse.

## Constraints

- Physique figée dans son état du 2026-11-08 (`src/game/physics.py`, constantes de `src/core/constants.py`) et rendu inchangé : toute modification passe d'abord par l'inbox.
- Garder les 9 actions discrètes.
- Entraînements de 30 min maximum par itération ; un modèle peut être repris d'une itération à l'autre.
- Chaque candidat est mesuré sur le banc de 50 circuits longs (et la piste fixe pour info) et ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/` avec sa mesure ; archiver l'ancien avant de le remplacer.
- Pour la vidéo d'évolution : garder des « générations » (modèles intermédiaires dans `data/checkpoints/`, nommés dans l'ordre, au moins un par étape d'entraînement). À la fin, générer `videos/evolution_longs.mp4` avec `scripts/evolution_video.py --track-variant 2 --track-seed <graine hors banc> --models … --labels …`.
- Pas de screenshot de l'app.
- Historique : `.team/` (lecture seule) et `docs/`.

## Success criterion

> Maintained by the planner. Do not edit by hand.

- criterion: banc de 50 circuits longs (`eval.py --bench --track-variant 2 --laps 1`, graines 0 à 49, mesuré par le reviewer dans `metrics.json`) : A = 50/50 finis et moyenne < 1 choc par course ; B (vitesse) = `mean_total_time` strictement inférieur à celui du professeur recalé (mesuré à l'étape 1). Priorité à A, puis B. Lecture retenue : « vite » = temps moyen du banc, comparé au professeur.
- status: not evaluated
