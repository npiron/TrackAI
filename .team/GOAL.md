# Objectif

Entraîner un agent qui fait 3 tours du circuit fixe sans jamais toucher un mur, 20 courses sur 20, puis réduire le temps total.

Ajouter une option d'entraînement `wall_fatal` (désactivée par défaut, le jeu ne change pas) et compter les chocs par course dans `eval.py`.
Y aller par paliers : grosse pénalité par choc d'abord, mort au contact ensuite, pour ne pas apprendre à l'agent à rouler au pas.
Bonus : même résultat sur des circuits aléatoires jamais vus.

## Contraintes

- Autorisé : ajouter un mode multi-tours (paramètre `laps`, 1 par défaut) au jeu et à l'environnement, sans changer la physique ni le comportement en 1 tour.
- Ne pas modifier la physique de la voiture sans le proposer d'abord dans l'inbox.
- Entraînements de 10 min maximum par itération. Un modèle peut être repris d'une itération à l'autre.
- Chaque modèle candidat est évalué avec `scripts/eval.py` sur au moins 20 épisodes, graine fixe, et ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/`, avec sa mesure.
- Pas de screenshot de l'app.

## Critère de réussite

> Rempli par le planificateur, ne pas éditer à la main.

- critère : sur `build_track()` (piste fixe, seed 42, `--static`), avec `laps=3`, via `scripts/eval.py` sur ≥ 20 épisodes, graine 0, politique déterministe : (1) fiabilité = 20/20 épisodes qui terminent les 3 tours avec **0 choc contre un mur** (compteur `wall_hits` d'`eval.py`, un choc = pas où le déplacement sortirait de la piste) et sans timeout ; (2) vitesse = temps total moyen des 3 tours le plus bas possible, en baisse à chaque palier (ou ≤ temps humain si `data/human_best.json` existe). Validé par le reviewer dans `metrics.json`. Bonus : même résultat sur circuits aléatoires jamais vus (`--no-static`).
- statut : en cours (ancien critère « terminer 3 tours » atteint par best/ T38, 20/20, 15,80 s, mais les chocs murs n'étaient pas comptés : nombre de chocs de best/ inconnu, mesuré en T46-T47 : 11 chocs/course, clean_rate 0 ; professeur heuristique sûr : 0 choc 20/20 à 17,40 s, mais agent appris T50 : 0/20)
