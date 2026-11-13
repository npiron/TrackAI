# TrackAI : consignes pour les agents

- Toujours passer par `python3 manage.py` (play, train, watch, test). Le jeu se joue et s'entraîne sur les
  **circuits longs aléatoires** (track_variant=2), jamais sur l'ancienne piste fixe.
- Version actuelle : observation **v3**, jeu d'actions **2** (15 actions avec demi-braquages), physique F1.
  Les formats v1/v2 et 9 actions ne servent qu'à relire d'anciens modèles ou au professeur heuristique.
- Physique : `src/core/constants.py` + `src/game/physics.py`. Après tout changement de physique, recalculer
  `REF_HASH` dans `tests/test_laps.py` et vérifier `tests/test_physics.py`. Un modèle entraîné sur une
  ancienne physique n'est plus comparable.
- `python3 manage.py test` doit passer avant de lancer un entraînement.
- Ne jamais supprimer `data/checkpoints/` ou `data/models/` sans accord explicite.
- Commits : `feat:` / `fix:` en français.
