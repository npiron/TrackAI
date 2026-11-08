# Project

> Filled in by you once. Every agent reads this file first.

## What it is

TrackAI : jeu de course vu de dessus en Pygame (`trackmania_clone.py`, `src/`) et agents entraînés dessus (PPO Stable-Baselines3, imitation BC/DAgger d'un professeur heuristique). Scripts d'entraînement et d'éval dans `scripts/`, modèles dans `data/models/` (le meilleur dans `data/models/best/`).

## Commands

- setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- fast tests (run by the reviewer on every task): `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q --ignore=tests/test_e2e_training.py`
- measure (results go to `.goal/metrics.json`): `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0` ; robustesse : `scripts/robust_eval.py` (eps 0,05, 100 épisodes)

## Rules

- Physique de la voiture (src/game/physics.py) figée : toute modification passe d'abord par l'inbox.
- Entraînements de 30 min maximum par itération. Lancer un entraînement long au premier plan avec un timeout Bash explicite (jusqu'à 2 400 000 ms, autorisé par `.claude/settings.json`).
- Pas de screenshot de l'app ; toujours `SDL_VIDEODRIVER=dummy` pour les scripts sans affichage.
- Puissance : un seul entraînement à la fois (ppo_finetune utilise 16 environnements, la collecte du professeur tous les cœurs) ; deux en parallèle se partagent les 8 cœurs et ne vont pas plus vite.
- macOS : `sed -i ''` (BSD sed, `sed -i 's/…/'` échoue). Pour attendre un processus lancé en arrière-plan, vérifier d'abord qu'il tourne (`pgrep`) et toujours borner l'attente (pas de `until …; do sleep; done` sans limite).
- `.team/` est l'historique de l'ancienne équipe : le lire, ne pas le modifier.

## Language

Write the journal, inbox messages and task titles in: French
