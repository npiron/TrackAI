# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T21** · Diagnostic du modèle t20/t19 : où et pourquoi la voiture s'arrête · P1
  - but : script `scripts/diagnose.py --model <zip> --static --laps N --episodes 5 --seed 0` qui rejoue la politique déterministe et rapporte par épisode : indice du dernier checkpoint, position finale, vitesse moyenne, nombre de frames à l'arrêt (<1), cause de fin (mur/timeout/…), récompense cumulée par composante (progress, alignment, speed, time_bonus, env). Lancer sur `ppo_t19_final.zip` (laps 1) et `ppo_t20_final.zip` (laps 3), résultats dans `docs/DIAG_T21.md`.
  - fini quand : le doc nomme la cause dominante de l'échec (ex. collision au virage N, récompense négative d'alignement qui piège la voiture, tourne en rond) avec chiffres ; test pytest sur le calcul des composantes ; deux lancements identiques
  - dépend de : rien
  - essais : 0

- [ ] **T22** · Contrôleur heuristique (poursuite des checkpoints) : faisabilité 3 tours et plancher de temps · P1
  - but : `scripts/heuristic_lap.py` : politique sans apprentissage qui vise le prochain checkpoint (direction + régulation vitesse) et passe par `GymTimeAttack(laps=3)` ; évaluation avec le même chrono. Sert à prouver que 3 tours sont faisables avec la physique figée et à donner un ordre de grandeur de temps.
  - fini quand : rapport (20 épisodes, seed 0, `--static`, laps 3) : finish_rate et temps total moyen, ajoutés à `metrics.json` (modèle `heuristic`, via eval.py ou option équivalente) ; même sans 20/20, indiquer où il échoue
  - dépend de : rien
  - essais : 0

- [ ] **T23** · Corriger la récompense/horizon selon T21 puis PPO 1 tour jusqu'à finish_rate > 0 · P1
  - but : appliquer la correction indiquée par `docs/DIAG_T21.md` (config de récompense, pas la physique) ; entraînement ≤ 10 min `--static --laps 1`, partant de zéro ou de `best` selon le diagnostic ; éval 20 épisodes `--laps 1` seed 0.
  - fini quand : entrée `metrics.json` ; `mean_checkpoints` > 2.0 ou `finish_rate` > 0 sinon justification chiffrée dans l'inbox ; `best/` mis à jour seulement si amélioré
  - dépend de : T21
  - essais : 0

- [ ] **T24** · Entraînement par imitation/amorçage depuis l'heuristique (si T22 réussit) · P2
  - but : collecter des trajectoires de l'heuristique, pré-entraîner la politique (behavior cloning, ≤ 5 min) ou injecter ces trajectoires, puis affiner PPO ; compatible `--load`.
  - fini quand : modèle évalué 20 ép. `--laps 1` ; entrée `metrics.json` comparée à T19/T23 ; décision `best/` notée
  - dépend de : T22
  - essais : 0

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Plus tard : fiabilité 3 tours 20/20 (reprise du meilleur modèle, `--laps 3`), puis paliers de vitesse (pénalité de temps, reprise). Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16, T17, T18, T19, T20 (validées ; T19 et T20 : finish_rate 0, mean_checkpoints 1.0 et 2.0).
