# Feuille de route TrackAI

> Tenue par le planificateur. Version initiale posée à la main le 2026-11-03, à revoir au premier passage.

## Vision

Un agent RL qui boucle proprement les circuits du clone Trackmania, avec des progrès **mesurés** sur un banc d'éval fixe, pas estimés.

## Jalon 0 : Mesurer avant d'optimiser (en cours)

- [fait, T1] Tests exécutables (pytest dans le `.venv`, 21 passed).
- [fait, T2] Banc d'éval reproductible (`scripts/eval.py`) : circuit fixe, graine fixe, N épisodes, sortie JSON (taux de tours terminés, meilleur temps, temps moyen, récompense moyenne).
- Mesurer la référence : agent aléatoire, puis DQN existant s'il y a un modèle.

## Jalon 1 : Valider PPO

- Entraînement PPO court (50k steps) qui tourne sans erreur.
- Comparer à la référence sur le banc. Les gains annoncés dans `RESUME_EXECUTIF.md` ne sont pas prouvés.

## Jalons suivants

À définir à partir des mesures du jalon 1 (récompenses, observations, curriculum, hyperparamètres…).

## Décisions

- 2026-11-03 22:06 : T1 et T2 validées. Reste T3 (référence random) et T4 (smoke PPO). Ajout T5 (valider le chemin modèle du banc) et T6 (PPO 50k = jalon 1). Aucune mesure réelle dans `metrics.json` pour l'instant.
- 2026-11-03 : replanification. Les 2 premières sessions de la boucle ont échoué à cause d'une erreur d'authentification (« Invalid API key », `ANTHROPIC_API_KEY` invalide qui masque le login claude.ai), pas à cause du plan. Plan inchangé, ajout de T4 (smoke PPO) en parallèle de T2. Action humaine requise : corriger/retirer `ANTHROPIC_API_KEY` avant de relancer `team_loop.sh`.
- 2026-11-03 : aucun gain n'est considéré comme acquis sans mesure dans `metrics.json`.
