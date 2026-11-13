# TrackAI 🏎️

Jeu de time attack vu de dessus, inspiré de Trackmania (Pygame), et bot entraîné par renforcement
(PPO, Stable-Baselines3) sur des circuits longs générés aléatoirement.

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`manage.py` utilise automatiquement le Python de `.venv`.

## Commandes

```bash
python3 manage.py play                      # conduire soi-même (circuits longs, 3 tours)
python3 manage.py train --minutes 360 --live  # entraîner de zéro et suivre en direct
python3 manage.py watch                     # regarder le meilleur bot
python3 manage.py watch --follow data/checkpoints/f1   # suivre un entraînement en cours
python3 manage.py test                      # tests
```

Les autres options sont passées aux scripts : `scripts/human_lap.py`, `scripts/train_long.py`,
`scripts/watch_best.py` (voir leur `--help`).

**Conduite** : flèches, ZQSD ou WASD ; Entrée : retour au dernier checkpoint ; R : recommencer ;
N : nouveau circuit ; Échap : quitter.

## Ce que voit et fait le bot

- **Actions** (jeu 2, 15 actions) : volant -1, -½, 0, +½, +1 × rien / gaz / frein.
- **Observation v3** (50 valeurs) : vitesse et glisse, volant, prochain checkpoint, 8 points de la ligne
  centrale à venir, 9 lidars, position latérale sur la route, virages proche / moyen / lointain,
  indicateur de drift et angle de glisse. Détail dans `src/game/env.py`.
- **Physique** (`src/core/constants.py`, `src/game/physics.py`) : adhérence de type F1, drift seulement à
  haute vitesse avec un vrai coup de frein en braquant.

Les anciens formats (observation v1/v2, 9 actions) restent lisibles pour charger les anciens modèles ;
tout nouvel entraînement utilise v3 et les 15 actions.

## Organisation

- `src/game/` : physique, voiture, circuits, environnement, rendu, son.
- `src/rl/wrappers.py` : environnement Gymnasium (actions, récompense).
- `scripts/` : entraînement, visualisation, évaluation, outils de diagnostic.
- `data/checkpoints/` : générations des entraînements ; `data/models/` : meilleurs modèles.
- `docs/` : rapports d'expériences passées.
