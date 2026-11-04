# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T60** · Imiter le professeur H=29 (14,62 s, 0 choc) avec un réseau plus gros · P1
  - but : t57 (15,94 s, 1 choc) a échoué par précision du MLP (0,84-0,97). Ajouter une option `--net-arch` (ex. 256 256 ou 256 256 256) à `imitate.py` (sans toucher à la physique ni à l'env), puis DAgger depuis zéro ou depuis best/ avec professeur H=29, `--wall-penalty -50`, eps 0 puis 0,05, ≤ 10 min (checkpoint repris si besoin).
  - fini quand : eval.py 20 ép. laps 3 seed 0 dans metrics.json ; si 20/20, 0 choc et < 20,46 s → remplace best/ (ancien copié dans `data/models/best_t53b/`, best.json mis à jour) ; sinon verdict chiffré (finis, chocs, temps, précision BC)
  - dépend de : rien
  - essais : 1

- [x] **T61** · Professeur intermédiaire plus facile à imiter (H=30 à 32 déjà testés ; viser 16-18 s à 0 choc) + imitation · P1
  - but : si T60 échoue ou en parallèle, choisir un H dont la politique est plus lisse (balayage 5 ép. puis 20 ép.) et imiter depuis best/ T53b ; gain visé entre 17 et 20 s à 0 choc.
  - fini quand : professeur seul mesuré (20 ép., 0 choc) + agent évalué 20 ép. laps 3 seed 0 ; remplace best/ seulement si 20/20, 0 choc et < 20,46 s
  - dépend de : T60 (ne pas lancer avant son verdict, pour réutiliser `--net-arch`)
  - essais : 2

- [ ] **T62** · Robustesse du professeur H=29 sous bruit + docs à jour · P2
  - but : `robust_eval` 100 ép. seed 1000, eps 0,05 sur `heuristic` H=29 (déjà mesuré seulement à H=32 : 93/100) ; mettre à jour `docs/SPEED_STATUS.md` et `docs/WALL_BASELINE.md` (SAFE_HORIZON 29, T56-T59, 4 entrées dupliquées seeds 1/2 dans metrics.json à signaler).
  - fini quand : entrée metrics.json + docs relues par le reviewer
  - dépend de : rien
  - essais : 0

- [ ] **T63** · Bonus : DAgger sur pistes aléatoires (`--no-static`) depuis best/ · P2
  - but : T58 a donné 18/20 finis, 36,9 chocs/course (heuristique : 0 choc, 18/20). Lancer `imitate.py` sans `--static` (professeur H=29 ou 32), laps 3, ≤ 10 min, en gardant le comportement sur la piste fixe.
  - fini quand : eval `--no-static` 20 ép. seed 0 ET eval `--static` 20 ép. dans metrics.json ; verdict chiffré (chocs/course vs 36,9). best/ remplacé seulement si le critère statique 20/20, 0 choc, ≤ 20,46 s est conservé
  - dépend de : T60 (architecture)
  - essais : 0

> Phase vitesse : plafond proche (borne 13,96 s, best/ 15,80 s, voir `docs/SPEED_STATUS.md`). Pas de nouvelle recherche locale tant que `data/human_best.json` manque.

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS), T46 (compteurs ; best/ T38 = 11 chocs/course), T47 (baseline), T48 (wall_fatal/penalty), T49 (professeur 0 choc 17,40 s ; bruité 93/100), T50 (ÉCHEC : DAgger 65k éch., 0/20, 78 chocs ; professeur lent et dépendant de l'état physique, voir T51-T53)., T51 (professeur 7,9× plus rapide), T52 (imitate --init), T53 (DAgger : 20/20, 0 choc, 20,46 s, best/ ; bruité 68/100), T54 (PPO+pénalité -20 non viable : 12 chocs), T55 (shield:T38 0 choc 16,42 s, non conforme), T56 (échec : robustesse 82 % mais 2 chocs, best/ gardé), T57 (professeur H=29 14,62 s 0 choc ; agent t57 15,94 s mais 1 choc, non remplacé), T58 (pistes aléatoires : 18/20, 36,9 chocs, bonus non atteint), T59 (3 graines : 20/20, 0 choc ; graine sans effet en statique), T43 (test e2e corrigé, pytest 49 passed).
