# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T3** · Mesurer la référence · P1
  - but : entrée `random` dans `metrics.json`, et DQN si un modèle existe
  - fini quand : les chiffres sont dans `metrics.json` et commentés dans le journal
  - dépend de : T2
  - essais : 0

- [ ] **T4** · Smoke test PPO 5k steps · P2
  - but : `rl_train_ppo.py` (ou équivalent) lance 5 000 steps en headless (`SDL_VIDEODRIVER=dummy`) et sauvegarde un modèle dans un dossier ignoré par git
  - fini quand : la commande exacte et le chemin du modèle sont dans le journal, code de sortie 0, durée < 10 min
  - dépend de : T1
  - essais : 0

- [ ] **T5** · Évaluer le modèle du smoke PPO sur le banc · P2
  - but : `scripts/eval.py --model <modèle T4> --episodes 5 --seed 1` valide le chemin « modèle » (VecNormalize inclus) ; ajouter un test unitaire léger (modèle minuscule 64 steps généré dans tmp_path)
  - fini quand : entrée `ppo_smoke_5k` dans `metrics.json`, test pytest passe, chiffres comparés à `random` dans le journal
  - dépend de : T3, T4
  - essais : 0

- [ ] **T6** · Entraînement PPO 50k steps (jalon 1) · P2
  - but : lancer `rl_train_ppo.py --steps 50000` headless en arrière-plan avec log, modèle dans dossier ignoré par git ; durée mesurée
  - fini quand : modèle sauvegardé, commande + durée dans le journal, éval 10 épisodes seed 1 ajoutée à `metrics.json` (entrée `ppo_50k`)
  - dépend de : T5
  - essais : 0

## Terminées

