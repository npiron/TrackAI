# Affinage PPO v2 (`scripts/ppo_finetune.py`)

PPO depuis `data/models/best/best.zip` (obs v2) : lr 3e-5, clip 0,05, `ent_coef` 0, `n_steps` 512/env, batch 512, 4 époques,
gamma 0,995, lambda 0,95, VecNormalize gelé (`training=False`), envs en alternance fixe / procédural (graines ≥ 1000).
Après chaque mise à jour PPO : 8 minibatchs de cross-entropy sur les états étiquetés par le professeur (collecte DAgger-like,
`hit_weight` 10), pondérés par un coefficient décroissant linéairement de `--aux-coef0` à 0.

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/ppo_finetune.py --init data/models/best/best.zip \
  --timesteps 20000 --n-envs 2 --aux-episodes 4 --out data/checkpoints/ppo_ft_smoke
```

Débit mesuré (M1, CPU, smoke test, 2 envs) : ~2 400 pas/s (20 480 pas en 8 s). Arrêt propre après `--max-minutes` (28 par défaut), état sauvé.
Le journal est imprimé tous les ~20 000 pas : coef aux, chocs/épisode, temps de tour moyen, entropie.
