# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T31** · Robustesse au bruit : DAgger bruité · P1
  - but : dans `scripts/imitate.py`, option pour injecter du bruit d'action (eps 0,05-0,1) pendant les tours DAgger (états de récupération, notamment le virage ~(181,510) après cp5), ré-entraîner depuis le professeur actuel (15,90 s), évaluer avec `robust_eval.py`.
  - fini quand : nouveau modèle 20/20 à eps 0 avec temps ≤ 16,2 s ET finish_rate ≥ 99/100 à eps 0,05 et ≥ 95/100 à eps 0,1 (100 ép., seed 1000) dans `metrics.json` ; `best/` remplacé seulement si eps 0 temps ≤ 15,90 s ou robustesse nettement meilleure avec écart de temps ≤ 0,3 s (décision justifiée dans le journal) ; sinon table des essais
  - dépend de : rien
  - essais : 1

- [x] **T32** · Borne inférieure théorique du temps sur 3 tours · P1
  - but : script `scripts/lower_bound.py` : estimer le temps minimal atteignable sur la ligne centrale/ligne de course (profil de vitesse à partir de ACCEL, FRICTION, MAX_SPEED effectifs, courbure et limite d'adhérence mesurée par scénarios numériques dans la physique actuelle, sans la modifier), pour savoir s'il reste une marge au-delà de 15,90 s.
  - fini quand : `docs/BOUND_T32.md` chiffré (hypothèses, borne, écart avec 15,90 s) ; sortie identique sur 2 lancements ; recommandation explicite (continuer la recherche / plafond proche)
  - dépend de : rien
  - essais : 1

- [x] **T33** · Recherche élargie du professeur (paramètres par secteur, redémarrages) · P1
  - but : étendre `scripts/search_heuristic.py` : vitesse cible par secteur de courbure (3 à 8 secteurs de la piste), plusieurs graines de redémarrage, budget ≤ 10 min ; vérifier 20/20 et audit (`audit_lap.py`: 0 hors piste, 0 mur, cp dans l'ordre).
  - fini quand : heuristique < 15,90 s, 20/20, audit propre, entrée `metrics.json` ; sinon table prouvant le plafond (≥ 3 redémarrages)
  - dépend de : rien (T32 oriente l'effort)
  - essais : 1

- [x] **T34** · Ré-imitation du meilleur professeur de T33 et remplacement de best/ · P1
  - but : `imitate.py --dagger 5` (avec bruit de T31 si validé) sur le nouveau professeur, éval 20 ép. laps 3 seed 0 et robustesse 100 ép. eps 0/0,05.
  - fini quand : modèle 20/20 plus rapide que 15,90 s dans `metrics.json` et `best/` remplacé ; sinon constat que T33 n'a rien produit (tâche close)
  - dépend de : T33 (amélioration trouvée)
  - essais : 2
  - note planner 00:45 : mesure partielle ppo_t34 = 15,68 s mais robustesse 49 % (eps 0,05) / 31 % (eps 0,1) contre 100/99 % pour best/ (T31). Ne PAS remplacer best/ avec ce modèle ; best/ ne change que si temps < 15,90 s ET robustesse ≥ celle de T31 (≥ 99 % eps 0,05, ≥ 95 % eps 0,1). Sinon clore T34 et passer à T36.

- [x] **T36** · Ré-imitation du professeur 15,68 s avec DAgger bruité · P1
  - but : `imitate.py --static --laps 3 --dagger 5 --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40` (comme T31, qui a donné 100/99 %) sur le professeur T33 ; éventuellement plus d'itérations DAgger / bruit plus fort si la robustesse reste basse (≤ 2 essais de 10 min).
  - fini quand : modèle avec eps 0 20/20 < 15,90 s ET ≥ 99/100 à eps 0,05 et ≥ 95/100 à eps 0,1 (100 ép., seed 1000) dans `metrics.json`, `best/` remplacé ; sinon table des essais et best/ inchangé
  - dépend de : T34 (clos)
  - essais : 2

- [x] **T37** · Recherche du professeur robuste au bruit · P2
  - but : dans `search_heuristic.py`, option de score = moyenne du temps sous bruit d'action eps 0,05 (≥ 5 épisodes, finish obligatoire) pour trouver un professeur rapide ET tolérant (virage ~(181,510) à ralentir) ; budget ≤ 10 min.
  - fini quand : heuristique avec temps eps 0 ≤ 15,9 s, 20/20, audit propre, et finish_rate ≥ 95 % à eps 0,05 (100 ép.) dans `metrics.json` ; sinon table des essais
  - dépend de : rien
  - essais : 1

- [x] **T35** · Clôture documentaire de l'état du meilleur modèle · P2
  - but : `docs/BEST_STATUS.md` : modèle, commande de reproduction (imitate + eval), mesures (20 ép., 100 ép. bruités, audit), limites (spline, piste fixe, PPO dégrade), et rappel de l'action humaine `human_lap.py`.
  - fini quand : le testeur reproduit la mesure 15,90 s (ou le meilleur courant) avec les commandes du doc
  - dépend de : rien
  - essais : 1

- [ ] **T38** · Ré-imiter le professeur T37 (15,80 s, robuste) · P1
  - but : `imitate.py --static --laps 3 --dagger 5 --dagger-episodes 30 --dagger-eps 0 0.05 0.1 --epochs 40 --out data/checkpoints/ppo_t38` (professeur courant = T37), puis `robust_eval.py` 100 ép. seed 1000 eps 0/0,05/0,1 et `eval.py` 20 ép. seed 0.
  - fini quand : eps 0 20/20 avec temps < 15,90 s ET ≥ 99/100 à eps 0,05 et ≥ 95/100 à eps 0,1, entrées dans `metrics.json`, `best/` remplacé (avec mesure) ; sinon table de l'essai et best/ inchangé (≤ 2 essais)
  - dépend de : rien
  - essais : 0

- [ ] **T39** · Professeur plus rapide et robuste : recherche repartant de T37 · P1
  - but : `search_heuristic.py --start` (paramètres T37), contrainte `--t0-max 15.7`, score bruité eps 0,05, 8 secteurs, budget ≤ 10 min ; garder le meilleur seulement s'il tient les critères.
  - fini quand : heuristique eps 0 < 15,80 s, 20/20, audit propre (`audit_lap.py`), finish ≥ 95/100 à eps 0,05 (100 ép., seed 1000) dans `metrics.json` ; sinon table des essais prouvant le plafond (T37 conservé)
  - dépend de : rien
  - essais : 0

- [ ] **T40** · Non-régression 1 tour / multi-tours · P2
  - but : test pytest (ou vérif scriptée) montrant que `laps=1` (défaut) donne les mêmes observations/récompenses/terminaisons qu'avant l'ajout multi-tours (comparaison à une trajectoire de référence ou au comportement `laps` omis) et que `laps=3` termine après 3 franchissements ordonnés.
  - fini quand : test ajouté, pytest hors e2e vert, test lancé 2 fois identique
  - dépend de : rien
  - essais : 0

- [ ] **T41** · Rapport de décision sur le critère vitesse · P2
  - but : `docs/SPEED_STATUS.md` : trajectoire du temps (45,5 → 15,90 s), borne T32 (13,96 s), marge restante, estimation du coût/bénéfice de continuer, et ce qu'il faut de Nicolas (`human_lap.py --laps 3`) pour conclure.
  - fini quand : doc chiffré, chaque valeur retrouvée dans `metrics.json` ou docs existants (vérifié par le testeur)
  - dépend de : rien
  - essais : 0

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/).
