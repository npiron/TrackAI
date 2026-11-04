# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T68** · Robustesse de best/ T65 (15,84 s, 0 choc) au bruit d'action · P1
  - but : mesurer sans rien changer : `scripts/robust_eval.py --model data/models/best/best.zip --static --laps 3 --episodes 100 --seed 1000` pour eps 0 et 0,05 (T53b : 68/100 à 0,05 ; T38 : 97 %). Compter finis, chocs/course, clean_rate ; section T68 dans `docs/WALL_BASELINE.md`.
  - fini quand : 2 entrées robust_eval dans metrics.json + tableau chiffré dans la doc, comparé à T53b et au professeur H=29 (65/100)
  - dépend de : rien
  - essais : 1

- [ ] **T69** · DAgger ciblé itéré depuis best/ T65 pour supprimer les chocs sous bruit · P1
  - but : repartir de `data/models/best/best.zip` (`--init`), `--hit-weight 10`, `--dagger-eps 0 0.05 0.1`, `--wall-penalty -50`, professeur H=29, ≤ 10 min, 2 graines (2300, 2400). Cible : garder 20/20, 0 choc, ≤ 15,84 s à eps 0 et améliorer le taux clean à eps 0,05 (mesure T68).
  - fini quand : eval.py 20 ép. laps 3 seed 0 --static + robust_eval eps 0,05 100 ép. dans metrics.json pour chaque run ; remplace best/ seulement si 20/20, 0 choc, ≤ 15,84 s ET robustesse ≥ celle de T65 (ancien copié dans `data/models/best_t65/`) ; sinon verdict chiffré
  - dépend de : T68 (valeur de référence)
  - essais : 0

- [ ] **T70** · Bonus : mix piste fixe/procédurale + `--hit-weight 10` · P2
  - but : T67 (mix seul, depuis T53b) : static 4 chocs, procédural 7,35 chocs. Refaire depuis best/ T65 avec `--mix-static --hit-weight 10`, H=29, `--dagger-eps 0 0.05`, ≤ 10 min.
  - fini quand : eval.py 20 ép. seed 0 en static (flag --static) ET procédural (sans flag) dans metrics.json ; verdict chiffré (static doit rester 20/20, 0 choc, ≤ 15,84 s pour remplacer best/ ; sinon comparer procédural aux 7,35 chocs de T67)
  - dépend de : rien

- [ ] **T71** · Bilan et point d'arrêt de la phase vitesse (docs) · P2
  - but : mettre à jour `docs/SPEED_STATUS.md` : best/ T65 15,84 s 0 choc, marge restante vs borne 13,96 s et professeur H=29 14,62 s, ce qui a été essayé (T60-T67), reste à faire (temps humain, robustesse, bonus). Aucune modif de code.
  - fini quand : section datée dans le doc, chiffres tous retrouvables dans metrics.json (le testeur recoupe 3 valeurs)
  - dépend de : T68

> Phase vitesse : plafond proche (borne 13,96 s, best/ 15,80 s, voir `docs/SPEED_STATUS.md`). Pas de nouvelle recherche locale tant que `data/human_best.json` manque.

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s), T27 (PPO affinage : 17,48 s, dégrade vs BC), T28 (robustesse : 100/100 eps 0, 97 % eps 0,05, 91 % eps 0,1), T29 (audit valide), T30 (heuristique 15,90 s, BC 15,90 s, best/)., T31 (DAgger bruité, 100/99 %), T32 (borne 13,96 s), T33 (professeur 15,68 s fragile), T34 (non remplacé), T35 (doc), T36, T37 (professeur robuste 15,80 s), T38 (BC 15,80 s robuste, best/), T39 (plafond, T37 gardé), T40 (non-régression laps), T41 (SPEED_STATUS), T46 (compteurs ; best/ T38 = 11 chocs/course), T47 (baseline), T48 (wall_fatal/penalty), T49 (professeur 0 choc 17,40 s ; bruité 93/100), T50 (ÉCHEC : DAgger 65k éch., 0/20, 78 chocs ; professeur lent et dépendant de l'état physique, voir T51-T53)., T51 (professeur 7,9× plus rapide), T52 (imitate --init), T53 (DAgger : 20/20, 0 choc, 20,46 s, best/ ; bruité 68/100), T54 (PPO+pénalité -20 non viable : 12 chocs), T55 (shield:T38 0 choc 16,42 s, non conforme), T56 (échec : robustesse 82 % mais 2 chocs, best/ gardé), T57 (professeur H=29 14,62 s 0 choc ; agent t57 15,94 s mais 1 choc, non remplacé), T58 (pistes aléatoires : 18/20, 36,9 chocs, bonus non atteint), T59 (3 graines : 20/20, 0 choc ; graine sans effet en statique), T43 (test e2e corrigé, pytest 49 passed), T60 (3×256 : 15,90 s mais 1 choc), T61 (H=30/34 depuis T53b : 2-3 chocs), T62 (professeur H=29 bruité 65/100), T63 (pistes aléatoires 18/20, 8,65 chocs ; static perdu : 6 chocs), T64 (chocs t57/t60 : même virage, spline ~700), T65 (--hit-weight : 15,84 s, 0 choc, 20/20 → best/), T66 (3×256 depuis zéro H=30/34 : 1-5 chocs, échec), T67 (--mix-static : static 4 chocs, procédural 19/20 7,35 chocs, échec partiel).
