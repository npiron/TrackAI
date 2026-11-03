# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T16** · Mode multi-tours `laps` (défaut 1) dans `TimeAttackEnv` et `GymTimeAttack` · P1
  - but : paramètre `laps=1` ; à chaque passage de la ligne d'arrivée avec tous les checkpoints validés, si tour < laps : incrémenter le compteur, remettre `cp_visited` à faux, enregistrer le temps du tour ; `done` seulement au dernier tour. `info` du wrapper expose `laps_done`, `lap_times` (liste), `total_time`, `is_success` (= laps tours finis). Aucun changement de physique ni de comportement à `laps=1`.
  - fini quand : test pytest `laps=1` identique à l'avant (même trajectoire/récompense sur actions fixes) ; test `laps=3` avec voiture téléportée/rejouée sur le tracé qui renvoie 3 `lap_times` ; pytest hors e2e vert
  - dépend de : rien
  - essais : 1

- [x] **T17** · Banc : `--laps N` et métriques multi-tours dans `scripts/eval.py` · P1
  - but : option `--laps` (défaut 1) ; sortie : `finish_rate` (épisodes qui finissent les N tours), `mean_total_time`, `best_total_time`, `mean_laps_done`. Rétrocompatible (mêmes clés qu'avant à `--laps 1`). Rappel : la piste fixe est `--static` (sinon le banc est procédural).
  - fini quand : `eval.py --model random --static --laps 3 --episodes 20 --seed 0` écrit une entrée dans `metrics.json` avec les nouvelles clés ; 2 lancements identiques ; test pytest sur le calcul
  - dépend de : T16
  - essais : 1

- [x] **T18** · Chrono humain : mode de mesure du meilleur temps humain sur la piste fixe · P1
  - but : ajouter dans `trackmania_clone.py` (ou un script `scripts/human_lap.py`) l'enregistrement du temps de chaque tour avec le même chrono que le banc (`1/FPS` par frame, via `TimeAttackEnv`), `laps` configurable, écriture du meilleur total dans `data/human_best.json`. Jouable par Nicolas. Pas de screenshot.
  - fini quand : un test headless rejoue une liste d'actions et obtient un total identique au chrono du banc ; `data/human_best.json` est lu par `eval.py` s'il existe (champ `human_best_total` dans l'entrée métrique, null sinon)
  - dépend de : T16
  - essais : 1

- [ ] **T19** · Référence PPO 1 tour sur piste fixe (reprise T4-T6 adaptée) · P2
  - but : entraînement PPO ≤ 10 min avec `rl_train_ppo.py --static --steps <≤200k>`, avec la physique actuelle (MAX_SPEED 23, frein moteur) ; évaluer avec `eval.py --static --laps 1 --episodes 20 --seed 0`. Copier le meilleur dans `data/models/best/` avec un `best.json` (mesure).
  - fini quand : entrée `metrics.json` du modèle ; `data/models/best/` + sa mesure ; taux de finition 1 tour rapporté (même s'il vaut 0)
  - dépend de : T17
  - essais : 0

- [ ] **T20** · Entraînement fiabilité 3 tours (reprise du modèle de T19) · P2
  - but : reprendre `--load` le meilleur modèle, entraînement ≤ 10 min avec `laps=3` ; adapter récompense seulement si nécessaire (checkpoints qui se répètent à chaque tour) ; évaluer 20 épisodes `--laps 3`.
  - fini quand : entrée `metrics.json` avec `finish_rate` ; `best/` mis à jour seulement si le finish_rate ou le temps s'améliore ; décision à noter dans l'inbox (reste à faire pour 20/20)
  - dépend de : T19
  - essais : 0

> Plus tard (après fiabilité 20/20) : paliers de vitesse (bonus de temps, pénalité de temps par tour, reprise de modèle) ; comparaison au temps humain. Les anciens modèles de `data/models/production` sont invalides (physique changée).
> Reportées : T4, T5, T6 remplacées par T19.

## Terminées

T1, T2, T3, T7, T8, T9, T10, T11, T12, T13, T14, T15 (validées).
