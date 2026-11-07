# Goal

Passer un cap : un agent qui roule sans choc sur des circuits aléatoires jamais vus, puis qui bat son professeur (pilote programmé, réglé à l'étape 0) sur le circuit fixe. Les commandes restent des touches (9 actions discrètes, comme un clavier) ; le dosage se fait en tapotant, la physique fait déjà monter le volant progressivement.

La physique a été refaite façon Trackmania le 2026-11-07 (voir `docs/PHYSICS.md`, section « Physique façon Trackmania ») : plus de pivot à l'arrêt, marche arrière, drift au frein, glissement le long des murs. Toutes les mesures d'avant sont invalidées : pilote programmé 12,56 s mais 10 chocs par course (réglages de l'ancienne physique), best/ s5_a 19,48 s avec 22 chocs.

Plan, dans l'ordre :

0. Recaler sur la nouvelle physique : régler à nouveau le pilote programmé (vitesses en virage, horizon du bouclier) pour qu'il soit rapide et sans choc, remesurer la borne (`scripts/lower_bound.py`) et le banc de 50 pistes ; le professeur réglé sert à toutes les étapes suivantes.

1. Observation v2, sans changer la physique : position réelle du volant (`car.steering`), 5 prochains points de la ligne centrale dans le repère de la voiture (distance, angle), courbure à venir, 9 lidars plus longs au lieu de 5. L'observation v1 (14 valeurs) reste disponible par option pour évaluer les anciens modèles.
2. Ré-imitation (BC + DAgger depuis le professeur réglé à l'étape 0) avec l'observation v2, sur un mélange piste fixe + pistes procédurales. Elle valide l'observation v2 : 0 choc en statique, au moins aussi rapide que le professeur réglé, et < 1 choc/course sur le banc procédural.
3. Affinage PPO depuis ce modèle, sans oubli : faible learning rate, petit clip, perte d'imitation auxiliaire décroissante, récompense = progression le long de la piste par pas + petite pénalité de temps + forte pénalité par choc, 8 environnements en parallèle, mélange fixe + procédural. But : battre le professeur en statique sans choc, et réduire encore les chocs en procédural.
4. Optionnel : professeur à trajectoire optimisée hors ligne sur la piste fixe (borne à remesurer avec la nouvelle physique), puis imitation.

Priorité : d'abord zéro choc sur pistes procédurales, ensuite la vitesse.

## Constraints

- Physique figée dans son état « Trackmania » du 2026-11-07 : toute modification passe d'abord par l'inbox.
- Garder les 9 actions discrètes (pas d'actions continues).
- Entraînements de 30 min maximum par itération. Un modèle peut être repris d'une itération à l'autre.
- Banc procédural fixe : 50 pistes (graines 0 à 49), toujours les mêmes, pour comparer les modèles ; plus l'éval statique habituelle (`scripts/eval.py --static --laps 3`, 20 épisodes, graine 0). Chaque candidat mesuré est ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/` avec sa mesure ; archiver l'ancien avant de le remplacer.
- Pas de screenshot de l'app.
- Historique de l'ancienne équipe : `.team/`, en lecture seule. Docs des essais précédents dans `docs/` (notamment `SPEED_E2.md`, `BOUND_T32.md`, `WALL_BASELINE.md`).

## Success criterion

> Maintained by the planner. Do not edit by hand.

- criterion: deux conditions mesurées sur un même modèle, par le reviewer, avec observation v2 : (A) banc procédural fixe (50 pistes, graines 0 à 49, 1 épisode par piste, 3 tours, `scripts/eval.py --bench`) : 50/50 finis et moyenne de chocs < 1 par course (intermédiaire ; cible finale 0 choc) ; (B) piste fixe (`eval.py --static --laps 3`, 20 épisodes, graine 0) : 20/20, 0 choc, temps total moyen < celui du professeur réglé à l'étape 0 (nouvelle physique) = 14,12 s (mesuré, 0 choc). Priorité : A avant B. Lecture retenue du but : « roule sans choc » = < 1 choc/course sur pistes jamais vues.
- status: in progress (professeur 14,12 s / 0 choc, banc 0 choc ; best/ v1 : 19,48 s / 22 chocs ; E5 en cours)
