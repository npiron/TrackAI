# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T25** · Heuristique plus rapide (nouveau plancher de temps et professeur plus fort) · P1
  - but : dans `scripts/heuristic_lap.py`, régler la vitesse cible/visée (SPEED_PER_RADIUS, LOOK, PREDICT_FRAMES, éventuellement trajectoire plus tendue dans les virages, limites de vitesse par courbure) pour baisser le temps 3 tours sous 41,7 s en gardant 20/20. Balayage scripté, résultat dans `docs/SPEED_T25.md`.
  - fini quand : `metrics.json` contient `heuristic` laps 3 20/20 avec mean_total_time < 41,7 (sinon table du balayage prouvant le plafond) ; trois lancements identiques ; pytest hors e2e vert
  - dépend de : rien
  - essais : 0

- [ ] **T26** · Ré-imitation depuis l'heuristique rapide (+ DAgger léger) · P1
  - but : étendre `scripts/imitate.py` : professeur = heuristique T25, données avec bruit, 1-2 tours de DAgger (la politique apprise conduit, l'heuristique corrige les actions), plus d'époques ; entraînement ≤ 5 min.
  - fini quand : modèle évalué `--static --laps 3 --episodes 20 --seed 0` : finish_rate 1.0 et mean_total_time < 41,7 (sinon entrée metrics + analyse chiffrée) ; `best/` remplacé seulement si 20/20 et plus rapide
  - dépend de : T25
  - essais : 0

- [ ] **T27** · Affinage PPO 3 tours depuis le BC, sous pression de temps · P2
  - but : tester `rl_train_ppo.py --load` sur `ppo_t24_bc.zip` (ou le best de T26) avec `--laps 3`, LR faible, récompense de vitesse/temps renforcée (config, pas physique ; vérifier que `rewards_config.json` ne masque pas les clés), ≤ 10 min. Surveiller l'effondrement : checkpoint à mi-parcours évalué.
  - fini quand : éval 20 ép. laps 3 seed 0 dans `metrics.json` ; compatibilité `--load` du zip BC confirmée ou corrigée ; `best/` mis à jour seulement si 20/20 et temps plus bas
  - dépend de : rien (T26 utile mais non bloquant)
  - essais : 0

- [ ] **T28** · Robustesse du meilleur modèle · P2
  - but : évaluer `best/` sur 100 épisodes avec seeds différents (`--static`, laps 3) et avec petit bruit d'action (eps 0,05) pour vérifier que 20/20 n'est pas un artefact de déterminisme ; rapport `docs/ROBUST_T28.md`.
  - fini quand : taux de finish chiffré dans le doc et une entrée `metrics.json` ; si < 100 %, cause principale identifiée (virage/checkpoint)
  - dépend de : rien
  - essais : 0

> Action humaine (non assignable) : jouer `python scripts/human_lap.py --laps 3` pour créer `data/human_best.json` ; sans lui le critère vitesse n'est pas évaluable (le banc affiche `human_best_total: null`).
> Anciens modèles de `data/models/production` invalides.

## Terminées

T1, T2, T3, T7-T15, T16-T20 (T19/T20 : finish_rate 0), T21 (diagnostic), T22 (heuristique 20/20, 45,5 s), T23 (PPO corrigé, cp 2, échec), T24 (BC : 20/20, 41,7 s, best/).
