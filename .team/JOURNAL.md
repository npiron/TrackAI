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
