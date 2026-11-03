# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [x] **T29** · Audit de validité des tours rapides (coupe de virages) · P1
  - but : script `scripts/audit_lap.py` : pour `best/` et l'heuristique, laps 3, `--static`, rapporter par tour : temps, vitesse moyenne/max, ordre des checkpoints franchis, distance min au bord de piste, nombre de frames hors piste/contact mur. Vérifier que 17,7 s n'exploite pas un défaut de comptage (checkpoints sautés, tour validé sans parcourir la piste).
  - fini quand : `docs/AUDIT_T29.md` chiffré, verdict explicite (valide / faille + correctif proposé dans l'inbox si faille) ; sortie identique sur 2 lancements
  - dépend de : rien
  - essais : 1

- [x] **T30** · Réduire encore le temps : optimisation de l'heuristique par recherche · P1
  - but : étendre `scripts/sweep_heuristic.py` (recherche aléatoire / hill-climbing, éventuellement paramètres par secteur de courbure) pour passer sous 17,74 s en gardant 20/20, puis ré-imitation (`imitate.py --dagger 5`) du nouveau professeur. ≤ 10 min de calcul par lancement.
  - fini quand : heuristique améliorée dans `metrics.json` (20/20, temps < 17,74) ; si modèle BC évalué 20/20 et plus rapide que best/, `best/` remplacé ; sinon table prouvant le plafond
  - dépend de : T29 (verdict valide)
  - essais : 1

- [ ] **T27** · Affinage PPO 3 tours depuis le BC, sous pression de temps · P2
  - but : tester `rl_train_ppo.py --load` sur `ppo_t24_bc.zip` (ou le best de T26) avec `--laps 3`, LR faible, récompense de vitesse/temps renforcée (config, pas physique ; vérifier que `rewards_config.json` ne masque pas les clés), ≤ 10 min. Surveiller l'effondrement : checkpoint à mi-parcours évalué.
  - fini quand : éval 20 ép. laps 3 seed 0 dans `metrics.json` ; compatibilité `--load` du zip BC confirmée ou corrigée ; `best/` mis à jour seulement si 20/20 et temps plus bas
  - dépend de : rien (T26 utile mais non bloquant)
  - essais : 0

- [x] **T28** · Robustesse du meilleur modèle · P1
  - but : évaluer `best/` sur 100 épisodes avec seeds différents (`--static`, laps 3) et avec petit bruit d'action (eps 0,05) pour vérifier que 20/20 n'est pas un artefact de déterminisme ; rapport `docs/ROBUST_T28.md`.
  - fini quand : taux de finish chiffré dans le doc et une entrée `metrics.json` ; si < 100 %, cause principale identifiée (virage/checkpoint)
  - dépend de : rien
  - essais : 1

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/), T25 (heuristique 20/20, 17,94 s), T26 (BC+DAgger 20/20, 17,74 s, best/).
