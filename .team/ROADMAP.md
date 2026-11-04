# Feuille de route TrackAI

> Tenue par le planificateur. Version initiale posée à la main le 2026-11-03, à revoir au premier passage.

## Objectif actuel (2026-11-03 22:43) : 3 tours sans échec puis temps minimal

Étapes : multi-tours (T16-T17) → référence humaine (T18) → PPO 1 tour (T19) → fiabilité 3 tours (T20) → vitesse. Le banc physique (ci-dessous) est clos ; physique figée (contrainte).

## Point 23:16

T16-T20 faits : infrastructure multi-tours et banc OK, mais PPO 200k steps n'a fini aucun tour (t19 : 1.0 cp, t20 : 2.0 cp). Avant d'entraîner plus, on réduit l'incertitude : diagnostic de l'échec (T21), preuve de faisabilité par heuristique (T22), puis correction de récompense (T23) et amorçage par imitation (T24). Temps humain : action de Nicolas en attente.

## Point 23:35

Fiabilité ATTEINTE : BC t24 (imitation de l'heuristique) 20/20 sur 3 tours, 41,7 s (heuristique 45,5 s ; PPO brut 0). Phase vitesse : T25 heuristique plus rapide, T26 ré-imitation/DAgger, T27 affinage PPO, T28 robustesse. Le critère vitesse final attend `data/human_best.json` (action de Nicolas) ; sans lui, on poursuit la baisse du temps. Limite connue : la politique dérive d'une heuristique qui lit la spline, valable sur la piste fixe seulement (conforme à l'objectif).

## Point 23:47

Heuristique 17,94 s et BC+DAgger 17,74 s (20/20, best/) : le temps a été divisé par 2,3. Avant d'aller plus loin, on vérifie la validité du chrono (T29 audit coupe de virages/checkpoints) et la robustesse (T28), puis nouveau gain par optimisation du professeur (T30). PPO (T27) passe en dernier : les tentatives brutes ont échoué. Temps humain toujours absent (action de Nicolas).

## Point 00:11

T27-T30 faits : best/ = BC t30, 15,90 s, 20/20, audit valide, 100/100 (91-97 % avec bruit d'action). PPO n'améliore pas le BC (17,48 s). Suite : robustesse bruitée (T31), borne théorique (T32) pour savoir s'il reste de la marge, recherche élargie (T33) + ré-imitation (T34), doc (T35). Temps humain toujours absent : pas de GOAL_REACHED.

## Point 00:45

T31-T33 faits : best/ 15,90 s robuste (100/100, 100/99 % bruités) ; professeur T33 15,68 s (borne ≈ 13,96 s, marge faible). Premier essai T34 : 15,68 s mais fragile sous bruit (49/31 %) → pas de remplacement ; T36 refait l'imitation avec DAgger bruité, T37 cherche un professeur robuste. Temps humain toujours absent : pas de GOAL_REACHED.

## Point 01:20

T31-T37 faits. Professeur T37 15,80 s robuste (99 % à eps 0,05) ; best/ reste BC T31 15,90 s. La marge restante est faible (borne 13,96 s). Suite : T38 ré-imitation du professeur T37, T39 recherche plus poussée, T40 non-régression 1 tour, T41 bilan vitesse. Temps humain toujours absent : pas de GOAL_REACHED.

## Décisions
- 2026-11-04 : le critère vitesse reste non évaluable sans `data/human_best.json` ; on continue à gagner du temps tant que robustesse ≥ T31, mais on plafonne l'effort (rendements décroissants) : si T38 et T39 échouent, clore la phase vitesse.

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
- 2026-11-03 23:16 : PPO brut à 0 tour fini ; on diagnostique (T21) et on prouve la faisabilité par heuristique (T22) avant d'investir plus de calcul. Pas de modif physique.
- 2026-11-03 23:35 : PPO brut abandonné comme voie principale (T19/T20/T23 : 0 tour) ; l'imitation (T24) donne la fiabilité. Phase vitesse T25-T28. Pas de GOAL_REACHED tant que le temps humain manque.
- 2026-11-03 23:47 : T25/T26 validées (17,74 s). Priorité à la validité des mesures (T29, T28) avant l'optimisation (T30). Pas de GOAL_REACHED : temps humain manquant.
- 2026-11-04 00:11 : PPO relégué (T27 dégrade). Effort sur le professeur (T32-T34) et la robustesse (T31) ; best/ remplacé seulement sur mesure.
- 2026-11-04 00:45 : un gain de temps ne remplace best/ que si la robustesse bruitée de T31 est conservée (T34 → T36/T37).
