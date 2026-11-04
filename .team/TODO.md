# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T46** · Compter les chocs murs dans l'env, le wrapper et `eval.py` · P1
  - but : `TimeAttackEnv` compte `wall_hits` (pas où `inside_track(new_pos)` est faux) et `wall_contacts` (nouveaux contacts, un pas sans choc avant) sans changer la physique ; `GymTimeAttack` les met dans `info` (`wall_hits`, `wall_contacts`) à chaque pas/fin ; `eval.py` et `robust_eval.py` affichent et écrivent dans `metrics.json` `mean_wall_hits`, `max_wall_hits`, `clean_rate` (épisodes finis à 0 choc).
  - fini quand : test unitaire (voiture envoyée dans un mur → compteur > 0 ; trajectoire du hash T40 inchangée) ; pytest hors e2e vert ; `eval.py` sur best/ laps 3 seed 0 20 ép. affiche les nouveaux champs
  - dépend de : rien
  - essais : 1

- [x] **T47** · Mesurer les chocs de `best/` T38 et du professeur heuristique (état de départ) · P1
  - but : baseline : combien de chocs par course pour best/ (eps 0) et pour `heuristic_lap` ; où (secteurs/checkpoints) ; entrée `metrics.json` + `docs/WALL_BASELINE.md`.
  - fini quand : doc avec chocs moyen/max/clean_rate sur 20 ép. (seed 0) pour les deux, et localisation des secteurs de choc ; entrées metrics.json
  - dépend de : T46
  - essais : 1

- [ ] **T48** · Option `wall_fatal` et `wall_penalty` dans `GymTimeAttack` (défaut : désactivées) · P1
  - but : paramètres `wall_fatal=False`, `wall_penalty=0.0` (pénalité par choc, ajoutée à la récompense) ; si `wall_fatal`, le choc met `terminated=True`, `end_cause="wall_fatal"`, récompense -100 ; exposés en options de `imitate.py` et du script d'entraînement PPO. Défaut = comportement identique (hash T40 inchangé), physique intacte.
  - fini quand : tests : défaut identique au hash ; wall_penalty=-50 baisse la récompense d'un épisode avec choc ; wall_fatal termine l'épisode au 1er choc ; pytest hors e2e vert
  - dépend de : T46
  - essais : 0

- [ ] **T49** · Palier 1 : professeur sans choc (heuristique avec marge aux murs) · P1
  - but : trouver des constantes de `heuristic_lap` (marge latérale/ligne plus intérieure, vitesse de virage) donnant 0 choc sur 20 ép. laps 3 seed 0 ET sur 100 ép. bruitées eps 0,05 (seed 1000) au maximum de vitesse possible ; utiliser `search_heuristic.py` avec contrainte `wall_hits == 0` (pénalité forte par choc dans le score).
  - fini quand : `docs/SEARCH_T49.md` avec constantes, 20/20 à 0 choc, temps moyen, clean_rate bruité ; entrée metrics.json (model "heuristic") ; si impossible, diagnostic des secteurs bloquants
  - dépend de : T46, T47
  - essais : 0

- [ ] **T50** · Palier 2 : ré-imitation DAgger du professeur sans choc → candidat best/ · P1
  - but : `imitate.py` (DAgger bruité, ≤ 10 min) sur le professeur T49, avec `wall_penalty` élevé en éval ; évaluer 20 ép. laps 3 seed 0 + robust_eval 100 ép. eps 0/0,05.
  - fini quand : candidat avec 20/20 finis, clean_rate 20/20 (0 choc), entrée metrics.json ; si OK, remplace best/ (avec mesure et best.json) car le critère exige 0 choc ; sinon diagnostic dans le journal
  - dépend de : T48, T49
  - essais : 0

- [ ] **T43** · Diagnostiquer `tests/test_e2e_training.py::test_training_runs_short_session` · P3
  - but : cause de l'échec ; corriger le test ou le code sans toucher à la physique.
  - fini quand : pytest complet vert 2 fois, ou skip justifié dans le journal
  - dépend de : rien
  - essais : 0

> Phase vitesse : plafond proche (borne 13,96 s, best/ 15,80 s, voir `docs/SPEED_STATUS.md`). Pas de nouvelle recherche locale tant que `data/human_best.json` manque.

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS).
