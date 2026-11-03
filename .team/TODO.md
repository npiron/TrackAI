# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [?] **T11** · Banc : seuil de dérive à 18° + statut global + mesure dans le dépôt · P1
  - but : dans `scripts/physics_check.py`, MAX_DRIFT_DEG=18 (décision #8 de docs/PHYSICS.md) ; ajouter au JSON un résumé `summary` (nb scénarios, nb pass, liste des fails) ; lancer le banc SANS `--metrics` pour écrire l'entrée `physics_check` dans `.team/metrics.json`
  - fini quand : `metrics.json` contient une entrée `physics_check` avec `summary` ; les seuls fails restants sont #1 (si mesuré), #2, #3, #4 ; 2 lancements donnent le même résumé ; pytest hors e2e vert
  - dépend de : T10
  - essais : 1

- [ ] **T12** · Corriger #3/#4 : clipper les actions dans `env.step` · P1
  - but : `np.clip` de steer ∈ [-1,1], accel ∈ [0,1], brake ∈ [0,1] au début de `step` dans `src/game/env.py`
  - fini quand : le scénario `out_of_range_actions` du banc passe (steer=5 → steering ≤ 1 ; accel=3 ≡ accel=1) ; test pytest ajouté ; suite pytest hors e2e verte ; docs/PHYSICS.md #3/#4 marqués corrigés
  - dépend de : T11
  - essais : 0

- [ ] **T13** · Corriger #2 : resynchroniser `speed` après collision · P1
  - but : après résolution du glissement mur, recaler `speed` sur la composante de `vel` selon le cap (ou |vel|) dans `env.py`
  - fini quand : scénarios walls du banc (perpendiculaire et 45°) passent le seuil 0.25 ; toujours 0 frame hors piste et 0 téléportation ; test pytest ; suite verte ; PHYSICS.md #2 marqué corrigé
  - dépend de : T11
  - essais : 0

- [ ] **T14** · Corriger #1 : MAX_SPEED cohérent avec la vitesse terminale · P2
  - but : choisir une des deux options (recommandé : baisser MAX_SPEED à ~23 pour garder la sensation de jeu ; ajuster le cap du boost relatif, BOOST_CAP du banc et la normalisation `speed_n`) et la justifier dans PHYSICS.md. Ajouter au banc un scénario « la vitesse terminale atteint ≥ 95 % de MAX_SPEED »
  - fini quand : nouveau scénario pass ; boost toujours borné et pass ; pytest vert ; note dans PHYSICS.md que les modèles RL antérieurs sont invalidés (aucun modèle n'existe dans le dépôt)
  - dépend de : T12, T13 (même fichier, éviter les conflits)
  - essais : 0

- [ ] **T15** · Rapport final du banc : 100 % pass · P2
  - but : relancer `physics_check.py` (écrit dans metrics.json), vérifier summary = 100 % pass, mettre à jour PHYSICS.md (tableau final, tous les écarts corrigés ou assumés), dédoublonner l'entrée `random` de metrics.json (doublon) sans en perdre
  - fini quand : `metrics.json` contient une entrée `physics_check` avec 0 fail ; reproductible ; le reviewer peut valider le critère de GOAL.md
  - dépend de : T14
  - essais : 0

> Reportées (plan RL en pause) : T4 smoke PPO, T5 éval du modèle, T6 PPO 50k. À reprendre après correction de la physique, car changer la physique invalide les entraînements.

## Terminées

T1, T2, T3, T7, T8, T9, T10 (validées).

