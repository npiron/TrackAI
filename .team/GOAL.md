# Objectif

Un agent entraîné qui enchaîne 3 tours complets du circuit fixe (`build_track()`) sans échec, puis qui réduit au maximum le temps total des 3 tours.

Étapes attendues : d'abord la fiabilité (finir les 3 tours), ensuite la vitesse. Le temps de référence à battre est mon meilleur temps humain sur ce circuit, à mesurer avec le même chrono que le banc.

## Contraintes

- Autorisé : ajouter un mode multi-tours (paramètre `laps`, 1 par défaut) au jeu et à l'environnement, sans changer la physique ni le comportement en 1 tour.
- Ne pas modifier la physique de la voiture sans le proposer d'abord dans l'inbox.
- Entraînements de 10 min maximum par itération. Un modèle peut être repris d'une itération à l'autre.
- Chaque modèle candidat est évalué avec `scripts/eval.py` sur au moins 20 épisodes, graine fixe, et ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/`, avec sa mesure.
- Pas de screenshot de l'app.

## Critère de réussite

> Rempli par le planificateur, ne pas éditer à la main.

- critère : sur `build_track()` (piste fixe, seed 42, `--static`), avec `laps=3`, via `scripts/eval.py` sur ≥ 20 épisodes, graine 0, politique déterministe : (1) fiabilité = 20/20 épisodes qui terminent les 3 tours sans sortie de piste fatale ni timeout ; (2) vitesse = temps total moyen des 3 tours inférieur ou égal au temps de référence humain (mesuré avec le même chrono, voir T16/T21), à défaut minimal et en baisse à chaque palier. Validé par le reviewer dans `metrics.json`.
- statut : en cours (fiabilité atteinte : BC t26 + DAgger, laps 3, 20/20, 17,74 s en moyenne, validé reviewer ; vitesse : temps humain non mesuré, on réduit le temps palier par palier)
