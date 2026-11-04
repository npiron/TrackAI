# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T42** · Mettre à jour `docs/BEST_STATUS.md` (best/ = T38) · P1
  - but : refléter best/ = ppo_t38 (15,80 s, 100/100 à eps 0/0,05/0,1), commande de reproduction réelle (imitate sur professeur T37), constantes du professeur actuelles.
  - fini quand : le testeur relance les commandes du doc et retrouve 20/20 à 15,80 s et la robustesse annoncée ; plus aucune mention de T31 comme best/ actuel
  - dépend de : rien
  - essais : 0

- [ ] **T43** · Diagnostiquer `tests/test_e2e_training.py::test_training_runs_short_session` · P1
  - but : trouver pourquoi il échoue (régression due à multi-tours/physique, ou test périmé) et corriger le test ou le code sans toucher à la physique.
  - fini quand : pytest complet (e2e inclus) vert 2 fois de suite, ou test marqué skip avec raison écrite et justifiée dans le journal
  - dépend de : rien
  - essais : 0

- [ ] **T44** · Hygiène du banc : `eval.py`/`robust_eval.py` ne doivent pas écraser `replays/personal_best.json` · P2
  - but : les évaluations réécrivent des fichiers de replay/record (signalé T38) ; ce record ne doit pas polluer le chrono humain. Option `--no-save` ou désactivation par défaut en éval.
  - fini quand : après un `eval.py` 20 ép., `git status`/hash de `replays/personal_best.json` inchangé ; pytest hors e2e vert
  - dépend de : rien
  - essais : 0

- [ ] **T45** · Robustesse hors conditions d'entraînement : départ perturbé · P2
  - but : mesurer `best/` avec légère perturbation du point de départ (position ±, cap ±) si l'env le permet sans changer la physique (option d'éval seulement) : 100 ép., seed 1000 ; sert à savoir si l'agent a mémorisé une trajectoire unique.
  - fini quand : table finish_rate/temps dans `docs/ROBUST_START.md` + entrée `metrics.json` ; si finish < 95 %, recommandation (DAgger avec départs perturbés) ; sinon constat de robustesse
  - dépend de : rien
  - essais : 0

> Phase vitesse : plafond proche (borne 13,96 s, best/ 15,80 s, voir `docs/SPEED_STATUS.md`). Pas de nouvelle recherche locale tant que `data/human_best.json` manque.

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS).
