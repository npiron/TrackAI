# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T1** · Rendre la suite de tests exécutable · P1
  - but : `pytest` tourne dans `.venv` (ajouter à `requirements.txt` si absent), tests rapides séparés de `test_e2e_training.py`
  - fini quand : `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q --ignore=tests/test_e2e_training.py` passe ou les échecs restants sont listés dans le journal
  - dépend de : —
  - essais : 0

- [ ] **T2** · Banc d'éval reproductible · P1
  - but : `scripts/eval.py --model <chemin|random> --episodes N --seed S` qui ajoute une entrée dans `.team/metrics.json`
  - fini quand : deux lancements identiques donnent le même résultat, test unitaire ajouté
  - dépend de : T1
  - essais : 0

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

## Terminées

