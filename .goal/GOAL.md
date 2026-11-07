# Goal

Passer un cap : un agent qui roule sans choc sur des circuits aléatoires jamais vus, puis qui bat son professeur (pilote programmé H=29, 14,62 s) sur le circuit fixe. Les commandes restent des touches (9 actions discrètes, comme un clavier) ; le dosage se fait en tapotant, la physique fait déjà monter le volant progressivement.

Plan, dans l'ordre :

1. Observation v2, sans changer la physique : position réelle du volant (`car.steering`), 5 prochains points de la ligne centrale dans le repère de la voiture (distance, angle), courbure à venir, 9 lidars plus longs au lieu de 5. L'observation v1 (14 valeurs) reste disponible par option pour évaluer les anciens modèles.
2. Ré-imitation (BC + DAgger depuis le professeur H=29) avec l'observation v2, sur un mélange piste fixe + pistes procédurales. Elle valide l'observation v2 : au moins aussi bon que best/ s5_a en statique (15,46 s, 0 choc) et nettement moins de chocs en procédural (cible < 1 choc/course, contre 2,8).
3. Affinage PPO depuis ce modèle, sans oubli : faible learning rate, petit clip, perte d'imitation auxiliaire décroissante, récompense = progression le long de la piste par pas + petite pénalité de temps + forte pénalité par choc, 8 environnements en parallèle, mélange fixe + procédural. But : passer sous 14,62 s en statique sans choc, et réduire encore les chocs en procédural.
4. Optionnel : professeur à trajectoire optimisée hors ligne sur la piste fixe (borne ≈ 13,96 s), puis imitation.

Priorité : d'abord zéro choc sur pistes procédurales, ensuite la vitesse.

## Constraints

- Ne pas modifier la physique de la voiture sans le proposer d'abord dans l'inbox.
- Garder les 9 actions discrètes (pas d'actions continues).
- Entraînements de 30 min maximum par itération. Un modèle peut être repris d'une itération à l'autre.
- Banc procédural fixe : 50 pistes (graines 0 à 49), toujours les mêmes, pour comparer les modèles ; plus l'éval statique habituelle (`scripts/eval.py --static --laps 3`, 20 épisodes, graine 0). Chaque candidat mesuré est ajouté à `metrics.json`.
- Garder le meilleur modèle dans `data/models/best/` avec sa mesure ; archiver l'ancien avant de le remplacer.
- Pas de screenshot de l'app.
- Historique de l'ancienne équipe : `.team/`, en lecture seule. Docs des essais précédents dans `docs/` (notamment `SPEED_E2.md`, `BOUND_T32.md`, `WALL_BASELINE.md`).

## Success criterion

> Maintained by the planner. Do not edit by hand.

- criterion: to be defined
- status: not evaluated
