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

- [x] **T48** · Option `wall_fatal` et `wall_penalty` dans `GymTimeAttack` (défaut : désactivées) · P1
  - but : paramètres `wall_fatal=False`, `wall_penalty=0.0` (pénalité par choc, ajoutée à la récompense) ; si `wall_fatal`, le choc met `terminated=True`, `end_cause="wall_fatal"`, récompense -100 ; exposés en options de `imitate.py` et du script d'entraînement PPO. Défaut = comportement identique (hash T40 inchangé), physique intacte.
  - fini quand : tests : défaut identique au hash ; wall_penalty=-50 baisse la récompense d'un épisode avec choc ; wall_fatal termine l'épisode au 1er choc ; pytest hors e2e vert
  - dépend de : T46
  - essais : 1

- [x] **T49** · Palier 1 : professeur sans choc (heuristique avec marge aux murs) · P1
  - but : trouver des constantes de `heuristic_lap` (marge latérale/ligne plus intérieure, vitesse de virage) donnant 0 choc sur 20 ép. laps 3 seed 0 ET sur 100 ép. bruitées eps 0,05 (seed 1000) au maximum de vitesse possible ; utiliser `search_heuristic.py` avec contrainte `wall_hits == 0` (pénalité forte par choc dans le score).
  - fini quand : `docs/SEARCH_T49.md` avec constantes, 20/20 à 0 choc, temps moyen, clean_rate bruité ; entrée metrics.json (model "heuristic") ; si impossible, diagnostic des secteurs bloquants
  - dépend de : T46, T47
  - essais : 1

- [ ] **T51** · Accélérer le professeur T49 (sécurité seulement si risque) · P1
  - but : `heuristic_action` ne lance les rollouts de sécurité que si l'action de base est jugée risquée (un seul rollout de base d'abord, alternatives seulement s'il y a choc) ; viser ≤ 1 s/épisode de 3 tours. Sortie identique ou meilleure : eps 0 inchangé (0 choc, ≤ 17,4 s).
  - fini quand : `heuristic_lap.py --static --laps 3 --episodes 20 --seed 0` : 20/20, mean_wall_hits 0, temps de calcul avant/après dans le journal, au moins 3× plus rapide ; pytest hors e2e vert
  - dépend de : rien
  - essais : 0

- [ ] **T52** · `imitate.py --init` : repartir de best/ T38 (ou d'un checkpoint) pour DAgger · P1
  - but : option `--init <model.zip>` qui charge poids + VecNormalize de départ au lieu de repartir de zéro ; la collecte DAgger étiquette avec le professeur sans choc les états visités par T38 (qui ne rate que les secteurs 3,4,5,7,11). `--wall-penalty` existe déjà.
  - fini quand : commande courte (1 tour DAgger, 3 épisodes) qui tourne et recharge le modèle ; le journal montre la précision initiale sur les données du professeur
  - dépend de : rien
  - essais : 0

- [ ] **T53** · DAgger long sans choc depuis T38 (≤ 10 min, reprises possibles) · P1
  - but : avec T51+T52, lancer DAgger (eps 0/0,05, `--wall-penalty -50`) ; évaluer 20 ép. laps 3 seed 0 (clean_rate) + robust_eval 100 ép. eps 0/0,05. Reprendre le checkpoint d'une itération à l'autre si nécessaire.
  - fini quand : entrée metrics.json ; si 20/20 finis ET clean_rate 20/20 → remplace best/ (avec best.json) ; sinon chocs par secteur dans le journal
  - dépend de : T51, T52
  - essais : 0

- [ ] **T54** · PPO fine-tuning depuis best/ T38 avec `wall_penalty` (voie alternative) · P2
  - but : `rl_train_ppo.py --load <best> --static --laps 3 --wall-penalty -20 --lr 3e-5` (≤ 10 min, ~200k pas) ; palier mort au contact (`--wall-fatal`) seulement si le palier pénalité baisse mean_wall_hits sans perdre 20/20.
  - fini quand : eval 20 ép. laps 3 seed 0 : finis, mean_wall_hits et clean_rate dans metrics.json vs 11 chocs de T38 ; verdict dans le journal (voie viable ou non)
  - dépend de : rien
  - essais : 0

- [ ] **T55** · Candidat de repli « politique + garde-fou » mesuré à part · P3
  - but : mesurer best/ T38 dont l'action est filtrée par la couche de sécurité T49 (eps 0, 20 ép.) : chocs, temps. Étiqueté NON conforme à « agent seul » ; sert de borne et de décision pour l'humain.
  - fini quand : entrée metrics.json (model « best+shield ») et paragraphe dans docs/WALL_BASELINE.md
  - dépend de : rien
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

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS), T46 (compteurs ; best/ T38 = 11 chocs/course), T47 (baseline), T48 (wall_fatal/penalty), T49 (professeur 0 choc 17,40 s ; bruité 93/100), T50 (ÉCHEC : DAgger 65k éch., 0/20, 78 chocs ; professeur lent et dépendant de l'état physique, voir T51-T53).
