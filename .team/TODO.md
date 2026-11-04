# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [?] **T64** · Diagnostic : où et pourquoi les agents rapides touchent 1 mur · P1
  - but : t57 (15,94 s) et t60 (15,90 s) font 1 choc/course (piste statique déterministe : toujours le même ?). Script /tmp ou `scripts/` (sans toucher physique/env) qui rejoue t60 et t57 et note pour chaque choc : pas, position, progression sur la piste (checkpoint/virage), vitesse, action de l'agent vs action du professeur H=29 au même état.
  - fini quand : tableau chiffré dans `docs/WALL_BASELINE.md` (section T64) : nombre et lieu des chocs pour t57 et t60, conclusion (même virage ? écart d'action ?)
  - dépend de : rien
  - essais : 1

- [ ] **T65** · DAgger ciblé sur les zones de choc (poids/suréchantillonnage) · P1
  - but : ajouter à `imitate.py` une option (ex. `--hit-weight K`) qui duplique K fois les échantillons des ~30 pas précédant un choc pendant les tours DAgger, puis reprendre depuis t60 (3×256, 15,90 s, 1 choc) avec professeur H=29, `--wall-penalty -50`, eps 0 puis 0,05, ≤ 10 min.
  - fini quand : eval.py 20 ép. laps 3 seed 0 --static dans metrics.json ; si 20/20, 0 choc et < 20,46 s → remplace best/ (ancien copié dans `data/models/best_t53b/`, best.json mis à jour) ; sinon verdict chiffré
  - dépend de : T64 (pour savoir où cibler)
  - essais : 0

- [ ] **T66** · Imitation depuis zéro en 3×256 avec les professeurs 0 choc H=30 (16,6 s) et H=34 (17,44 s) · P1
  - but : T61 n'a testé qu'un départ depuis best/ T53b (2-3 chocs). T60 montre que 3×256 depuis zéro tient 15,9 s : refaire pareil avec `--teacher-horizon 30` puis 34, `--net-arch 256 256 256`, `--wall-penalty -50`, eps 0 puis 0,05, ≤ 10 min chacun. Gain visé : 0 choc entre 17 et 20,4 s.
  - fini quand : eval 20 ép. laps 3 seed 0 --static dans metrics.json pour chaque run ; remplacement de best/ comme en T65 si critère rempli ; sinon verdict chiffré
  - dépend de : rien
  - essais : 0

- [ ] **T67** · Bonus : entraînement mixte piste fixe + pistes aléatoires (corriger la régression statique de T63) · P2
  - but : T63 : no-static 18,87 s/8,65 chocs mais static 6 chocs. Ajouter `--mix-static` à `imitate.py` (épisodes DAgger alternant piste fixe et procédurale, sans changer le défaut), reprendre depuis best/ T53b, professeur H=29, ≤ 10 min.
  - fini quand : eval --static ET --no-static 20 ép. seed 0 dans metrics.json ; verdict chiffré (static doit rester 20/20, 0 choc pour remplacer best/)
  - dépend de : rien
  - essais : 0

> Phase vitesse : plafond proche (borne 13,96 s, best/ 15,80 s, voir `docs/SPEED_STATUS.md`). Pas de nouvelle recherche locale tant que `data/human_best.json` manque.

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS), T46 (compteurs ; best/ T38 = 11 chocs/course), T47 (baseline), T48 (wall_fatal/penalty), T49 (professeur 0 choc 17,40 s ; bruité 93/100), T50 (ÉCHEC : DAgger 65k éch., 0/20, 78 chocs ; professeur lent et dépendant de l'état physique, voir T51-T53)., T51 (professeur 7,9× plus rapide), T52 (imitate --init), T53 (DAgger : 20/20, 0 choc, 20,46 s, best/ ; bruité 68/100), T54 (PPO+pénalité -20 non viable : 12 chocs), T55 (shield:T38 0 choc 16,42 s, non conforme), T56 (échec : robustesse 82 % mais 2 chocs, best/ gardé), T57 (professeur H=29 14,62 s 0 choc ; agent t57 15,94 s mais 1 choc, non remplacé), T58 (pistes aléatoires : 18/20, 36,9 chocs, bonus non atteint), T59 (3 graines : 20/20, 0 choc ; graine sans effet en statique), T43 (test e2e corrigé, pytest 49 passed), T60 (3×256 : 15,90 s mais 1 choc), T61 (H=30/34 depuis T53b : 2-3 chocs), T62 (professeur H=29 bruité 65/100), T63 (pistes aléatoires 18/20, 8,65 chocs ; static perdu : 6 chocs).
