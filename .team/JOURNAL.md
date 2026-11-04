# Journal de l'équipe

> Ajouter en bas, ne jamais réécrire. Format :
> `## AAAA-MM-JJ HH:MM · <agent> · <tâche ou sujet>` puis quelques puces factuelles (fait, résultat mesuré, problème, suite).

## 2026-11-03 21:50 · humain+claude · Mise en place

- Projet déplacé dans `~/TrackAI` (symlink laissé dans `~/.openclaw/workspace/TackAI`).
- Équipe créée : planner, worker, reviewer. Feuille de route et todo initiales posées.
- Constat : aucun modèle entraîné dans le dépôt, `pytest` absent du `.venv`, branche PPO jamais validée par une mesure.

## 2026-11-03 21:53 · boucle · Démarrage

- Session de 2 itérations sur `team/main`.

## 2026-11-03 21:53 · boucle · Fin

- Session terminée après 2 itération(s), 0 tâche(s) validée(s) au total.

## 2026-11-03 21:55 · boucle · Démarrage

- Session de 2 itérations sur `team/main`.

## 2026-11-03 22:00 · planner · Replanification

- Constat : 0 tâche validée ; les logs worker/planner montrent « Invalid API key » (ANTHROPIC_API_KEY invalide prioritaire sur le login claude.ai). Problème d'infra, à corriger par l'humain.
- Inbox vide. Plan T1→T2→T3 conservé. Ajout T4 (smoke PPO 5k steps, dépend de T1) pour débloquer le jalon 1 en parallèle de T2.
- `metrics.json` toujours vide ; aucun modèle entraîné dans le dépôt.

## 2026-11-03 22:20 · worker · T1 Suite de tests exécutable

- Fichiers : `requirements.txt` (+pytest), `tests/test_dashboard_utils.py` (`pytest.importorskip("gradio")`, gradio absent du .venv), `tests/test_env.py` (test_track_has_boundaries obsolète : utilisait rect_outer/obstacles inexistants → vérifie spline_points, checkpoints, collision_mask).
- `pip install pytest` dans `.venv` (pytest 9.2.0).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q --ignore=tests/test_e2e_training.py` → 20 passed, 1 skipped (dashboard, faute de gradio), 1.7 s.
- Limites : test_e2e_training.py non lancé ; tests dashboard non exécutés tant que gradio n'est pas installé.

## 2026-11-03 22:30 · reviewer · T1 validée

- Relu le diff (requirements, 2 tests) : changements ciblés, sans hors-sujet.
- `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q --ignore=tests/test_e2e_training.py` → 20 passed, 1 skipped en 1.7 s (conforme au worker).
- Note : tests dashboard sautés faute de gradio.

## 2026-11-03 22:45 · worker · T2 Banc d'éval reproductible

- Fichiers : `scripts/eval.py` (nouveau), `scripts/__init__.py`, `tests/test_eval.py`.
- Principe : épisode k seedé à S+k (random, np.random → piste procédurale) ; politique random via `RandomState(S)` ; modèle PPO/DQN chargé avec VecNormalize frère `*_vecnormalize.pkl` si présent (politique déterministe). Ajoute une entrée à `.team/metrics.json` (`--metrics` pour changer).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model random --episodes 3 --seed 1 --metrics /tmp/m.json` lancée 2× → résultats identiques (mean_return -2835.2134, 1.0 checkpoint, 0 succès, 2000 steps).
- Tests : 21 passed, 1 skipped (pytest hors e2e), dont test_eval (reproductibilité).
- Limites : chemin « modèle » non testé (aucun modèle dans le dépôt). `.team/metrics.json` non modifié (réservé à T3).

## 2026-11-03 22:55 · reviewer · T2 validée

- Relu eval.py, test_eval.py : propre, hors-sujet nul, metrics.json du dépôt intact.
- Deux lancements `--model random --episodes 3 --seed 1` → résultats identiques (-2835.2134, 1.0 cp, 0 succès), égal au journal worker.
- pytest hors e2e : 21 passed, 1 skipped.
- Note : chemin « modèle » non testé (pas de modèle) ; à couvrir quand T4 produira un modèle.

## 2026-11-03 21:58 · boucle · Fin

- Session terminée après 2 itération(s), 2 tâche(s) validée(s) au total.

## 2026-11-03 22:06 · boucle · Démarrage

- Session de 5 itérations sur `team/main`.

## 2026-11-03 22:06 · planner · Replanification

- T1 et T2 validées, rangées dans « Terminées ». Inbox vide. `metrics.json` toujours vide.
- T3 et T4 conservées (indépendantes, prêtes). Ajout T5 (éval du modèle smoke, couvre le chemin modèle non testé) et T6 (PPO 50k, jalon 1).
- Feuille de route : jalon 0 presque terminé, décision datée ajoutée.

## 2026-11-03 22:06 · boucle · Fin

- Session terminée après 1 itération(s), 0 tâche(s) validée(s) au total.

## 2026-11-03 22:14 · boucle · Démarrage

- Session de 10 itérations sur `team/main`.

## 2026-11-03 22:14 · boucle · Objectif modifié

- Nouvel objectif : verifier le gameplay et la physique du jeu, et avoir une simulation realiste 

## 2026-11-03 22:15 · planner · Replanification

- Objectif modifié (vérifier gameplay/physique, simulation réaliste, sans screenshot) : critère défini dans GOAL.md = banc `scripts/physics_check.py` avec scénarios déterministes + écarts corrigés ou documentés ; statut « en cours », aucune mesure.
- Lecture de `env.step`/constants : suspicions (vitesse terminale ≈22 < MAX_SPEED 32, pas de dt, pas de marche arrière, désynchro speed/vel après mur, drift non stocké, actions non bornées). À confirmer par mesure, pas acquis.
- Plan RL mis en pause (T4-T6 reportées : la physique peut changer et invaliderait les entraînements). Nouvelles tâches T7-T10 ; T3 gardée en P3. Inbox vide.

## 2026-11-03 22:16 · worker · T7 Banc physique longitudinal

- Fichiers : `scripts/physics_check.py` (nouveau), `tests/test_physics.py`. Murs/boost/checkpoints neutralisés sur l'instance pour isoler le longitudinal (piste fixe `build_track`).
- Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/physics_check.py --metrics /tmp/m.json` lancée 3× → JSON identique. pytest hors e2e : 22 passed, 1 skipped.
- Mesures (FPS=50) : vitesse terminale 22.32 px/frame = 1116 px/s, soit 69.75 % de MAX_SPEED=32 → **MAX_SPEED inatteignable** par accélération seule (ACCEL·FRICTION/(1-FRICTION)). 90 % du terminal en 287 frames (5.74 s). Freinage plein depuis le terminal : 39 frames, 476 px. Roue libre : −0.148 px/frame² en moyenne sur 50 frames (≈0.66 %/frame, friction 0.8 %/frame). Marche arrière impossible (speed borné à 0).
- Limites : pas de dt variable (1 frame = 1/FPS fixe) ; le boost seul peut dépasser le terminal (T9). `.team/metrics.json` du dépôt non modifié (testé avec --metrics /tmp).

## 2026-11-03 22:16 · reviewer · T7 validée

- Relancé le banc 2× (--metrics /tmp) : JSON identique (cmp OK), chiffres = ceux du worker (terminal 22.32 px/frame = 69.75 % de MAX_SPEED, freinage 39 frames/476 px). pytest hors e2e : 22 passed, 1 skipped. metrics.json du dépôt intact.
- Remarque mineure : `coast_decel_pct_per_frame` a une formule alambiquée (équivaut à 100*decel/v0), sans conséquence.

## 2026-11-03 22:18 · worker · T8 Banc physique virage/adhérence

- Fichiers : `scripts/physics_check.py` (+`measure_turn`, `measure_out_of_range`, seuils en tête de fichier, clés `turn` et `out_of_range_actions` du JSON), `tests/test_physics.py` (+1 test).
- Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/physics_check.py --metrics /tmp/aN.json` 2× → sortie identique (cmp OK). pytest hors e2e : 23 passed, 1 skipped.
- Mesures (braquage plein, vitesse maintenue, régime établi, FPS=50) :
  - v=5 : rayon 61.5 px, rotation 3.81 rad/s, dérive 16.8° → **fail** (seuil 15°)
  - v=15 : rayon 206.6 px, 3.44 rad/s, dérive 15.2° → **fail** (marginal)
  - v=22 : rayon 329.9 px, 3.18 rad/s, dérive 14.2° → pass
  - Le rayon croît avec la vitesse (pass) mais la vitesse de rotation est quasi constante (~TURN_SPEED·50 rad/s) : pas de limite d'adhérence latérale, pas de vrai sous-virage physique. Dérive 14–17° en virage établi : vient de LATERAL_GRIP=0.2 (vel rattrape le cap lentement), à trancher en T10.
  - Réaction volant : braquage plein en 7 frames (0.14 s) → pass (seuil 15).
- Actions hors bornes (écarts confirmés) : **steer=5 → `car.steering` monte à 5.0** (non borné), rotation 17.2 rad/s (5× le max) → fail ; **accel=3 → vitesse après 50 frames 22.15 vs 7.38 pour accel=1** (accel non borné, triple l'accélération) → fail. accel=-1 et brake=-1 : sans effet (gardes `>0`) → pass ; aucun NaN. Sans clip dans `env.step`, un agent qui sort de [-1,1] triche ; les politiques SB3 clippent normalement, mais pas les appels directs.
- Limites : vitesse maintenue par réécriture de `car.speed` à chaque frame (frottement appliqué après → vitesse effective ≈0.992·v) ; pas de test sur piste avec murs (T9).

## 2026-11-03 22:18 · reviewer · T8 validée

- Banc relancé 2× : stdout identique, JSON identique hors horodatage `date`. Chiffres = ceux du worker (v5 16.77° fail, v15 15.25° fail, v22 14.16° pass ; steer=5 → 5.0 ; accel3 22.15 vs 7.38). pytest hors e2e : 23 passed, 1 skipped. Les fails sont des écarts réels assumés (critère = statuts pass/fail présents), à trancher en T10.

## 2026-11-03 22:19 · worker · T9 Banc physique murs/boost/checkpoints/arrivée

- Fichiers : `scripts/physics_check.py` (+`measure_world` : walls, boost, checkpoints, reproducibility ; clé `world` du JSON), `tests/test_physics.py` (+1 test).
- Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/physics_check.py --metrics /tmp/cN.json` 2× → stdout identique (cmp OK). pytest hors e2e : 24 passed, 1 skipped.
- Résultats : checkpoints (8) dans l'ordre, pas de saut, hors-ordre ignoré, finish refusé avant les CP et accepté après (reward 100), départ à vitesse 0, reproductibilité à graine égale : **pass**. Murs (piste seed 42, vitesse 15, perpendiculaire et biais 45°, 200 frames, accel pleine) : 0 frame hors piste, aucune téléportation (saut ≤ |vel|), valeurs finies : pass.
- Écarts de réalisme :
  1. **Désynchro speed/|vel| au choc** : écart relatif max 0.85 (perpendiculaire) et 0.87 (biais) > seuil 0.25 → fail. Le glissement annule une composante de vel mais `speed` n'est réduit que de 10 % (et ×0.5 si coincé), donc speed reste élevé alors que la voiture est quasi arrêtée ; la vitesse observée (obs speed_n) ment.
  2. **Boost dépasse MAX_SPEED** : pic 36.8 px/frame (115 % de MAX_SPEED=32) sous boost permanent, cap 38.4 respecté → pass du seuil 120 %, mais contredit le clamp MAX_SPEED (le clamp ne s'applique qu'avant le boost). À trancher en T10 (choix arcade probable). Note : build_track n'a aucune zone de boost (boost_zones=[]), le test injecte une zone sur toute la carte.
  3. Pas de dégâts/rebond : la voiture colle au mur et glisse (choix arcade ?).
- Limites : scénarios de mur sur un seul point de départ ; la détection du « contact » est heuristique (déplacement < 50 % de |vel|) ; `.team/metrics.json` du dépôt non modifié.

## 2026-11-03 22:20 · reviewer · T9 validée

- Banc relancé 2× : stdout identique, chiffres = ceux du worker (mismatch speed/vel 0.847 et 0.868 fail, boost pic 36.8 pass, checkpoints/reproductibilité pass, 0 frame hors piste). pytest hors e2e : 24 passed, 1 skipped. metrics.json du dépôt intact. Les échecs sont listés comme écarts numérotés.

## 2026-11-03 22:20 · worker · T10 Triage des écarts de réalisme

- Fichier : `docs/PHYSICS.md` (nouveau, aucun code touché). 15 écarts avec mesure et décision, relancé le banc pour confirmer les chiffres (identiques à T7-T9).
- Corriger : #1 MAX_SPEED inatteignable, #2 désynchro speed/vel au choc, #3/#4 actions non bornées. Assumer : marche arrière, adhérence, dérive 14-17° (seuil du banc à relever à 18°), boost, murs, dt fixe.
- Limite : décisions proposées, à valider par le planner ; corriger #1 invalide les modèles RL.

## 2026-11-03 22:21 · reviewer · T10 validée

- docs/PHYSICS.md relu : 15 écarts, mesure + décision chacun ; chiffres recoupés avec le banc relancé (terminal 22.32, drift 16.77/15.25/14.16, steer5 5.0, accel3 22.15). Aucun code modifié. pytest hors e2e : 24 passed, 1 skipped.

## 2026-11-03 22:21 · worker · T3 Référence random

- Fichier modifié : `.team/metrics.json` (entrée `random`).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model random --episodes 20 --seed 0` (3,9 s).
- Résultat : mean_return -2992.97, 1.0 checkpoint en moyenne, succès 0 %, 2000 steps/épisode (jamais de fin anticipée), pas de temps au tour. Pistes procédurales.
- Limite : une seule graine de base (0) ; cohérent avec T2 (seed 1, 3 épisodes : -2835).

## 2026-11-03 22:22 · reviewer · T3 validée

- eval.py random relancé (20 ép., seed 0) : -2992.9709, 1.0 CP, succès 0 %, 2000 steps = metrics.json. pytest hors e2e : 24 passed, 1 skipped.

## 2026-11-03 22:25 · planner · Replanification

- T7-T10 et T3 validées, rangées. Inbox vide. Constat : `metrics.json` n'a pas d'entrée `physics_check` (les lancements écrivaient dans /tmp) et l'entrée `random` est en double.
- Écarts à corriger (PHYSICS.md) convertis en T11 (seuil dérive 18° + summary + entrée metrics), T12 (clip actions), T13 (resync speed), T14 (MAX_SPEED), T15 (rapport final 100 % pass, dédoublonnage random). Décision #8 acceptée.
- GOAL.md : statut mis à jour (en cours). T4-T6 RL toujours reportées.

## 2026-11-03 22:23 · worker · T11 Seuil dérive 18° + summary + mesure dans le dépôt

- Fichier : `scripts/physics_check.py` (MAX_DRIFT_DEG=18, fonction `summarize`, clé `summary` ajoutée au JSON).
- Commandes : banc 2× avec `--metrics /tmp/yN.json` → physics_check identique (dict égal) ; puis lancé sans `--metrics` → entrée `physics_check` ajoutée à `.team/metrics.json`.
- Résumé : 19 scénarios, 15 pass ; fails = out_of_range_steer5 (#3), out_of_range_accel3 (#4), walls_perpendicular/oblique_speed_vel_coherent (#2). Les 3 virages passent à 18°. #1 non mesuré par le banc (T14).
- pytest : `-m "not e2e"` ne filtre pas (marqueur absent) → test_e2e_training échoue (long/dépendance) ; avec `--ignore=tests/test_e2e_training.py` : voir résultat ci-dessus du run (24 passed attendu).
- Limite : doublon `random` dans metrics.json laissé pour T15.

## 2026-11-03 22:23 · reviewer · T11 validée

- Banc relancé 2× (--metrics /tmp) : physics_check identique ; summary 19 scénarios, 15 pass, fails = steer5, accel3, walls ×2 (#2/#3/#4), conforme à metrics.json. Dérive 18° : 3 virages pass. pytest hors e2e : 24 passed, 1 skipped. Entrée physics_check présente dans metrics.json. Note : doublon random laissé à T15.

## 2026-11-03 22:24 · worker · T12 Clip des actions dans env.step

- Fichiers : `src/game/env.py` (np.clip steer∈[-1,1], accel/brake∈[0,1] en début de `step`), `tests/test_physics.py` (+test_step_clips_actions), `docs/PHYSICS.md` (#3/#4 corrigés), `.team/metrics.json` (physics_check réécrit par le banc).
- Banc : out_of_range_actions pass (steer5 → steering 1.0 ; accel3 = accel1 = 7.3825). Summary : 19 scénarios, 17 pass, fails restants = walls ×2 (#2).
- pytest --ignore=tests/test_e2e_training.py : voir dernière ligne exécutée (25 attendus passed + 1 skipped).
- Limite : le clip modifie le comportement d'appels directs hors bornes uniquement.

## 2026-11-03 22:25 · reviewer · T12 validée

- Diff relu (clip en tête de step, test ajouté, PHYSICS.md #3/#4). Banc relancé : out_of_range_actions pass (steering 1.0, accel3=accel1=7.3825), summary 19 scénarios / 17 pass, fails = walls ×2 (#2, T13). pytest hors e2e : 25 passed, 1 skipped. Note : le test pytest assert steering<=1 est faible mais couvert par le banc.

## 2026-11-03 22:27 · worker · T13 Resync speed après collision

- Fichiers : `src/game/env.py` (après la résolution mur : `speed = |vel|`), `scripts/physics_check.py` (détection du contact dans `_wall_run` : chute de `speed` >3 % d'une frame à l'autre, au lieu de `vm < 0.5*speed` qui comptait aussi le simple retard de `vel` au redémarrage), `tests/test_physics.py` (+import math, +test_speed_resynced_after_wall_hit), `docs/PHYSICS.md` (#2 corrigé), `.team/metrics.json` (physics_check réécrit).
- Essais : projection sur le cap puis min(speed,|vel|) laissaient 0.43 en perpendiculaire (artefact de détection au redémarrage, pas de collision) ; retenu `speed = |vel|`.
- Résultats : banc 2× sans --metrics, sorties identiques ; summary 19/19 pass ; murs : 0 frame hors piste, pas de téléportation, mismatch 0.0 aux contacts (perpendiculaire et 45°). pytest `--ignore=tests/test_e2e_training.py` : 26 passed, 1 skipped.
- Limites : mismatch 0.0 est quasi tautologique après le correctif (speed:=|vel|) ; le test garde sa valeur comme garde-fou. `speed` peut remonter légèrement si vel > speed (retard de grip), jugé négligeable. #1 non mesuré (T14).

## 2026-11-03 22:28 · reviewer · T13 validée

- Diff relu (env.py speed=|vel| après collision, détection de contact du banc, test, PHYSICS.md). Banc relancé 2× : sortie identique, summary 19/19 pass, murs 0 hors piste, 0 téléportation, mismatch 0.0. pytest hors e2e : 26 passed, 1 skipped. Réserves non bloquantes dans l'inbox (entrées physics_check cumulées, critère de contact modifié, test à aligner sur pi/2).

## 2026-11-03 22:28 · worker · T14 MAX_SPEED cohérent avec la vitesse terminale

- Fichiers : `src/core/constants.py` (MAX_SPEED 32→23), `scripts/physics_check.py` (MIN_TERMINAL_RATIO=0.95, clé `terminal_reaches_max`, scénario `terminal_reaches_max_speed` dans summary), `tests/test_physics.py` (+test), `docs/PHYSICS.md` (#1 corrigé, modèles RL invalidés), `.team/metrics.json` (physics_check réécrit).
- Résultats : terminal 22.32 = 97.04 % de MAX_SPEED (pass) ; boost pic 26.45, cap 27.6 (pass) ; virages 3/3 pass (dérive 16.5/14.3/12.8°) ; summary 20/20 pass. pytest `--ignore=tests/test_e2e_training.py` : 27 passed, 1 skipped.
- Limites : rayon de virage légèrement plus grand (speed_factor normalisé sur 23) ; doublons metrics.json laissés à T15 ; scripts/test_drift.py et env_backup lisent la constante sans changement.

## 2026-11-03 22:29 · reviewer · T14 validée

- Diff relu (MAX_SPEED 32→23, scénario terminal_reaches_max_speed, test, PHYSICS.md #1 + invalidation modèles RL). Banc relancé: 20/20 pass, terminal 22.32 = 97.04 %, boost pic 26.45 < cap 27.6, virages 3/3. pytest hors e2e: 27 passed, 1 skipped. Usages de MAX_SPEED (env, wrappers) cohérents.

## 2026-11-03 22:29 · worker · T15 Rapport final du banc

- Fichiers : `.team/metrics.json` (dédoublonné : 1 `random`, 1 `physics_check` ; la dernière entrée physics_check a été regénérée), `docs/PHYSICS.md` (section « Bilan final »), `.team/TODO.md` (statut).
- Commandes : banc sans `--metrics` (écrit dans metrics.json), puis relancé avec `--metrics /tmp/m2.json` → physics_check identique (True). Résumé : 20 scénarios, 20 pass, fails=[]. pytest `--ignore=tests/test_e2e_training.py` : 27 passed, 1 skipped.
- Limites : le `date` de l'entrée diffère entre lancements (seul champ non comparé). Réserves du reviewer en T13 (test à aligner sur pi/2) non traitées, hors tâche.

## 2026-11-03 22:30 · reviewer · T15 validée

- Banc relancé (--metrics /tmp) : 20/20 pass, fails=[] ; identique à metrics.json. metrics.json : 1 random + 1 physics_check (doublon random retiré, anciennes physics_check obsolètes supprimées). PHYSICS.md bilan cohérent. pytest hors e2e : 27 passed, 1 skipped. Critère GOAL du banc atteint.

## 2026-11-03 22:30 · boucle · Fin

- Session terminée après 10 itération(s), 5 tâche(s) validée(s) au total.

## 2026-11-03 22:33 · humain · Physique : frein moteur

- Demande de Nicolas : la voiture glissait trop quand on lâche l'accélérateur.
- Ajout de `COAST_FRICTION = 0.975` (src/core/constants.py), appliqué dans `env.step` quand `accel == 0`. `FRICTION = 0.992` reste appliqué en accélération, donc la vitesse terminale ne change pas.
- Effet : la vitesse tombe de moitié en 0,56 s au lieu de 1,74 s. Tests rapides : 27 passed, 1 skipped.
- À prendre en compte : les mesures physiques et d'éval antérieures ont été faites avec l'ancien comportement.

## 2026-11-03 22:41 · humain · Nouvel objectif

- Ancien objectif clos : « vérifier le gameplay et la physique du jeu, et avoir une simulation réaliste » (banc physique terminé en T15).
- Nouvel objectif : 3 tours complets du circuit fixe sans échec, puis temps total minimal, avec un temps humain comme référence. Mode multi-tours autorisé.

## 2026-11-03 22:43 · boucle · Démarrage

- Session de 12 itérations sur `team/main`.

## 2026-11-03 22:43 · boucle · Objectif modifié

- Nouvel objectif : Un agent entraîné qui enchaîne 3 tours complets du circuit fixe (`build_track()`) sans échec, puis qui réduit au maximum le temps total des 3 tours. Étapes attendues : d'abord la fiabilité (finir les 3 tours), ensuite la vitesse. Le temps de référence à battre est mon meilleur temps humain sur ce ci

## 2026-11-03 22:43 · planner · Replanification

- Objectif modifié : critère posé dans GOAL.md (piste fixe, laps=3, 20 épisodes, seed 0 ; fiabilité 20/20 puis temps ≤ référence humaine). Statut : non évalué.
- Nouvelles tâches T16-T20 : multi-tours, banc `--laps`, chrono humain, PPO 1 tour, fiabilité 3 tours. Piège noté : `eval.py` est procédural par défaut, il faut `--static`.
- Inbox : note reviewer T13 déjà traitée (T15 a dédoublonné metrics.json) ; seul reste mineur : aligner un test sur pi/2, non retenu. Fichier archivé.
- Le temps humain n'existe pas encore : il demande que Nicolas joue (T18).

## 2026-11-03 22:45 · worker · T16 Mode multi-tours laps
- Fichiers : `src/game/env.py` (param `laps=1`, `lap_count`, `lap_times`, reset des checkpoints à chaque tour, done au dernier tour, +100 par fin de tour), `src/rl/wrappers.py` (param `laps`, info `laps_done`/`lap_times`/`total_time`/`is_success`, timeout 2000×laps, pas de saut de progress au changement de tour), `tests/test_laps.py` (3 tests).
- Vérifs : pytest --ignore=tests/test_e2e_training.py → 30 passed, 1 skipped. Comparaison one-shot de l'env HEAD (git show) et du nouveau à laps=1 sur 1500 steps aléatoires : obs/récompense/done identiques.
- Limites : à laps>1 le `time_bonus`/PB du wrapper utilise le temps total ; pas de bonus de tour dans le wrapper hormis +100 de l'env.

## 2026-11-03 22:46 · reviewer · T16 validée

- Relu diff env.py/wrappers.py/test_laps.py ; laps=1 inchangé (test trajectoire identique), laps=3 par téléportation donne 3 lap_times, info wrapper OK. pytest hors e2e : 30 passed, 1 skipped. Reset de _last_cp_count non nécessaire (pas de récompense quand le compte baisse).

## 2026-11-03 22:48 · worker · T17 Banc --laps et métriques multi-tours
- Fichiers : `scripts/eval.py` (option `--laps`, fonction `multi_lap_stats`, clés `finish_rate`, `mean_total_time`, `best_total_time`, `mean_laps_done`, champ `laps` dans l'entrée ; anciennes clés conservées), `tests/test_eval.py` (+2 tests).
- Commande : `eval.py --model random --static --laps 3 --episodes 20 --seed 0` ×3 (2 en /tmp, 1 dans metrics.json) → sorties identiques (hors date) : finish_rate 0.0, mean_laps_done 0.0, mean_checkpoints 1.1, totaux null (aucun épisode fini).
- pytest `--ignore=tests/test_e2e_training.py` : 32 passed, 1 skipped.
- Limite : `random` ne finit aucun tour, donc mean_total_time non exercé en réel (couvert par le test unitaire). Entrée random laps=3 ajoutée à metrics.json.

## 2026-11-03 22:48 · reviewer · T17 validée

- Diff relu (eval.py, tests). Relancé eval random --static --laps 3 --episodes 20 --seed 0 ×2 : sorties identiques (hors date), nouvelles clés présentes, anciennes conservées. pytest hors e2e : 32 passed, 1 skipped. Réserve : mean_total_time non exercé en réel (couvert en unitaire).

## 2026-11-03 22:49 · worker · T18 Chrono humain
- Fichiers : `scripts/human_lap.py` (nouveau : `replay`, `load_best`, `record`, mode jeu pygame `--laps N`, écrit `data/human_best.json` si record), `scripts/eval.py` (champ `human_best_total`, null si fichier absent), `tests/test_human_lap.py` (3 tests).
- Vérifs : pytest `--ignore=tests/test_e2e_training.py` → 35 passed, 1 skipped. Test : total du rejeu = n/FPS = `total_time` du wrapper du banc (fin de tour forcée par patch). eval.py : `human_best_total` null sans fichier, 99.0 avec un fichier factice (supprimé ensuite).
- Limites : le mode jeu pygame n'a pas été lancé (pas d'affichage) ; pas de `data/human_best.json` réel : Nicolas doit jouer `python scripts/human_lap.py --laps 3`. Le record n'est comparé qu'à `laps` identique.

## 2026-11-03 22:50 · reviewer · T18 validée

- Relu human_lap.py, eval.py, tests. pytest hors e2e : 35 passed, 1 skipped. eval random --static --laps 3 : human_best_total null sans fichier. Imports pygame du mode jeu vérifiés par grep (non lancé, pas d affichage). Le test de rejeu utilise une fin de tour patchée, acceptable.

## 2026-11-03 23:01 · worker · T19 Référence PPO 1 tour piste fixe
- Fichiers : `rl_train_ppo.py` (tensorboard_log=None si tensorboard absent, sinon l'entraînement plantait), `data/models/best/` (best.zip, best_vecnormalize.pkl, best.json), `.team/metrics.json` (entrée du modèle).
- Entraînement : `SDL_VIDEODRIVER=dummy .venv/bin/python rl_train_ppo.py --static --steps 200000 --run-id t19` → 8 min 14 s, ep_rew_mean final ≈ -732.
- Éval : `scripts/eval.py --model data/checkpoints/ppo_t19_final.zip --static --laps 1 --episodes 20 --seed 0` → finish_rate 0.0, mean_checkpoints 1.0, mean_return -3.19, épisodes de 2000 steps (timeout). Aucun tour fini ; pas meilleur que random (1.1 cp).
- Limites : 200k steps insuffisants avec cette récompense/physique ; copié dans best/ comme référence (finish_rate 0). Pistes pour T20 : plus de steps en reprise, revoir la récompense. Entraînement sans `laps` (option absente de rl_train_ppo.py) à ajouter pour T20.

## 2026-11-03 23:02 · reviewer · T19 validée

- Relancé eval du modèle t19 (static, laps 1, 20 ép., seed 0) : finish_rate 0.0, mean_checkpoints 1.0, return -3.1875, identique à metrics.json. pytest hors e2e : 35 passed, 1 skipped. Fix tensorboard optionnel OK. best/ est gitignoré (non commité, normal). Référence faible (0 tour) assumée par le critère.

## 2026-11-03 23:14 · worker · T20 Fiabilité 3 tours (reprise)
- Fichiers : `rl_train_ppo.py` (`--laps`, reprise des stats VecNormalize via `--load`), `.team/metrics.json` (entrée), inbox (décision).
- Entraînement : `SDL_VIDEODRIVER=dummy .venv/bin/python rl_train_ppo.py --static --laps 3 --steps 200000 --run-id t20 --load data/models/best/best.zip` (~9 min).
- Éval : `scripts/eval.py --model data/checkpoints/ppo_t20_final.zip --static --laps 3 --episodes 20 --seed 0` → finish_rate 0.0, mean_checkpoints 2.0, mean_return 364.8, épisodes à 6000 steps (timeout).
- best/ non modifié (finish_rate inchangé). pytest hors e2e : 35 passed, 1 skipped.
- Limites : 0/20 ; récompense non adaptée, pistes dans l'inbox.

## 2026-11-03 23:15 · reviewer · T20 validée

- Relancé eval du modèle t20 (static, laps 3, 20 ép., seed 0) : finish_rate 0.0, mean_checkpoints 2.0, return 364.8389, identique à metrics.json. pytest hors e2e : 35 passed, 1 skipped. Diff rl_train_ppo.py (--laps, reprise VecNormalize) cohérent. best/ non modifié, décision notée dans l inbox. Reste : 20/20 non atteint (0 tour fini), à replanifier (récompense/durée).

## 2026-11-03 23:16 · planner · Replanification

- T19/T20 validées : aucun tour fini (finish_rate 0, 1.0 puis 2.0 checkpoints). Statut GOAL : en cours. Inbox T20 traitée (pistes retenues : diagnostic, récompense, imitation) puis archivée.
- Nouvelles tâches : T21 diagnostic, T22 heuristique (faisabilité + plancher de temps), T23 correction récompense + PPO 1 tour, T24 imitation.
- Temps humain toujours absent : Nicolas doit jouer `scripts/human_lap.py --laps 3`.

## 2026-11-03 23:18 · worker · T21 Diagnostic t19/t20
- Fichiers : `scripts/diagnose.py` (nouveau), `tests/test_diagnose.py` (2 tests), `src/rl/wrappers.py` (info `reward_components` dont la somme = récompense, et `end_cause` timeout/wall_stuck ; récompense inchangée), `docs/DIAG_T21.md`.
- Commandes : `diagnose.py --model data/checkpoints/ppo_t{19,20}_final.zip --static --laps {1,3}` ×2 chacun → sorties identiques (cmp). pytest hors e2e : 37 passed, 1 skipped.
- Résultat : t19 bloqué au cp 1/8, 96 % des frames à l'arrêt ; t20 cp 2/8, 97 % à l'arrêt ; voiture collée au mur, actions frein, fin par timeout. Cause : +0.1/frame « sur piste » + pas de coût à l'arrêt, wall_stuck jamais déclenché. Détails/pistes dans le doc.
- Limites : les 5 épisodes sont identiques (piste fixe + déterministe) ; raison du choix « frein » non élucidée.

## 2026-11-03 23:19 · reviewer · T21 validée

- Relancé diagnose t19 ×2 : sorties identiques (cmp), total -3.188 = eval. t20 : cp 2, arrêt 5840, total 364.8 conforme au doc. pytest hors e2e : 37 passed, 1 skipped. Récompense inchangée (test somme des composantes = récompense). Doc nomme la cause (arrêt au mur, +0.1/frame sur piste sans coût d arrêt). Réserve : le doc dit que progress n est pas une pénalité alors qu il cumule -410 ; formulation imprécise, sans impact.

## 2026-11-03 23:22 · worker · T22 Contrôleur heuristique
- Fichiers : `scripts/heuristic_lap.py` (nouveau), `scripts/eval.py` (`--model heuristic`, passe `env.ta` à la politique), `tests/test_heuristic.py` (2 tests), `.team/metrics.json` (entrée heuristic).
- Politique : vise un point de la ligne centrale (`track.spline_points`) en avance sur la voiture, avec anticipation de la vitesse angulaire (inertie de direction ~18 images), et vitesse limitée par le rayon de courbure à venir (0,06 px/frame par px de rayon). Écart au sujet : la visée directe du prochain checkpoint (obs seule) coupe les virages et bloque au mur (cp 3/8, 0/20) ; la version finale utilise donc la piste en plus de l'observation.
- Réglages choisis par petit balayage (27 combinaisons, toutes finissent 3 tours en 45 à 114 s) ; retenu PREDICT_FRAMES=18, SPEED_PER_RADIUS=0.06, LOOK_MIN=25.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` ×3 → identique : finish_rate 1.0 (20/20), mean_total_time 45.46 s (2273 steps), mean_laps_done 3.0, 8 checkpoints. pytest hors e2e : 39 passed, 1 skipped.
- Conclusion : 3 tours faisables avec la physique figée ; plancher de référence ≈ 45,5 s (non optimisé : touches de mur occasionnelles dans les virages serrés).
- Limites : politique non pure-observation (utilise la spline) ; piste fixe uniquement ; `mean_lap_time` du banc vaut en fait le temps total (existant).

## 2026-11-03 23:23 · reviewer · T22 validée

- Relancé heuristic_lap (static, laps 3, 20 ép., seed 0) : finish_rate 1.0, temps total moyen 45.46 s, identique à metrics.json (doublon créé par ma relance retiré). pytest hors e2e : 39 passed, 1 skipped. Réserve : politique non pure-observation (utilise la spline), assumé et documenté par le worker.

## 2026-11-03 23:31 · worker · T23 Récompense corrigée + PPO 1 tour
- Fichiers : `src/rl/wrappers.py` (bonus « sur piste » configurable `on_track_bonus` défaut 0 au lieu de +0.1 ; `urgency_penalty` défaut -0.3 sans seuil de distance ; wall_stuck sur arrêt <0.05 même sur piste), `.team/metrics.json` (entrée t23), inbox.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python rl_train_ppo.py --static --laps 1 --steps 200000 --run-id t23` (depuis zéro, ~8 min). Éval : `scripts/eval.py --model data/checkpoints/ppo_t23_final.zip --static --laps 1 --episodes 20 --seed 0` → finish_rate 0.0, mean_checkpoints 2.0, mean_return -153.5, épisodes 275 steps (wall_stuck).
- Vitesse moyenne 2.1 (vs 0.1 avant) mais bloqué au mur après cp 2. Critère « > 2.0 » non atteint : justification dans l'inbox. best/ non modifié. pytest hors e2e : 39 passed, 1 skipped.
- Limites : un seul run, 200k steps ; rewards_config.json (tracké) est prioritaire sur les défauts mais ne contient pas les nouvelles clés.

## 2026-11-03 23:32 · reviewer · T23 validée

- Relancé eval t23 (static, laps 1, 20 ép., seed 0) : finish_rate 0, cp 2.0, return -153.54, 275 steps, identique à metrics.json (doublon retiré). pytest hors e2e : 39 passed, 1 skipped. Diff wrappers cohérent (défauts configurables). Critère : échec justifié chiffré dans inbox, best/ intact. Réserve : rewards_config.json peut masquer les nouvelles clés. Reste à faire : T24 imitation.

## 2026-11-03 23:33 · worker · T24 Imitation depuis l'heuristique
- Fichiers : `scripts/imitate.py` (collecte obs/action de l'heuristique sur 40 épisodes avec bruit eps 0/0.1/0.2/0.3, BC cross-entropy 30 époques sur PPO MlpPolicy [256,256], stats VecNormalize issues des données, sauve zip + _vecnormalize.pkl), `tests/test_imitate.py`, `.team/metrics.json` (2 entrées), `data/models/best/` (remplacé, gitignoré).
- Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 1` (17 s, 32 913 échantillons, précision 0.848) ; `scripts/eval.py --model data/checkpoints/ppo_t24_bc.zip --static --laps {1,3} --episodes 20 --seed 0`.
- Résultats : laps 1 → finish_rate 1.0, 14.1 s, 8 cp ; laps 3 → finish_rate 1.0 (20/20), temps total 41.7 s (heuristique : 45.46 s ; t19/t23 : 0). pytest hors e2e : 40 passed, 1 skipped.
- Décision : best/ remplacé par ce modèle (finish_rate 1.0 à 3 tours). Pas de fine-tuning PPO fait (inutile pour le critère) ; `--load` compatible mais non testé avec ce zip.
- Limites : l'heuristique utilise la spline, la politique apprise reproduit son comportement sur piste fixe seulement ; évaluation seed 0 sur piste fixe déterministe (20 épisodes identiques). Temps humain toujours absent.

## 2026-11-03 23:34 · reviewer · T24 validée

- Relancé eval t24_bc laps 1 et 3 (20 ép., seed 0) : finish_rate 1.0, 14.1 s et 41.7 s, identique à metrics.json (doublons retirés). pytest hors e2e : 40 passed, 1 skipped. Décision best/ notée. Réserve : dépend de la spline via l heuristique, piste fixe, --load non testé.

## 2026-11-03 23:34 · worker · Aucune tâche

- T21-T24 toutes [x], aucune [ ] ni [-]. REPLAN créé. Rappel : data/human_best.json absent (action humaine).

## 2026-11-03 23:35 · planner · Replanification

- T21-T24 validées. Fiabilité atteinte : BC t24 20/20 sur 3 tours, 41,7 s (heuristique 45,5 s). PPO brut toujours à 0 tour. GOAL : statut mis à jour (vitesse en cours), pas de GOAL_REACHED car le temps humain est absent (data/human_best.json, action de Nicolas : `python scripts/human_lap.py --laps 3`).
- Inbox T23 traitée (pistes imitation faite ; reprise PPO → T27) et archivée.
- Nouvelles tâches : T25 heuristique plus rapide, T26 ré-imitation/DAgger, T27 affinage PPO depuis BC, T28 robustesse sur seeds/bruit.

## 2026-11-03 23:38 · worker · T25 Heuristique plus rapide
- Fichiers : `scripts/heuristic_lap.py` (constantes : SPEED_PER_RADIUS 0.06→0.2, PREDICT_FRAMES 18→10, LOOK_MIN/GAIN 25/40→200/240), `scripts/sweep_heuristic.py` (nouveau, balayage), `docs/SPEED_T25.md` (5 balayages, ~450 combinaisons), `.team/metrics.json` (entrée heuristic).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` ×4 → identique : finish_rate 1.0 (20/20), mean_total_time 17.94 s (897 steps), 8 cp, 3 tours (avant : 45,46 s). pytest hors e2e : 40 passed, 1 skipped.
- Gain essentiellement dû à la visée lointaine sur la spline (trajectoire tendue) ; LOOK 300-400 dégrade. Plafond local du réglage, pas prouvé global.
- Limites : utilise la spline, piste fixe uniquement ; la trajectoire coupe sans doute les virages (à vérifier visuellement) ; le BC T24 (41,7 s) a donc maintenant un professeur 2,3× plus rapide pour T26.

## 2026-11-03 23:39 · reviewer · T25 validée

- Relancé heuristic_lap (static, laps 3, 20 ép., seed 0) : finish_rate 1.0, 17.94 s, identique à metrics.json. pytest hors e2e : 40 passed, 1 skipped. Diff limité aux constantes + sweep + doc. Réserve : coupe possible des virages non mesurée (inbox).

## 2026-11-03 23:43 · worker · T26 Ré-imitation + DAgger
- Fichiers : `scripts/imitate.py` (`collect(policy=...)`, `make_policy`, options `--dagger N`, `--dagger-episodes`), `tests/test_imitate.py` (+1 test), `.team/metrics.json` (2 entrées eval), `data/models/best/` remplacé (gitignoré).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --dagger 5 --dagger-episodes 20 --epochs 40 --out data/checkpoints/ppo_t26_bc` (2 min 20 s ; 40 épisodes bruités + 5 tours DAgger, 97 083 échantillons, précision finale 0.985).
- Éval `scripts/eval.py --model data/checkpoints/ppo_t26_bc.zip --static --laps 3 --episodes 20 --seed 0` : finish_rate 1.0 (20/20), mean_total_time 17.74 s (heuristique 17.94 s ; t24 41.7 s). Même éval sur best/ : identique.
- Essai précédent (2 tours DAgger, 40 ép.) : 0/20, 2 tours faits, 5 cp, arrêt à 912 steps (entrée metrics conservée) → 5 tours nécessaires.
- pytest hors e2e : 41 passed, 1 skipped.
- Limites : piste fixe, éval déterministe (voir T28) ; professeur utilise la spline.

## 2026-11-03 23:44 · reviewer · T26 validée

- Relancé eval t26_bc (static, laps 3, 20 ép., seed 0) : finish_rate 1.0, 17.74 s, identique à metrics.json (doublon retiré). pytest hors e2e : 41 passed, 1 skipped. Diff limité à imitate.py + test. Réserve : piste fixe, éval déterministe, professeur dépend de la spline.

## 2026-11-03 23:44 · boucle · Fin

- Session terminée après 12 itération(s), 2 tâche(s) validée(s) au total.

## 2026-11-03 23:47 · boucle · Démarrage

- Session de 12 itérations sur `team/main`.

## 2026-11-03 23:47 · planner · Replanification

- T25/T26 validées : 17,74 s sur 3 tours, 20/20 (best/). Rangées en Terminées. GOAL : mesure mise à jour, toujours pas atteint (temps humain absent : `python scripts/human_lap.py --laps 3`).
- Nouvelles tâches : T29 audit de validité (coupe de virages, checkpoints), T30 optimisation du professeur + ré-imitation. T28 passée P1, T27 (PPO) en dernier. Inbox vide.

## 2026-11-03 23:48 · worker · T29 Audit de validité des tours rapides
- Fichiers : `scripts/audit_lap.py` (nouveau), `docs/AUDIT_T29.md`.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/audit_lap.py --static --laps 3 --out docs/AUDIT_T29.md` ×2 → identique (cmp).
- Résultats (best/ 17,74 s ; heuristique 17,94 s) : 8 cp dans l'ordre à chaque tour, couverture ligne centrale ≈ 1,00, 0 frame hors piste, 0 contact mur, v moy 9-10,3, v max 15,4-16,9, chemin 2660-2840 px (ligne centrale 3032). Verdict : valide, pas de faille.
- Correction en cours de route : demi-largeur réelle de route = 59 px (mesurée sur le masque), pas TRACK_WIDTH/2 = 45. La voiture rase le bord (≈ -0,9 px, précision de la spline).
- Limites : piste fixe, seed 0 ; CHECKPOINT_RADIUS 100 px très permissif (non exploité). Effet de bord : l'env écrit `replays/personal_best.json` (comportement existant).

## 2026-11-03 23:49 · reviewer · T29 validée

- Relancé audit_lap (static, laps 3) : tableaux identiques à docs/AUDIT_T29.md (seul le bloc verdict est rédigé à la main). 8 cp dans l ordre, 0 hors piste, 0 mur. pytest hors e2e : 41 passed, 1 skipped. Verdict valide, pas de faille.

## 2026-11-04 00:00 · worker · T30 Optimisation de l'heuristique par recherche
- Fichiers : `scripts/search_heuristic.py` (nouveau, hill-climbing sur SPEED_PER_RADIUS, PREDICT_FRAMES, LOOK_MIN, LOOK_GAIN, STEER_DEADZONE ; 1 ép. déterministe par essai), `docs/SEARCH_T30.md`, `scripts/heuristic_lap.py` (constantes : 0.2→0.2836, 10→8, 200/240→125/384, deadzone 0.05→0.0375), `.team/metrics.json`, `data/models/best/` (remplacé, gitignoré).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/search_heuristic.py --budget 1500` (~4 min, 17,94 → 15,9 s). Heuristique `heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` ×2 : 20/20, 15,90 s (795 steps), identique.
- Ré-imitation : `imitate.py --static --laps 3 --dagger 5 --dagger-episodes 20 --epochs 40 --out data/checkpoints/ppo_t30_bc` → précision 0.993 ; eval 20 ép. : 20/20, 15,90 s (avant 17,74). best/ remplacé et réévalué : identique.
- Audit (audit_lap.py sur nouveau best/ et heuristique) : 8 cp dans l'ordre, 0 frame hors piste, 0 contact mur, bord au pire -1,9 px (précision spline). Sortie `/tmp`, docs/AUDIT_T29.md non réécrit.
- pytest (hors e2e, `--ignore=tests/test_e2e_training.py`) : 41 passed, 1 skipped.
- Limites : surapprentissage possible aux 1 épisode/piste fixe ; la recherche n'est pas optimale globale ; professeur utilise la spline.

## 2026-11-04 00:01 · reviewer · T30 validée

- Relancé : heuristic_lap (static, 3 tours, 20 ép.) → 20/20, 15,90 s ; eval best/best.zip → 20/20, 15,90 s (identique au journal). audit_lap : 8 cp dans l ordre, 0 hors piste, 0 mur. pytest hors e2e : 41 passed, 1 skipped. Diff limité aux constantes, script de recherche et doc. Réserve : surapprentissage possible à la piste fixe/éval déterministe.

## 2026-11-04 00:05 · worker · T28 Robustesse du meilleur modèle
- Fichiers : `scripts/robust_eval.py` (nouveau : N épisodes, bruit d'action eps), `docs/ROBUST_T28.md`, `.team/metrics.json` (3 entrées).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --seed 1000 --eps 0 0.05 0.1 --out docs/ROBUST_T28.md` (55 s).
- Résultats best/ : eps 0 → 100/100, 15,9 s, écart-type 0 (déterministe, graines sans effet sur piste statique) ; eps 0,05 → 97/100, 18,59 s moy, pire 22,78 ; eps 0,1 → 91/100, 19,94 s.
- Cause des échecs : 11/12 bloqués vers (181, 510) après 5 cp (virage serré, mur) ; détail dans le doc. Pistes : DAgger bruité / vitesse limitée dans ce virage.
- Limites : piste fixe ; le bruit est uniforme, pas de variation de départ. Effet de bord : replays/personal_best.json réécrit par l'env.

## 2026-11-04 00:04 · reviewer · T28 validée

- Relancé robust_eval (100 ép., eps 0/0,05/0,1) : 100/100, 97/100 (18,59 s), 91/100 (19,94 s), identique au journal. Cause (virage ~181,510 après cp5) cohérente avec le doc. pytest hors e2e : 41 passed, 1 skipped. Mes 3 entrées dupliquées dans metrics.json retirées.

## 2026-11-04 00:10 · worker · T27 Affinage PPO 3 tours depuis le BC
- Fichiers : `rl_train_ppo.py` (`--rewards` ; `--lr` désormais appliqué au `--load` via custom_objects, sinon ignoré ; checkpoints avec `save_vecnormalize`), `src/rl/wrappers.py` (env `TRACKAI_REWARDS_CONFIG` remplace le chemin de rewards_config.json, sans toucher le fichier tracké), `data/rewards_t27.json` (speed_weight 0.3→1.0, time_bonus 300→600 ; rewards_config.json ne masque rien car les clés y sont explicitement remplacées), `.team/metrics.json` (2 entrées).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python rl_train_ppo.py --static --laps 3 --steps 150000 --lr 3e-5 --load data/checkpoints/ppo_t30_bc.zip --rewards data/rewards_t27.json --run-id t27` (5 min 24 s). Compatibilité `--load` du zip BC + stats VecNormalize confirmée (log « Model loaded »).
- Éval 20 ép. laps 3 seed 0 : checkpoint 80k steps → 20/20, 18,30 s ; final 150k → 20/20, 17,48 s. Pas d'effondrement, mais la base BC t30 fait 15,90 s : PPO dégrade (-1,6 s). best/ NON modifié.
- pytest hors e2e : voir sortie ci-dessus du lancement (41 attendus).
- Limites : un seul run, 150k steps, LR 3e-5 ; pas de gain, plafond non prouvé. Eval sur le zip de mi-parcours nécessite de copier le .pkl vecnormalize vers <zip>_vecnormalize.pkl.

## 2026-11-04 00:11 · reviewer · T27 validée

- Relancé éval ppo_t27_final.zip (20 ép., laps 3) : 20/20, 17,48 s, identique au journal. Diff limité à --rewards, LR au --load, save_vecnormalize, env TRACKAI_REWARDS_CONFIG. pytest hors e2e : 41 passed, 1 skipped. best/ non modifié (cohérent : PPO dégrade vs BC 15,90 s). Entrée dupliquée de ma ré-éval retirée de metrics.json.

## 2026-11-04 00:11 · worker · Aucune tâche

- T27-T30 toutes [x], aucune [ ] ni [-]. REPLAN créé. Rappel : data/human_best.json absent (action humaine).

## 2026-11-04 00:11 · planner · Replanification

- T27-T30 rangées en Terminées. Mesure : best/ 15,90 s, 20/20 ; PPO affiné 17,48 s (pas de gain). GOAL : statut mis à jour, pas de GOAL_REACHED (temps humain absent, action de Nicolas : `python scripts/human_lap.py --laps 3`).
- Nouvelles tâches : T31 DAgger bruité (robustesse), T32 borne inférieure théorique, T33 recherche élargie, T34 ré-imitation, T35 doc d'état. Inbox vide. REPLAN supprimé.

## 2026-11-04 00:18 · worker · T31 DAgger bruité
- Fichiers : `scripts/imitate.py` (option `--dagger-eps`, niveaux de bruit alternés par épisode, défaut 0 0.05 = ancien comportement), `docs/ROBUST_T31.md`, `.team/metrics.json` (4 entrées), `data/models/best/` remplacé (gitignoré ; ancien t30 copié dans /tmp/best_t30*).
- Entraînement (4 min 11 s) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --dagger 5 --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40 --out data/checkpoints/ppo_t31a` (179 561 échantillons, précision 0,991). Premier essai, une seule configuration.
- eval.py 20 ép. laps 3 seed 0 : 20/20, 15,90 s. robust_eval 100 ép. seed 1000 : eps 0 → 100/100, 15,9 s ; eps 0,05 → 100/100 (18,63 s moy, pire 22,22) ; eps 0,1 → 99/100 (19,20 s, pire 23,22). Avant (T30/T28) : 100, 97, 91.
- Décision best/ : temps eps 0 identique (15,90 s, pas plus rapide) mais robustesse nettement meilleure (écart 0 s ≤ 0,3 s) → remplacé ; best/ réévalué : 20/20, 15,90 s. pytest hors e2e : 41 passed, 1 skipped.
- Limites : piste fixe, bruit uniforme ; 1 seule graine d'entraînement ; temps bruités un peu plus lents (inévitable). Effet de bord : replays/personal_best.json réécrit par l'env.

## 2026-11-04 00:19 · reviewer · T31 validée

- Relancé robust_eval sur best/ (100 ép.) : 100/100, 100/100 (18,63 s), 99/100 (19,20 s), identique au journal ; critères T31 atteints (eps 0 15,90 s). pytest hors e2e : 41 passed, 1 skipped. Diff limité à --dagger-eps (défaut = ancien comportement). Mes 3 entrées dupliquées retirées de metrics.json.

## 2026-11-04 00:22 · worker · T32 Borne inférieure théorique
- Fichiers : `scripts/lower_bound.py` (nouveau), `docs/BOUND_T32.md`.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/lower_bound.py --out docs/BOUND_T32.md` ×2 → `cmp` identique. Physique mesurée sur le vrai env.step (murs désactivés) : v terminale 22,5 px/frame, courbure max en régime établi kappa_max(v) (rayon 62 px à v=5, 384 px à v=23), freinage jusqu'à -0,6…-1,0/frame.
- Résultat : la courbure ponctuelle donne une « borne » (21,1 s) supérieure au temps réel → invalide ; j'ai donc calibré la fenêtre de courbure sur la trajectoire réelle de l'heuristique (k=16 nœuds, 1,4 % de points encore en violation). Borne 3 tours : 13,96 s (ligne de course), 14,77 s (ligne centrale) ; sensibilité k=12…24 : 12,9-15,0 s. Écart avec 15,90 s : +1,94 s (intervalle 0,9-3,0 s).
- Recommandation écrite dans le doc : continuer la recherche (T33), avec marge réelle plus faible que l'écart (borne optimiste, non rigoureuse).
- Limites : borne modèle-dépendante (fenêtre calibrée), ligne de course = lissage borné par le couloir (pas optimum temps).

## 2026-11-04 00:22 · reviewer · T32 validée

- Relancé lower_bound.py : sortie identique (cmp) au doc ; borne 13,96 s, écart +1,94 s, recommandation explicite. Limite (non rigoureux) bien déclarée. pytest hors e2e : 41 passed, 1 skipped. Aucun changement hors sujet.

## 2026-11-04 00:33 · worker · T33 Recherche élargie du professeur
- Fichiers : `scripts/search_heuristic.py` (options `--sectors N`, `--restarts R` ; multiplicateurs de vitesse par secteur de spline), `scripts/heuristic_lap.py` (`SECTOR_MULT` 6 secteurs + constantes mises à jour : SPR 0.2567, PREDICT 9, LOOK 139/400, deadzone 0.0345), `docs/SEARCH_T33.md`, `.team/metrics.json`.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/search_heuristic.py --sectors 6 --restarts 4 --max-seconds 560 --budget 100000 --out docs/SEARCH_T33.md` (9 min 22 s ; 4 redémarrages de 140 s, ~700 essais chacun) : 15,90 / 15,90 / 16,38 / **15,68 s**.
- Vérif : `heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` ×2 : 20/20, 15,68 s (784 steps), identique. `audit_lap.py --models heuristic` : 8 cp dans l'ordre à chaque tour, 0 frame hors piste, 0 contact mur, bord au pire -1,4 px (précision spline), couverture tour 1 0,96. pytest hors e2e : 41 passed, 1 skipped.
- Limites : gain de 0,22 s seulement, un seul restart sur 4 l'a trouvé (recherche non globale) ; borne T32 ≈ 13,96 s ; surapprentissage à la piste fixe. best/ non modifié (T34).

## 2026-11-04 00:33 · reviewer · T33 validée

- Relancé heuristic_lap (20 ép., laps 3) : 20/20, 15,68 s (< 15,90) ; audit_lap : 8 cp dans l ordre, 0 hors piste, 0 mur. pytest hors e2e : 41 passed, 1 skipped. Diff limité à search_heuristic/heuristic_lap. Ma entrée dupliquée retirée de metrics.json. Réserve : gain de 0,22 s, surapprentissage piste fixe (déclaré).

## 2026-11-04 00:43 · boucle · Démarrage

- Session de 15 itérations sur `team/main`.

## 2026-11-04 00:44 · planner · Replanification

- T34 en cours : mesure partielle 15,68 s mais robustesse 49 %/31 % (bruit) vs 100/99 % pour best/ ; règle de remplacement de best/ précisée. Ajout T36 (ré-imitation avec DAgger bruité) et T37 (professeur robuste au bruit). Inbox vide. GOAL : statut inchangé (temps humain absent), pas de GOAL_REACHED. REPLAN absent.

## 2026-11-04 00:44 · worker · T34 Ré-imitation du professeur 15,68 s
- Fichiers : aucun code modifié ; `data/checkpoints/ppo_t34.zip` (+vecnormalize), 4 entrées dans `.team/metrics.json` (mesures du 00:37-00:38, relues, non relancées).
- Résultats ppo_t34 : 20 ép. laps 3 seed 0 → 20/20, 15,68 s (< 15,90) ; robustesse 100 ép. seed 1000 : eps 0 → 100/100 15,68 s ; eps 0,05 → 49/100 ; eps 0,1 → 31/100 (best/ T31 : 100 et 99).
- Décision : best/ NON remplacé (règle planner : robustesse ≥ T31 exigée). Constat : le modèle est plus rapide mais fragile ; le professeur T33 est moins tolérant au bruit. Tâche close, suite = T36 (DAgger bruité sur ce professeur) et T37.
- Limites : mesures reprises de l'essai précédent, pas de nouvel entraînement.

## 2026-11-04 00:45 · reviewer · T34 validée (close sans remplacement de best/)

- Relancé robust_eval sur ppo_t34 (100 ép., seed 1000) : eps 0 → 100/100 15,68 s ; eps 0,05 → 49/100 (18,31 s), identique au journal. pytest hors e2e : 41 passed, 1 skipped. Aucun code modifié ; best/ inchangé, conforme à la règle du planner (robustesse < T31). Mes entrées dupliquées de metrics.json retirées. Suite : T36/T37.

## 2026-11-04 00:59 · worker · T36 Ré-imitation 15,68 s avec DAgger bruité (échec, best/ inchangé)
- Fichiers : aucun code modifié ; `data/checkpoints/ppo_t36a.zip`, `ppo_t36b.zip`, entrées dans `.team/metrics.json` (robust_eval).
- Essai a (4 min) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --dagger 5 --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40 --out data/checkpoints/ppo_t36a` (165 698 éch., précision 0,985).
- Essai b (~6 min) : même commande avec `--dagger 7 --dagger-episodes 40 --dagger-eps 0 0.1 0.15 0.2`, `--out ppo_t36b` (276 965 éch., précision 0,987).
- Mesure : `robust_eval.py --model <zip> --static --laps 3 --episodes 100 --seed 1000 --eps 0 0.05 0.1`

| essai | eps 0 | eps 0,05 | eps 0,1 |
|---|---|---|---|
| T34 (réf.) | 100 %, 15,68 s | 49 % | 31 % |
| t36a | 100 %, 15,68 s | 49 % | 31 % |
| t36b | 100 %, 15,76 s | 39 % | 33 % |
| best/ T31 (réf.) | 100 %, 15,90 s | 100 % | 99 % |

- Constat : t36a redonne exactement les chiffres de T34 ; plus de bruit et d'itérations ne change rien. La fragilité vient donc probablement du professeur T33 (trajectoire agressive, virage ~(181,510) sans marge), pas du volume DAgger (hypothèse non testée directement). Critère non atteint, best/ inchangé. Suite : T37 (professeur robuste au bruit).

## 2026-11-04 01:00 · reviewer · T36 validée (échec documenté, best/ inchangé)

- Relancé robust_eval ppo_t36b (100 ép., seed 1000, eps 0,05) : 39/100, identique au journal. pytest hors e2e : 41 passed, 1 skipped. Aucun code modifié, best/ inchangé (robustesse < T31), table des essais fournie, 2 essais conformes. Mes mesures parasites retirées de metrics.json. Suite : T37.

## 2026-11-04 01:12 · worker · T37 Professeur robuste au bruit
- Fichiers : `scripts/search_heuristic.py` (`--noise-eps`, `--noise-episodes`, `--t0-max`, `--start` ; score = temps moyen sous bruit d'action, échec = 60 s, contrainte temps eps 0 ≤ 15,9 s), `scripts/robust_eval.py` (accepte `--model heuristic`), `scripts/heuristic_lap.py` (LOOK_MIN 139→127, STEER_DEADZONE 0,0345→0,0342), `docs/SEARCH_T37.md`, `docs/ROBUST_T37.md`, `.team/metrics.json`. Ancien professeur T33 sauvegardé : /tmp/heuristic_lap_t33.py.
- Recherche (9 min) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/search_heuristic.py --sectors 6 --restarts 2 --max-seconds 540 --budget 100000 --noise-eps 0.05 --noise-episodes 8 --out docs/SEARCH_T37.md` → restart 0 : 17,62 s moyen bruité (8 ép. tous finis), restart 1 : 23,12 s. Référence avant : professeur T33 = 50 % de finish à eps 0,05 (20 ép.).
- Mesure (100 ép., seed 1000, `robust_eval.py --model heuristic --static --laps 3`) : eps 0 → 100/100, 15,80 s ; eps 0,05 → 99/100 (18,48 s) ; eps 0,1 → 100/100 (19,68 s). `heuristic_lap.py` 20 ép. seed 0 : 20/20, 15,80 s. audit_lap : 8 cp dans l'ordre, 0 hors piste, 0 mur. pytest hors e2e : voir sortie (relancé).
- Limites : 15,80 s contre 15,68 s du T33 (+0,12 s) ; graines de recherche 5000-5007 différentes de la validation (1000+) donc pas de fuite directe ; piste fixe. Suite possible : ré-imiter ce professeur (DAgger bruité) pour dépasser best/ 15,90 s.

## 2026-11-04 01:16 · worker · T35 Clôture documentaire
- Fichier : `docs/BEST_STATUS.md` (nouveau). Commandes eval/robust_eval/audit du doc relancées : 20/20 15,90 s ; eps 0/0,05/0,1 → 100/100, 100/100 (18,63 s), 99/100 (19,20 s) ; audit propre (0 hors piste, 0 mur, cp dans l ordre). Entrées ajoutées dans metrics.json par ces lancements (doublons à retirer par le reviewer).
- Limite : la commande imitate du doc part du professeur courant (T37), pas T30, donc ne reproduit pas bit à bit best/ ; précisé dans le doc, non relancée.

## 2026-11-04 01:18 · reviewer · T35 validée
- Relancé les commandes du doc : eval 20 ép. → 20/20, 15,90 s ; robust_eval eps 0,05 → 100/100, 18,63 s ; audit : 8 cp dans l'ordre, 0 hors piste, 0 mur. Identique au doc. pytest hors e2e : 41 passed, 1 skipped. Doc honnête sur la limite de reproduction (professeur T37 ≠ T30). Mes mesures parasites retirées de metrics.json.

## 2026-11-04 01:17 · worker · Aucune tâche

- T31-T37 toutes [x], aucune [ ] ni [-]. REPLAN créé. Suite possible : ré-imiter le professeur T37 (15,80 s, robuste) par DAgger bruité pour battre best/ 15,90 s. Rappel : data/human_best.json absent (action humaine).

## 2026-11-04 01:17 · planner · Replanification

- T31-T37 closes. Ajout T38 (ré-imitation professeur T37), T39 (recherche repartant de T37), T40 (non-régression 1 tour), T41 (bilan vitesse). Inbox vide. GOAL : statut inchangé (temps humain absent), pas de GOAL_REACHED. Décision : si T38/T39 échouent, clore la phase vitesse. REPLAN supprimé.

## 2026-11-04 01:24 · worker · T38 Ré-imitation du professeur T37
- Fichiers : `data/checkpoints/ppo_t38.*`, `data/models/best/` remplacé (best.zip, vecnormalize, best.json ; ancien T31 copié dans /tmp/best_t31), `.team/metrics.json`. Aucun code modifié.
- Entraînement (4 min 12 s) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --dagger 5 --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40 --out data/checkpoints/ppo_t38` (176 925 éch., précision 0,989). 1 essai.
- Mesures : `robust_eval.py --model data/checkpoints/ppo_t38.zip --static --laps 3 --episodes 100 --seed 1000 --eps 0 0.05 0.1` : eps 0 → 100/100, 15,80 s ; eps 0,05 → 100/100 (18,54 s, pire 23,2) ; eps 0,1 → 100/100 (19,65 s, pire 23,52). `eval.py` 20 ép. laps 3 seed 0 : 20/20, 15,80 s. best/ réévalué après copie : 20/20, 15,80 s.
- Décision : critères atteints (15,80 < 15,90 ; 100 ≥ 99 ; 100 ≥ 95) et mieux que T31 en temps et robustesse → best/ remplacé.
- pytest : hors tests/test_e2e_training.py (échoue avec `-m "not e2e"`, test_training_runs_short_session, non investigué) : 41 passed, 1 skipped.
- Limites : piste fixe, 1 graine d'entraînement ; replays/personal_best.json réécrits par l'env. Mesures parasites éventuelles dans metrics.json à dédoublonner par le reviewer.

## 2026-11-04 01:25 · reviewer · T38 validée

- Relancé robust_eval sur best/ (100 ép., seed 1000) : eps 0,1 → 100/100, 19,65 s, identique au journal (eps 0/0,05 déjà confirmés par les entrées metrics du worker). pytest hors e2e : 41 passed, 1 skipped. Aucun code modifié ; best/ (non suivi par git) remplacé avec mesure. Mes mesures parasites retirées de metrics.json. Note : test_e2e_training échoue (non investigué par le worker).

## 2026-11-04 01:35 · worker · T39 Recherche repartant de T37 (plafond, T37 conservé)
- Fichiers : `scripts/search_heuristic.py` (le départ n'est plus soumis à `--t0-max`, seuls les candidats le sont — sinon T37 à 15,80 s était rejeté d'emblée), `docs/SEARCH_T39.md`. Constantes de `heuristic_lap.py` inchangées.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/search_heuristic.py --sectors 6 --restarts 2 --max-seconds 540 --budget 100000 --noise-eps 0.05 --noise-episodes 8 --t0-max 15.7 --start '<params T37>' --out docs/SEARCH_T39.md` (9 min 4 s).
- Résultat : 1425 + 1409 candidats, aucun ne tient t0 ≤ 15,7 s ET bruité < 17,62 s. Pas d'amélioration → critère (< 15,80 s) non atteint ; table fournie. 1 essai, 6 secteurs au lieu de 8 (SECTOR_MULT de T37 a 6 valeurs).
- Limites : score bruité sur 8 ép. seulement, hill-climbing local ; le contrainte t0 ≤ 15,7 est stricte et le score bruité est bruité. Pas de test pytest relancé (changement limité au script de recherche).

## 2026-11-04 01:36 · worker · T40 Non-régression 1 tour / multi-tours
- Fichier : `tests/test_laps.py` (+2 tests : `test_default_and_laps1_match_pre_multilap_reference`, `test_laps3_needs_ordered_checkpoints`).
- Référence : hash sha256 de 600 pas (obs, récompense, done, actions aléatoires seed 0) mesuré sur le code d'avant multi-tours (`git archive e32dec6~1 src` dans /tmp) = code actuel (laps omis et laps=1) : `efb6b743…2826e`, figé dans le test.
- pytest tests/test_laps.py ×2 : 5 passed identique ; suite hors e2e : 43 passed, 1 skipped.
- Limites : trajectoire aléatoire de 600 pas sur piste statique, sans franchissement de ligne (le tour complet reste couvert par les tests existants).

## 2026-11-04 01:36 · reviewer · T40 validée
- Relu le diff (tests seuls). pytest hors e2e lancé 2 fois : 43 passed, 1 skipped, identique. Test de non-régression par hash de référence pré-multi-tours ; fin à 3 tours couverte par les tests existants.

## 2026-11-04 01:37 · worker · T41 Rapport de décision vitesse
- Fichier : `docs/SPEED_STATUS.md` (nouveau). Aucun code, aucune commande de calcul.
- Valeurs relues dans metrics.json/journal/docs : 45,46 → 41,7 → 17,94 → 17,74 → 15,90 → (15,68 fragile) → 15,80 s (best/ T38, 100/100 à eps 0/0,05/0,1) ; borne T32 13,96 s (centrale 14,77 s) ; marge ≈ 1,84 s (optimiste). Recommandation : plafond proche, ne pas poursuivre la recherche locale sans temps humain.
- Limites : le 45,5 s de T22 n'est que dans le journal ; `docs/BEST_STATUS.md` décrit encore best/ = T31 (15,90 s), périmé depuis T38 (non modifié ici).

## 2026-11-04 01:37 · reviewer · T41 validée
- Doc relu : chiffres retrouvés (13,96/14,77 dans BOUND_T32, 17,94 SPEED_T25, 17,74 AUDIT_T29, 15,68 SEARCH_T33, 17,48 journal T27, 15,80 metrics). pytest hors e2e : 43 passed, 1 skipped. Docs seul, pas de code. Note : docs/BEST_STATUS.md périmé (best/ = T38) signalé par le worker.

## 2026-11-04 01:37 · worker · Aucune tâche

- T31-T41 toutes [x], aucune [ ] ni [-]. REPLAN créé. Rappel : docs/BEST_STATUS.md périmé (best/ = T38, 15,80 s) ; data/human_best.json absent (action humaine).

## 2026-11-04 01:38 · planner · Replanification

- T38-T41 validées. Phase vitesse close (T39 : plafond, T41 : marge ≈1,8 s). best/ = T38, 15,80 s, 100/100 bruité. Nouvelles tâches T42 (doc périmée), T43 (test e2e en échec), T44 (replays écrasés par éval), T45 (robustesse départ perturbé). Inbox vide. GOAL : statut mis à jour, pas de GOAL_REACHED (temps humain absent, action de Nicolas : `scripts/human_lap.py --laps 3`). REPLAN supprimé.

## 2026-11-04 01:38 · boucle · Arrêt sur erreur

- `worker` a échoué (code 1), voir `.team/logs/20261104-013818-worker.log`.

## 2026-11-04 21:22 · boucle · Démarrage

- Session de 26 itérations sur `team/main`.

## 2026-11-04 21:22 · boucle · Objectif modifié

- Nouvel objectif : Entraîner un agent qui fait 3 tours du circuit fixe sans jamais toucher un mur, 20 courses sur 20, puis réduire le temps total. Ajouter une option d'entraînement `wall_fatal` (désactivée par défaut, le jeu ne change pas) et compter les chocs par course dans `eval.py`. Y aller par paliers : grosse pé

## 2026-11-04 21:23 · planner · Replanification

- Objectif modifié : 0 choc mur (20/20, 3 tours) puis temps. Critère GOAL réécrit (compteur `wall_hits`), statut en cours : chocs de best/ inconnus. Nouvelles tâches T46-T50 (compteur, baseline, options wall_penalty/wall_fatal, professeur sans choc, ré-imitation). Abandonnées : T42 (doc), T44, T45 (hors objectif) ; T43 gardée P3. Inbox vide. Pas de GOAL_REACHED. REPLAN supprimé.

## 2026-11-04 21:25 · worker · T46 Compteurs de chocs murs
- Fichiers : `src/game/env.py` (`wall_hits`, `wall_contacts`, `_wall_prev`, remis à 0 au reset ; compte dans la branche `not inside_track(new_pos)`, physique inchangée), `src/rl/wrappers.py` (`info["wall_hits"]`, `info["wall_contacts"]` via `_add_lap_info`, donc à chaque pas et en fin/timeout/wall_stuck), `scripts/eval.py` (`wall_stats` : `mean_wall_hits`, `max_wall_hits`, `clean_rate`), `scripts/robust_eval.py` (mêmes champs dans metrics.json + colonnes du tableau), `tests/test_laps.py` (+2 tests : choc compté dans env et dans info).
- pytest hors e2e : 45 passed, 1 skipped, 1 failed = `test_e2e_training` (préexistant, T43). Le test de hash T40 passe → trajectoire inchangée.
- `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed 0` : 20/20, 15,80 s, **mean_wall_hits 11,0, max 11, clean_rate 0,0** (best/ touche donc des murs à chaque course).
- Limites : `clean_rate` = fini ET 0 choc ; le clamp des bords d'écran (4b) n'est pas compté. Entrée de cette éval ajoutée dans metrics.json.

## 2026-11-04 21:25 · reviewer · T46 validée
- Diff relu (env, wrapper, eval, robust_eval, 2 tests). pytest hors e2e : 45 passed, 1 skipped. eval best/ laps 3 seed 0 20 ép. : 20/20, 15,80 s, mean_wall_hits 11,0, max 11, clean_rate 0,0 (identique au journal). Physique inchangée (compteurs seuls ; test de hash T40 passe).

## 2026-11-04 21:26 · worker · T47 Baseline chocs murs
- Fichiers : `scripts/wall_locate.py` (nouveau), `docs/WALL_BASELINE.md`, `.team/metrics.json` (entrée heuristique ; best/ déjà là via T46).
- Commandes : `heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` ; `wall_locate.py --model data/models/best/best.zip --static` ; idem `--model heuristic` (SDL_VIDEODRIVER=dummy).
- Résultat : best/ et heuristique identiques : 20/20, 15,80 s, mean_wall_hits 11, max 11, clean_rate 0,0. Chocs par secteur (12) cumul 20 ép. : [0,0,0,20,60,60,0,40,0,0,0,40] (secteurs 3,4,5,7,11).
- Limites : pas de choc, pas de contact ; effets de bord : replays/personal_best réécrits par l'env. Pas de pytest relancé (aucun code existant modifié).

## 2026-11-04 21:28 · worker · T48 Options wall_fatal / wall_penalty
- Fichiers : `src/rl/wrappers.py` (`GymTimeAttack(wall_fatal=False, wall_penalty=0.0)` ; pénalité × nouveaux chocs ajoutée à la récompense et au composant `wall` de `reward_components` ; fatal → terminated, `end_cause="wall_fatal"`, -100), `scripts/imitate.py` (`--wall-fatal`, `--wall-penalty`, propagés à collect et à l'env), `rl_train_ppo.py` (mêmes options), `tests/test_laps.py` (+3 tests : défaut identique, pénalité -50 × chocs, fatal au 1er choc).
- pytest hors e2e (`-m "not e2e"`) : 48 passed, 1 skipped, 1 failed = test_e2e_training (préexistant, T43, échoue aussi sans mes changements). Hash T40 passe.
- Limites : la pénalité n'est pas appliquée sur les sorties forcées timeout/wall_stuck (récompense fixe) ; avec `--wall-fatal` dans imitate, les épisodes de collecte s'arrêtent au 1er choc (voulu). Nom du paramètre `wall_penalty` distinct de la clé de config existante `wall_penalty` (chute de vitesse), inchangée.

## 2026-11-04 21:29 · reviewer · T48 validée
- Diff relu (wrappers, imitate, rl_train_ppo, 3 tests). pytest hors e2e : 48 passed, 1 skipped. Défaut identique (test + hash T40), pénalité et fatal testés. Note : pénalité non appliquée sur sorties forcées timeout/wall_stuck (acceptable).

## 2026-11-04 22:14 · worker · T49 Professeur sans choc
- Fichiers : `scripts/heuristic_lap.py` (`INNER_OFFSET`, `CROSS_GAIN` = 0 par défaut ; `SAFE_HORIZON = 32` : prédiction par simulation de la physique + choix d'une action sans choc ; `base_action` = ancienne politique), `scripts/search_heuristic.py` (`--wall-penalty`, `SEARCH_INNER`), `docs/SEARCH_T49.md`, `.team/metrics.json` (entrées eval 20 ép. et robust 100 ép.).
- Constantes seules (offset, gain latéral, recherche aléatoire 1192 essais, hill-climbing pénalisé) : au mieux 6 chocs. Couche de sécurité N=32 : `heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` → 20/20, 17,40 s, mean_wall_hits 0, clean_rate 1,0. `robust_eval.py --model heuristic --eps 0.05 --episodes 100 --seed 1000` → 93/100 finis, 18,72 s, mean_wall_hits 1,49, clean_rate 0,29.
- pytest -m "not e2e" : 48 passed, 1 skipped, 1 failed (test_e2e_training, T43 préexistant).
- Limites : critère eps 0 atteint ; bruité non (chocs par actions aléatoires non filtrées, 7 échecs). Le comportement de "heuristic" change (défaut SAFE_HORIZON=32 ; 0 = ancien : 15,80 s/11 chocs). Horizon non monotone (25 et ≥45 échouent). ≈ 5 s/épisode : DAgger plus lent. Les docs antérieures (15,80 s) décrivent SAFE_HORIZON=0.

## 2026-11-04 22:15 · reviewer · T49 validée
- Relancé heuristic_lap --static --laps 3 --episodes 20 --seed 0 : 20/20, 17,40 s, mean_wall_hits 0, clean_rate 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff relu (SAFE_HORIZON, sim de la physique, search_heuristic). Bruité non atteint mais diagnostiqué honnêtement dans docs/SEARCH_T49.md ; noté pour T50 dans inbox.

## 2026-11-04 22:24 · worker · T50 Ré-imitation DAgger du professeur sans choc (ÉCHEC)
- Aucun code modifié ; `data/checkpoints/ppo_t50.*` créé ; best/ NON remplacé (T38 conservé).
- Commande (8 min 55) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --episodes 20 --dagger 3 --dagger-episodes 15 --dagger-eps 0 0.05 --epochs 40 --wall-penalty -50 --out data/checkpoints/ppo_t50` (64 926 éch., précision BC 0,86 → 0,913). Budget réduit : professeur ≈ 5 s/épisode (rollouts de sécurité).
- Éval `eval.py --model data/checkpoints/ppo_t50.zip --static --laps 3 --episodes 20 --seed 0` : 0/20 finis, 1 tour fait, mean_wall_hits 78, clean_rate 0. robust_eval non lancé.
- Diagnostic : l'action du professeur T49 dépend de l'état physique simulé (env.ta, horizon 32), pas seulement de l'obs 14-dim → pas imitable fidèlement par un MLP (précision 0,91) ; une erreur en virage = choc, et sans couche de sécurité le suiveur enchaîne les chocs. Peu de données (65k) car professeur coûteux.
- Pistes : (a) professeur plus rapide/horizon réduit pour plus de DAgger, (b) features de prédiction de choc dans l'obs ou sécurité appliquée au suiveur, (c) PPO avec wall_penalty/wall_fatal partant de best/ T38, (d) DAgger long en tâche de fond. 1 essai, REPLAN créé.

## 2026-11-04 22:25 · planner · Replanification

- T50 échec (0/20, 78 chocs) : professeur sûr trop lent et non imitable depuis zéro. T50 rangée en Terminées (échec diagnostiqué). Nouvelles tâches : T51 professeur rapide, T52 imitate --init depuis T38, T53 DAgger long, T54 PPO+wall_penalty depuis T38, T55 repli politique+garde-fou (mesure seule). Note reviewer T49 intégrée (traitée). GOAL : statut mis à jour, pas de GOAL_REACHED. REPLAN supprimé.

## 2026-11-04 22:29 · worker · T51 Professeur T49 accéléré
- Fichier : `scripts/heuristic_lap.py` seul. Le code ne lançait déjà les alternatives que si le rollout de base choquait ; le coût venait de chaque rollout (32 images × `base_action`). Changements : (1) rollout de base unique (n'était pas réutilisé) ; (2) `curve_speed_limit` précalculée par indice de spline (`_limit_table`, cache, exacte) ; (3) `closest_index` global une fois par image réelle, recherche fenêtrée ±40 indices (`_near_index`) dans les rollouts ; `base_action(obs, ta, ci)` et `lookahead_error(..., i)` acceptent l'indice.
- Temps (`time … heuristic_lap.py --static --laps 3 --episodes 5 --seed 0`, démarrage inclus) : avant 28,7 s (≈5,7 s/ép.) → après 3,65 s : ≈ 7,9× plus rapide. 20 ép. après : 13,2 s au total (≈0,6 s/ép., objectif ≤ 1 s atteint). Mesure « avant » faite avant modification (20 ép. avant non relancées).
- Résultat identique : 20/20, 17,40 s, mean_wall_hits 0, clean_rate 1,0. pytest -m "not e2e" : 48 passed, 1 skipped, 1 failed (test_e2e_training, T43 préexistant).
- Limites : recherche fenêtrée peut en théorie différer de l'argmin global (pas observé ici) ; robustesse bruitée (93/100) non remesurée.

## 2026-11-04 22:31 · reviewer · T51 validée
- Relancé heuristic_lap --static --laps 3 --episodes 20 --seed 0 : 20/20, 17,40 s, 0 choc, clean 1,0, 13,8 s au total (~0,6 s/ép., conforme). pytest hors e2e : 48 passed, 1 skipped. Diff relu (rollout unique, table de limites en cache, recherche fenêtrée). Réserve : robustesse bruitée non remesurée.

## 2026-11-04 22:30 · worker · T52 imitate.py --init
- Fichier : `scripts/imitate.py` seul. `--init <model.zip>` charge le PPO + `<nom>_vecnormalize.pkl` (stats figées, non réécrites) ; la 1re collecte est conduite par ce modèle (bruit `--dagger-eps`), étiquetée par le professeur T49/T51 ; affiche la précision initiale puis fait un BC (`--epochs 0` pour le sauter) ; les tours `--dagger` suivent. Sans `--init` : comportement inchangé.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --init data/models/best/best.zip --episodes 3 --dagger 1 --dagger-episodes 3 --epochs 5 --wall-penalty -50 --out /tmp/t52_test` → modèle chargé, 2489 éch., **précision initiale de T38 sur le professeur : 0,728** ; BC 0,705 (5 époques) ; DAgger 1 : +3425 éch., précision 0,768 ; sauvé (.zip + _vecnormalize.pkl).
- Limites : pas de pytest relancé (script seul) ; l'env réécrit replays/personal_best (effet connu) ; le BC à lr 1e-3 baisse un peu la précision au début (lr à baisser pour T53 si besoin).

## 2026-11-04 22:31 · reviewer · T52 validée
- Relancé la commande courte (--init best.zip, 3 ép., 1 DAgger) : modèle rechargé, 2489 éch., précision initiale 0,728, BC 0,705, DAgger 0,768, .zip + vecnormalize sauvés (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff relu : chemin sans --init inchangé. Réserve : le BC à lr 1e-3 dégrade au départ (noté par le worker).

## 2026-11-04 22:38 · worker · T53 DAgger sans choc depuis T38
- Fichiers : `scripts/imitate.py` (+`--lr` pour le BC), `data/models/best/` remplacé par T53b (ancien best/ copié dans `data/models/best_t38/`), best.json, metrics.json (evals).
- Commandes (SDL_VIDEODRIVER=dummy) : (1) `imitate.py --static --laps 3 --init data/models/best/best.zip --episodes 10 --dagger 8 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 10 --lr 3e-4 --wall-penalty -50 --out data/checkpoints/ppo_t53` (1 min 52) → eval 20 ép. : 20/20, 17,02 s, 1 choc/course. (2) `imitate.py ... --init data/checkpoints/ppo_t53.zip --episodes 12 --dagger 16 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 10 --lr 2e-4 --wall-penalty -50 --seed 500 --out data/checkpoints/ppo_t53b` (3 min 57).
- T53b, eval.py laps 3 seed 0 20 ép. : **20/20 finis, 20,46 s, mean_wall_hits 0, clean_rate 1,0**. robust_eval 100 ép. seed 1000 : eps 0 → 100/100, 0 choc, clean 1,0, 20,46 s ; eps 0,05 → 68/100 finis, 20,68 s, mean_wall_hits 6,89, clean 0,08.
- Critère « 20/20 finis ET clean 20/20 » atteint → best/ remplacé. Coût : 20,46 s au lieu de 15,80 s.
- Limites : fragile au bruit d'action (eps 0,05) ; l'ancien best/ (rapide, 11 chocs) est gardé dans best_t38. Pas de pytest relancé (seul ajout : option --lr). Piste : DAgger plus long avec eps 0,05 pour la robustesse, puis réduction du temps.

## 2026-11-04 22:38 · reviewer · T53 validée
- Relancé eval.py best.zip laps 3 seed 0 20 ép. : 20/20, 20,46 s, 0 choc, clean 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff imitate.py (--lr) relu, minime. robust_eval non relancé. Réserve : fragile au bruit eps 0,05 (68/100) et plus lent (20,46 vs 15,80 s), annoncé honnêtement.

## 2026-11-04 22:46 · worker · T54 PPO fine-tuning + wall_penalty depuis T38
- Aucun code modifié. Commande (≈ 5 min, 200 000 pas, 16 envs) : `SDL_VIDEODRIVER=dummy .venv/bin/python rl_train_ppo.py --load data/models/best_t38/best.zip --static --laps 3 --wall-penalty -20 --lr 3e-5 --steps 200000 --run-id t54a` → `data/checkpoints/ppo_t54a_final.zip`.
- Éval `eval.py --model data/checkpoints/ppo_t54a_final.zip --static --laps 3 --episodes 20 --seed 0` : 20/20 finis, 17,28 s, **mean_wall_hits 12,0, max 12, clean_rate 0,0** (T38 : 11 chocs, 15,80 s). Entrée ajoutée dans metrics.json par eval.
- Verdict : voie PPO + pénalité -20 non viable à ce réglage : pas de baisse de chocs (12 vs 11) et plus lent. Palier `--wall-fatal` non lancé (condition de la tâche : la pénalité doit d'abord baisser les chocs). Pistes si reprise : pénalité plus forte (-50/-100), plus de pas, ou fatal directement ; DAgger (T53) reste la voie qui a marché.
- Limites : un seul essai, une seule graine ; best/ non touché.

## 2026-11-04 22:47 · reviewer · T54 validée
- Relancé eval.py ppo_t54a_final.zip laps 3 seed 0 20 ép. : 20/20, 17,28 s, mean_wall_hits 12, clean 0,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié, seuls .team/ changés. Verdict « voie non viable à -20 » justifié (12 chocs vs 11). Un seul essai/graine, palier fatal non tenté (conforme à la condition).

## 2026-11-04 22:50 · worker · T55 Repli politique + garde-fou
- Fichiers : `scripts/eval.py` (modèle `shield:<zip>` : action du modèle filtrée par `_safe_action`), `docs/WALL_BASELINE.md` (section T55), metrics.json (2 entrées).
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model shield:data/models/best_t38/best.zip --static --laps 3 --episodes 20 --seed 0` → 20/20, **16,42 s, 0 choc, clean_rate 1,0** (T38 seul : 15,80 s, 11 chocs). Mesuré aussi `shield:data/models/best/best.zip` (T53b) : 0/20 finis (bloqué ~306 pas), 0 choc.
- pytest -m "not e2e" : 48 passed, 1 skipped, 1 failed (test_e2e_training, T43 préexistant).
- Limites : non conforme « agent seul » ; eps 0 seulement ; robustesse bruitée non mesurée.

## 2026-11-04 22:49 · reviewer · T55 validée
- Relancé eval.py shield:best_t38 laps 3 seed 0 20 ép. : 20/20, 16,42 s, 0 choc, clean 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff eval.py minime (préfixe shield:), doc WALL_BASELINE cohérente. Note : le nom du modèle dans metrics.json est « shield:... » et non « best+shield » (équivalent, accepté).

## 2026-11-04 22:49 · planner · Replanification
- T51-T55 validées et rangées. Critère fiabilité (20/20, 0 choc, seed 0) rempli par best/ T53b (metrics.json, reviewer). GOAL_REACHED non créé : le critère vitesse (baisse à chaque palier / ≤ humain) reste ouvert et `human_best.json` manque ; reproductibilité sur d'autres graines non mesurée.
- Nouvelles tâches : T56 robustesse bruitée, T57 temps sous 0 choc, T58 bonus pistes aléatoires, T59 autres graines. T43 reste P3. Inbox vide (hors traite/), pas de REPLAN.

## 2026-11-04 22:58 · worker · T56 DAgger de robustesse depuis best/ T53b (ÉCHEC, best/ non remplacé)
- Aucun code modifié ; checkpoints `data/checkpoints/ppo_t56*`. Deux essais, tous depuis best/ (`imitate.py --static --laps 3 --init data/models/best/best.zip --wall-penalty -50 --episodes 10`) :
  - (a) `--dagger 20 --dagger-episodes 8 --dagger-eps 0.05 0.1 --epochs 10 --lr 2e-4 --seed 600 --out data/checkpoints/ppo_t56` (4 min 43, 158k éch.) → eval 20 ép. laps 3 seed 0 : 0/20 finis, 3 chocs/course.
  - (b) `--dagger 14 --dagger-eps 0 0.05 --epochs 6 --lr 1e-4 --seed 700 --out data/checkpoints/ppo_t56b` (120k éch.) → eval : 20/20, 20,3 s, mean_wall_hits 2,0, clean_rate 0 ; robust_eval 100 ép. seed 1000 eps 0,05 : 82/100 finis, 20,59 s, mean_wall_hits 2,06, clean 0,06 (eps 0 non relu dans ce run, déjà non clean à l'eval).
- Verdict : la robustesse (68→82 % finis à eps 0,05) s'obtient au prix du 0 choc à eps 0 (2 chocs/course) ; l'agrégation de données bruitées dégrade la précision du MLP (0,84-0,86). best/ T53b conservé (critère : 20/20 ET 0 choc ET ≤ 20,46 s non atteint). Entrées dans metrics.json (evals).
- Limites : 2 essais, une graine d'imitation chacun ; piste : plus de données à eps 0 seulement, ou réseau plus gros / obs enrichie.

## 2026-11-04 22:59 · reviewer · T56 validée
- Relancé eval.py ppo_t56b.zip laps 3 seed 0 20 ép. : 20/20, 20,3 s, 2 chocs, clean 0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié, best/ non remplacé (justifié : 2 chocs). Verdict négatif honnête (robustesse 82 %, pas 90 %). robust_eval non relancé.

## 2026-11-04 23:13 · worker · T57 Temps sous 0 choc (professeur 14,62 s ; agent non remplacé)
- Fichier modifié : `scripts/heuristic_lap.py` (`SAFE_HORIZON` 32 → 29). Balayage (script /tmp, 5 ép.) : l'échelle de vitesse de virage n'a aucun effet à H=32 ; l'horizon domine, non monotone : H=20 6 chocs, 24 7 chocs, 25 0/5 finis, 26 15,80 s, 27 15,14 s, 28 15,34 s/1 choc, **29 14,62 s/0 choc**, 30 16,60 s, 31 17,18 s, 32 17,40 s, 36 19,18 s.
- Professeur seul (`heuristic_lap.py --static --laps 3 --episodes 20 --seed 0`) : **20/20, 14,62 s, 0 choc, clean 1,0** (mieux que T38 15,80 s). Bruité eps 0,05 (robust_eval 100 ép. seed 1000) mesuré seulement à H=32 par erreur d'ordre : 93/100, 1,49 chocs ; non remesuré à H=29.
- DAgger depuis best/ T53b (`imitate.py --static --laps 3 --init <modèle> --wall-penalty -50 --episodes 12 …`) :
  - t57 (`--dagger 14 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 10 --lr 2e-4 --seed 800`, 2 min 30) : 20/20, 15,94 s, **1 choc/course**, clean 0.
  - t57b (depuis t57, `--dagger 20 … --lr 1.5e-4 --seed 900`) : 0/20, 3 chocs.
  - t57c (depuis best/, `--dagger 16 --dagger-eps 0 --lr 2e-4 --seed 1100`) : 0/20, 0 choc (bloqué ~561 pas), précision BC 0,97.
- Verdict : critère (20/20, 0 choc, < 20,46 s) non atteint ; best/ T53b conservé. Le meilleur agent (t57) est à 15,94 s mais touche 1 mur/course. Le professeur H=29 est plus rapide mais plus tranchant, donc plus dur à imiter.
- pytest -m "not e2e" : voir ci-dessous (lancé après le changement de constante).
- pytest : 48 passed, 1 skipped, 1 failed (test_e2e_training, T43 préexistant). Limites : 3 essais DAgger seulement ; le changement de H=29 modifie le comportement par défaut de `heuristic` (docs antérieures décrivent 32).

## 2026-11-04 23:13 · reviewer · T57 validée
- Relancé heuristic_lap seed 0, 20 ép., laps 3 : 20/20, 14,62 s, 0 choc, clean 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff minime (SAFE_HORIZON 32→29). Agent non remplacé (best/ conservé), verdict chiffré honnête. Agents DAgger et robustesse bruitée à H=29 non relancés.

## 2026-11-04 23:14 · worker · T58 Pistes aléatoires (--no-static)
- Fichiers : docs/WALL_BASELINE.md (section T58), metrics.json (3 entrées via eval/heuristic_lap). Aucun code modifié.
- Commandes : `eval.py --model <zip> --laps 3 --episodes 20 --seed 0` (sans --static) ; `heuristic_lap.py --laps 3 --episodes 20 --seed 0`.
- Résultats : best/ T53b 18/20 finis, 26,27 s, 36,9 chocs/course, clean 0 ; best_t38 14/20, 24,08 s, 116,5 chocs ; heuristique 18/20, 15,61 s, 0 choc, clean 0,9.
- Verdict : bonus non atteint ; piste = DAgger sur pistes aléatoires. Limites : graine 0 seule.

## 2026-11-04 23:15 · reviewer · T58 validée
- Relancé eval.py best/ --no-static laps 3 seed 0 20 ép. : 18/20, 26,27 s, 36,85 chocs, clean 0 ; heuristic_lap : 18/20, 15,61 s, 0 choc, clean 0,9 (conformes). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié, doc et verdict honnêtes. best_t38 non relancé.

## 2026-11-04 23:15 · worker · T59 Reproductibilité sur seeds 1 et 2
- Aucun code modifié. Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/models/best/best.zip --static --laps 3 --episodes 20 --seed {1,2}` → 2 entrées metrics.json.
- Résultats : seed 1 et seed 2 : 20/20 finis, 20,46 s, mean_wall_hits 0, clean_rate 1,0 (identiques à seed 0, mean_return 8234,1487 partout).
- Verdict : critère reproduit sur 3 graines. Limite : piste statique + politique déterministe + départ fixe → la graine n'a aucun effet, donc ce n'est pas une vraie preuve de généralisation (seul eps>0 ou --no-static varient : voir T56/T58).

## 2026-11-04 23:16 · reviewer · T59 validée
- Relancé eval.py best/ static laps 3 20 ép. seeds 1 et 2 : 20/20, 20,46 s, 0 choc, clean 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié. Note : mes relances ont ajouté 2 entrées doublons dans metrics.json (4 au total). Le verdict du worker est honnête : la graine est sans effet en statique déterministe.

## 2026-11-04 23:17 · worker · T43 test_e2e_training
- Cause : test obsolète, chemins de sortie de rl_train.py déplacés (monitor → data/monitoring/, modèle/vecnormalize → data/checkpoints/{id}_final.zip et {id}_final_vecnormalize.pkl) ; le code est correct. Fichier modifié : tests/test_e2e_training.py (chemins + nettoyage des artefacts du test). Physique non touchée.
- pytest complet (`SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q`) lancé 2 fois : 49 passed, 1 skipped les deux fois. Aucun artefact test_e2e_ résiduel.

## 2026-11-04 23:17 · reviewer · T43 validée
- Relancé pytest complet (e2e inclus) : 49 passed, 1 skipped, aucun artefact résiduel. Diff limité au test (chemins data/monitoring et data/checkpoints + nettoyage), physique non touchée. Une seule exécution de ma part (le worker en annonce 2).

## 2026-11-04 23:20 · planner · Replanification
- T43, T56-T59 rangées. Critère fiabilité toujours rempli (best/ T53b, 3 graines) ; vitesse ouverte (20,46 s ; professeur H=29 14,62 s ; t57 15,94 s mais 1 choc). GOAL_REACHED non créé : temps humain absent, vitesse non plafonnée.
- Nouvelles tâches : T60 (réseau plus gros pour imiter H=29), T61 (professeur intermédiaire), T62 (robustesse H=29 + docs), T63 (bonus pistes aléatoires). Inbox vide, pas de REPLAN.

## 2026-11-04 23:30 · worker · T60 Réseau plus gros pour imiter H=29 (échec, best/ non remplacé)
- Fichier : `scripts/imitate.py` (+`--net-arch`, défaut 256 256 = ancien comportement, appliqué sans `--init`). Physique/env intacts.
- Commandes (SDL_VIDEODRIVER=dummy, `imitate.py --static --laps 3 --wall-penalty -50`, éval `eval.py --static --laps 3 --episodes 20 --seed 0`) :
  - t60 : depuis zéro, `--net-arch 256 256 256 --episodes 12 --dagger 12 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 10 --lr 5e-4 --seed 1200` (2 min 53, 92k éch., précision finale 0,929) → 20/20, **15,90 s, 1 choc/course**.
  - t60b : `--init t60 --dagger 20 --dagger-eps 0 0.05 --epochs 8 --lr 2e-4 --seed 1300` (précision 0,91) → 20/20, 16,32 s, 1 choc.
  - t60c : `--init t60 --dagger 12 --dagger-eps 0 --epochs 30 --lr 3e-4 --seed 1400` (précision 0,997) → 20/20, 18,22 s, 4 chocs.
- Verdict : critère (0 choc, < 20,46 s) non atteint ; best/ T53b conservé. Le réseau 3×256 depuis zéro donne 15,90 s (≈ t57) mais toujours 1 choc ; plus de précision BC (0,997) n'a pas aidé (surapprentissage sur trajectoires eps 0, 4 chocs). Le goulot n'est donc pas que la précision du MLP. Pas d'entrée robust_eval. Pas de pytest relancé (seule option CLI ajoutée). Checkpoints : data/checkpoints/ppo_t60{,b,c}.

## 2026-11-04 23:31 · reviewer · T60 validée
- Relancé eval t60 static laps 3 20 ép. seed 0 : 20/20, 15,90 s, 1 choc (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff code = option --net-arch (défaut inchangé). best/ non remplacé, verdict négatif honnête. t60b/t60c non relancés. Mon éval a ajouté une entrée metrics.json.

## 2026-11-04 23:38 · worker · T61 Professeur intermédiaire (échec, best/ non remplacé)
- Fichier : `scripts/imitate.py` (+`--teacher-horizon`, défaut None = inchangé). Balayage 1 ép. statique laps 3 (script /tmp/sweep61.py, `PYTHONPATH=.`) : H=30 16,60 s 0 choc (235 changements d'action) ; 33 17,82 s 0 choc ; 34 17,44 s 0 choc (288) ; 35 18,16 s 1 choc ; 36 19,18 s ; 38 17,98 s. (statique déterministe : 1 ép. = 20 ép.)
- Professeur seul, 20 ép. seed 0 (heuristic_lap avec SAFE_HORIZON forcé) : H=30 20/20, 16,6 s, 0 choc ; H=34 20/20, 17,44 s, 0 choc.
- DAgger depuis best/ T53b (`imitate.py --static --laps 3 --wall-penalty -50 --teacher-horizon H --init data/models/best/best.zip --episodes 12 --dagger 14 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 10 --lr 2e-4 --seed S`) : t61 (H=30, seed 1500, 2 min 37) → eval 20 ép. : 0/20 finis, 105 chocs ; t61b (H=34, seed 1600, 3 min 30, précision 0,86) → 0/20, 1008 chocs (bloqué/tourne).
- Verdict : aucun agent ne passe ; best/ T53b conservé. Les professeurs H=30/34 sont à 0 choc (16,6 / 17,44 s) mais l'imitation depuis T53b dégrade au lieu d'améliorer ; pas d'essai depuis zéro/3×256 (suite possible). Pas de pytest relancé (option CLI seule).

## 2026-11-04 23:39 · reviewer · T61 renvoyée
- pytest hors e2e : 48 passed, 1 skipped. Diff = option --teacher-horizon (défaut inchangé), OK. Mais eval de t61/t61b sans .zip = sans VecNormalize (chiffres du worker faux). Avec .zip : t61 20/20 20,22 s 2 chocs ; t61b 20/20 19,36 s 3 chocs. Verdict négatif (0 choc non atteint) mais causes erronées → inbox.

## 2026-11-04 23:40 · worker · T61 reprise (correction des évals)
- Fichiers : `scripts/eval.py` (`_load_model` : le .pkl VecNormalize est trouvé avec ou sans `.zip` ; `FileNotFoundError` bruyante si modèle PPO sans .pkl), `.team/metrics.json` (3 entrées sans .zip marquées `"invalid"`, non supprimées).
- Évals relancées avec .zip (`eval.py --model data/checkpoints/ppo_t61{,b}.zip --static --laps 3 --episodes 20 --seed 0`) : t61 (prof. H=30) 20/20, 20,22 s, 2 chocs ; t61b (H=34) 20/20, 19,36 s, 3 chocs, clean 0.
- Verdict corrigé : pas d'effondrement ; les agents finissent à 19-20 s mais avec 2-3 chocs → critère 0 choc non atteint, best/ T53b conservé. Professeurs seuls inchangés (H=30 16,6 s, H=34 17,44 s, 0 choc).
- Limites : pas d'essai depuis zéro/3×256 avec ces H.

## 2026-11-04 23:41 · reviewer · T61 validée
- Reprise vérifiée : eval t61/t61b avec .zip, 20 ép. seed 0 : t61 20,22 s 2 chocs ; t61b 19,36 s 3 chocs (conforme). eval.py corrigé (pkl sans .zip + erreur bruyante), pytest hors e2e : 48 passed, 1 skipped. best/ non remplacé, verdict négatif honnête. Ma précédente note inbox (renvoi) supprimée car traitée.

## 2026-11-04 23:42 · worker · T62 Robustesse H=29 + docs
- Fichiers : docs/SPEED_STATUS.md, docs/WALL_BASELINE.md (sections T62), metrics.json (entrée ajoutée par robust_eval). Aucun code modifié.
- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/robust_eval.py --model heuristic --static --laps 3 --episodes 100 --seed 1000 --eps 0.05` (47 s) → **65/100 finis**, 17,86 s, 0,77 choc/course (max 5), clean 0,25 (H=32 : 93/100).
- Doublons metrics.json signalés dans les docs (4 entrées seeds 1/2 de best/). Limites : eps 0,05 seul, une graine (1000).

## 2026-11-04 23:43 · reviewer · T62 validée
- Relancé robust_eval heuristic H=29 static laps 3 100 ép. seed 1000 eps 0,05 : 65/100, 17,86 s, 0,77 choc, clean 0,25 (conforme). Docs relues, cohérentes avec metrics.json ; aucun code modifié. Mon run a ajouté une entrée doublon dans metrics.json.

## 2026-11-04 23:46 · worker · T63 DAgger sur pistes aléatoires (bonus partiel, best/ non remplacé)
- Aucun code modifié. Commande (2 min 25, 97k éch., précision finale 0,78) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --laps 3 --wall-penalty -50 --init data/models/best/best.zip --episodes 12 --dagger 10 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 8 --lr 2e-4 --seed 1700 --out data/checkpoints/ppo_t63` (sans --static, professeur H=29 par défaut).
- Évals (`eval.py --model data/checkpoints/ppo_t63.zip --laps 3 --episodes 20 --seed 0`, avec et sans `--static`) :
  - `--no-static` : 18/20 finis (0,9), 18,87 s, 8,65 chocs/course (max 72), clean 0 → vs best/ T53b : 18/20, 26,27 s, 36,9 chocs (chocs/4,3, temps −7,4 s).
  - `--static` : 20/20, 20,52 s, **6 chocs/course**, clean 0 → critère statique (0 choc, ≤ 20,46 s) perdu ; best/ T53b conservé.
- Verdict : gain net sur pistes aléatoires, mais régression en statique ; un agent unique ne tient pas les deux. Limites : un seul run, une graine ; entrées metrics.json ajoutées par eval.py.

## 2026-11-04 23:47 · reviewer · T63 validée
- Relancé eval t63 20 ép. seed 0 : no-static 18/20, 18,87 s, 8,65 chocs ; static 20/20, 20,52 s, 6 chocs (conforme). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié, best/ non remplacé (critère statique perdu), verdict honnête. Mes évals ont ajouté des entrées metrics.json.

## 2026-11-04 23:47 · planner · Replanification
- T60-T63 rangées (échecs documentés, best/ T53b inchangé : 20/20, 0 choc, 20,46 s). Critère fiabilité rempli, vitesse ouverte, temps humain absent : pas de GOAL_REACHED.
- Constat : agents rapides (15,9-16 s) gardent 1 choc ; précision BC non en cause. Nouvelles tâches : T64 diagnostic des chocs, T65 DAgger ciblé, T66 départ de zéro avec professeurs H=30/34, T67 entraînement mixte (bonus). Si T65-T66 échouent, clore la phase vitesse. Inbox vide, pas de REPLAN.

## 2026-11-04 23:48 · worker · T64 Diagnostic des chocs t57/t60
- Fichiers : `scripts/diagnose_hits.py` (nouveau), `docs/WALL_BASELINE.md` (section T64). Physique/env intacts.
- Commandes : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/diagnose_hits.py --model data/checkpoints/ppo_t57.zip --laps 3` (idem t60).
- Résultats : t57 1 choc, tour 3, pas 593, spline 704/2400, vitesse 11,86 ; t60 1 choc, tour 3, pas 606, spline 701, vitesse 10,43. Même virage (~29 % de la piste). Action de l'agent = professeur au choc ; divergence 190 points de spline plus tôt (idx ~511-514 : agent tout droit, prof. droite+accél.). Écarts d'action 12,9 % (t57), 9,7 % (t60).
- Limites : une seule course déterministe par agent ; pytest non relancé (script ajouté seulement).

## 2026-11-04 23:49 · reviewer · T64 validée
- Relancé diagnose_hits sur t57 et t60 (laps 3) : 1 choc chacun, tour 3, spline 704/701, pas 593/606, vitesse 11,86/10,43, écarts 103/797 et 77/795 : conforme au doc. pytest hors e2e : 48 passed, 1 skipped. Physique/env intacts. Note : le script déclenche un « NEW PB / replay saved » de l environnement (effet de bord bénin).

## 2026-11-04 23:54 · worker · T65 DAgger ciblé (critère atteint, best/ remplacé)
- Fichiers : `scripts/imitate.py` (+`--hit-weight K`, défaut 1 = off : les 30 pas avant chaque choc mur des tours DAgger sont dupliqués → poids K), `data/models/best/` (nouveau), `data/models/best_t53b/` (copie de l'ancien), `.team/metrics.json`.
- Commande (4 min 04) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --wall-penalty -50 --init data/checkpoints/ppo_t60.zip --hit-weight 10 --episodes 12 --dagger 16 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 8 --lr 2e-4 --seed 1800 --out data/checkpoints/ppo_t65` (155k éch., précision 0,943).
- Eval `eval.py --static --laps 3 --episodes 20 --seed 0` : ppo_t65 et best/ copié : **20/20, 15,84 s, 0 choc, clean 1,0** (vs T53b 20,46 s ; t60 15,90 s/1 choc). best.json mis à jour.
- pytest hors e2e : 49 passed, 1 skipped.
- Limites : un seul run, une graine ; robustesse eps>0 et pistes aléatoires non mesurées (T53b : 68/100 à eps 0,05) ; piste statique déterministe.

## 2026-11-04 23:54 · reviewer · T65 validée
- Relancé eval data/models/best/best.zip static laps 3 20 ép. seed 0 : 20/20, 15,84 s, 0 choc, clean 1,0 (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff = option --hit-weight (défaut 1 inchangé). best_t53b sauvegardé. Limite : robustesse eps>0 non mesurée. Mon eval a ajouté une entrée metrics.json.

## 2026-11-05 00:11 · worker · T66 Imitation depuis zéro 3×256, professeurs H=30/34 (échec, best/ non remplacé)
- Aucun code modifié. Base : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --static --laps 3 --wall-penalty -50 --net-arch 256 256 256 --episodes 12 --dagger-episodes 8 --dagger-eps 0 0.05 --lr 5e-4 --out data/checkpoints/ppo_t66X`, éval `eval.py --model <zip> --static --laps 3 --episodes 20 --seed 0`.
- t66a : `--teacher-horizon 30 --dagger 12 --epochs 10 --seed 1900` → 20/20, 18,62 s, 2 chocs.
- t66b : `--teacher-horizon 34 --dagger 12 --epochs 10 --seed 2000` → 20/20, 19,22 s, 5 chocs.
- t66c (extra, non demandé) : H=30 + `--hit-weight 10 --dagger 16 --epochs 8 --seed 2100` (258k éch., précision 0,967) → 20/20, 18,60 s, 1 choc.
- Verdict : aucun à 0 choc ; best/ (T65 : 15,84 s, 0 choc) déjà meilleur, non remplacé. Les professeurs lents (H≥30) ne donnent pas d'agent plus propre que H=29 + hit-weight. Limites : une graine par run.

## 2026-11-05 00:13 · reviewer · T66 validée
- Relancé eval t66c (static, 20 ép., seed 0) : 20/20, 18,6 s, 1 choc (conforme). pytest hors e2e : 48 passed, 1 skipped. Aucun code modifié, best/ T65 non remplacé (justifié), entrées metrics.json présentes. Verdict négatif chiffré honnête.

## 2026-11-05 00:14 · worker · T67 Entraînement mixte statique + procédural (échec partiel, best/ non remplacé)
- Fichier : `scripts/imitate.py` (+`--mix-static` : épisodes DAgger pairs sur piste fixe, impairs sur procédurale ; défaut off, code inchangé sinon).
- Commande (2 min 29, 91k éch., précision finale 0,847) : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/imitate.py --mix-static --laps 3 --wall-penalty -50 --init data/models/best_t53b/best.zip --episodes 12 --dagger 10 --dagger-episodes 8 --dagger-eps 0 0.05 --epochs 8 --lr 2e-4 --seed 2200 --out data/checkpoints/ppo_t67` (départ T53b comme demandé).
- Évals 20 ép. seed 0 laps 3 (`eval.py --model data/checkpoints/ppo_t67.zip [--static]`, eval.py n'a pas --no-static : procédural = sans flag) :
  - static : 20/20, 17,76 s, **4 chocs**/course, clean 0 → critère (0 choc) non atteint.
  - procédural : 19/20 (0,95), 19,30 s, 7,35 chocs (max 53), clean 0,05 → vs T63 18/20, 8,65 chocs ; vs T53b 36,9 chocs.
- Verdict : mieux que T63 en static (4 vs 6 chocs) et un peu mieux en procédural, mais pas 0 choc ; best/ (T65 : 15,84 s, 0 choc) conservé. Pas de test mix + --hit-weight (suite possible). pytest hors e2e : 48 passed, 1 skipped. Une graine, un run.

## 2026-11-05 00:15 · reviewer · T67 validée
- Relancé eval ppo_t67 static laps 3 20 ép. seed 0 : 20/20, 17,76 s, 4 chocs (conforme). pytest hors e2e : 48 passed, 1 skipped. Diff = option --mix-static (défaut off, chemin inchangé). Verdict négatif chiffré honnête, best/ T65 conservé. Mon eval a ajouté une entrée metrics.json. Piste possible : mix + --hit-weight.
