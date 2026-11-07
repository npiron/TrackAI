# Goal

Entraîner un agent qui fait 3 tours du circuit fixe sans jamais toucher un mur, 20 courses sur 20, puis réduire le temps total.

Ajouter une option d'entraînement `wall_fatal` (désactivée par défaut, le jeu ne change pas) et compter les chocs par course dans `eval.py`.
Y aller par paliers : grosse pénalité par choc d'abord, mort au contact ensuite, pour ne pas apprendre à l'agent à rouler au pas.
Bonus : même résultat sur des circuits aléatoires jamais vus.

## Constraints

- Autorisé : ajouter un mode multi-tours (paramètre `laps`, 1 par défaut) au jeu et à l'environnement, sans changer la physique ni le comportement en 1 tour.
- Ne pas modifier la physique de la voiture sans le proposer d'abord dans l'inbox.
- Entraînements de 10 min maximum par itération. Un modèle peut être repris d'une itération à l'autre.
- Chaque modèle candidat est évalué avec `scripts/eval.py` sur au moins 20 épisodes, graine fixe, et ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/`, avec sa mesure.
- Pas de screenshot de l'app.
- Historique de l'ancienne équipe (tâches T1-T69, journal, feuille de route) : `.team/`, en lecture seule. La prochaine tâche prévue était T69 (`.team/TODO.md`).

## Success criterion

> Maintained by the planner. Do not edit by hand.

- criterion: sur `build_track()` (piste fixe, seed 42, `--static`), avec `laps=3`, via `scripts/eval.py` sur ≥ 20 épisodes, graine 0, politique déterministe : (1) fiabilité = 20/20 épisodes qui terminent les 3 tours avec **0 choc contre un mur** (compteur `wall_hits` d'`eval.py`, un choc = pas où le déplacement sortirait de la piste) et sans timeout ; (2) vitesse = temps total moyen des 3 tours le plus bas possible, en baisse à chaque palier (ou ≤ temps humain si `data/human_best.json` existe). Validé par le reviewer dans `metrics.json`. Bonus : même résultat sur circuits aléatoires jamais vus (`--no-static`).
- status: en cours (dernière mesure : best/ T65, validé reviewer : 20/20 finis, 0 choc, clean_rate 1,0, 15,84 s, laps 3 seed 0 → fiabilité ATTEINTE, vitesse en baisse (20,46 → 15,84 s) ; borne ≈ 13,96 s, professeur H=29 14,62 s ; robustesse au bruit de T65 non mesurée (T53b : 68/100 à eps 0,05) ; bonus pistes aléatoires : 19/20, 7,35 chocs (T67, non atteint) ; temps humain absent)
