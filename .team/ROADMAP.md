# Feuille de route TrackAI

> Tenue par le planificateur. Version initiale posée à la main le 2026-11-03, à revoir au premier passage.

## Objectif actuel (2026-11-03 22:43) : 3 tours sans échec puis temps minimal

Étapes : multi-tours (T16-T17) → référence humaine (T18) → PPO 1 tour (T19) → fiabilité 3 tours (T20) → vitesse. Le banc physique (ci-dessous) est clos ; physique figée (contrainte).

## Ancien objectif (clos, 2026-11-03 22:30) : physique/gameplay : vérifier gameplay/physique, simulation réaliste

Priorité absolue sur l'ancien plan RL (jalons 0-1 mis en pause : T3-T6 reportées, sauf T3 random qui sert de test de bon sens). Contrainte : aucune capture d'écran ; tout se vérifie par scénarios numériques headless.
Suspicions lues dans le code (à confirmer par mesure) : vitesse terminale théorique ≈ 22 < MAX_SPEED 32 (ACCEL 0.18, FRICTION 0.992) ; pas de dt (unités par frame, FPS=50) ; marche arrière impossible (speed>=0) ; après un mur, `speed` et `vel` se désynchronisent ; `is_drifting` calculé mais jamais stocké ; actions non bornées ; boost ×1.15 par frame dans la zone ; collision par glissement axe X/Y grossier.

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
- 2026-11-03 22:15 : objectif changé (physique/gameplay réaliste). Pause du plan RL ; nouveau jalon « banc physique » (T7-T11). Critère défini dans GOAL.md.
- 2026-11-03 22:25 : banc T7-T10 validé, 15 écarts triés. Corrections retenues : #1 MAX_SPEED, #2 désynchro, #3/#4 clip actions ; le reste assumé arcade. Tâches T11-T15 ; objectif atteint si metrics.json porte un `physics_check` sans fail, validé reviewer. Plan RL toujours en pause.
- 2026-11-03 22:43 : nouvel objectif (3 tours puis temps). Critère mesurable défini dans GOAL.md (piste fixe `--static`, 20 épisodes, seed 0, finish_rate 20/20 puis temps ≤ humain). Les modèles existants sont invalides (physique changée). Temps humain à mesurer (T18, action de Nicolas).
