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
