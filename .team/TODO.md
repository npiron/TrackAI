# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T56** · DAgger de robustesse sur best/ T53b (bruit eps 0,05/0,1) sans perdre 0 choc · P1
  - but : repartir de `data/models/best/best.zip` (`imitate.py --init`, `--lr 2e-4`, `--wall-penalty -50`, `--dagger-eps 0.05 0.1`, seed différente de 500, ≤ 10 min, checkpoint repris si besoin) ; viser eps 0,05 : ≥ 90/100 finis et clean_rate nettement > 0,08 tout en gardant 20/20 et 0 choc à eps 0.
  - fini quand : eval 20 ép. laps 3 seed 0 + robust_eval 100 ép. eps 0/0,05 (seed 1000) dans metrics.json ; best/ remplacé SEULEMENT si 20/20, 0 choc à eps 0 ET temps ≤ 20,46 s et robustesse meilleure ; sinon verdict au journal
  - dépend de : rien
  - essais : 1

- [x] **T57** · Réduire le temps sous contrainte 0 choc (T53b = 20,46 s ; professeur sûr 17,40 s ; T38 15,80 s) · P1
  - but : DAgger depuis best/ T53b avec un professeur plus rapide à 0 choc (ex. `SAFE_HORIZON`/vitesse de virage de `heuristic_lap` réglés pour ≤ 17 s avec 0 choc sur 20 ép. ; vérifier d'abord le professeur seul), puis ré-imitation (≤ 10 min).
  - fini quand : professeur seul mesuré (temps, 0 choc, 20 ép. seed 0) puis agent évalué 20 ép. laps 3 seed 0 : si 20/20, 0 choc et temps < 20,46 s → remplace best/ (best.json) ; sinon verdict chiffré
  - dépend de : T56 (si T56 remplace best/, repartir de lui)
  - essais : 1

- [x] **T58** · Bonus : mesurer best/ sur pistes aléatoires jamais vues (`--no-static`) · P2
  - but : `eval.py --no-static --laps 3 --episodes 20 --seed 0` sur best/ (et best_t38) : finis, chocs, clean_rate ; diagnostic court (l'heuristique lit la spline : attendu faible).
  - fini quand : entrée metrics.json + paragraphe dans `docs/WALL_BASELINE.md` (ou doc dédié) avec verdict de faisabilité du bonus
  - dépend de : rien
  - essais : 1

- [ ] **T59** · Reproductibilité du critère : eval de best/ sur 3 graines (0, 1, 2) à eps 0 · P2
  - but : vérifier que 20/20 et 0 choc ne tiennent pas qu'à la graine 0 (eval.py laps 3, 20 ép., seeds 1 et 2) ; si échec, secteurs de choc.
  - fini quand : 2 entrées metrics.json, verdict au journal
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

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS), T46 (compteurs ; best/ T38 = 11 chocs/course), T47 (baseline), T48 (wall_fatal/penalty), T49 (professeur 0 choc 17,40 s ; bruité 93/100), T50 (ÉCHEC : DAgger 65k éch., 0/20, 78 chocs ; professeur lent et dépendant de l'état physique, voir T51-T53)., T51 (professeur 7,9× plus rapide), T52 (imitate --init), T53 (DAgger : 20/20, 0 choc, 20,46 s, best/ ; bruité 68/100), T54 (PPO+pénalité -20 non viable : 12 chocs), T55 (shield:T38 0 choc 16,42 s, non conforme).
