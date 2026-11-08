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

## S-23 : deux candidats depuis `best/` (v2_b)

Un seul levier change : le learning rate (`--lr`). Graines distinctes. 1 M de pas chacun, ~5,3 min (les deux en parallèle, ~3 200 pas/s).

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/ppo_finetune.py --init data/models/best/best.zip --timesteps 1000000 \
  --n-envs 4 --lr 3e-5 --seed 1 --max-minutes 28 --out data/checkpoints/ppo_v2_ft_a
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/ppo_finetune.py --init data/models/best/best.zip --timesteps 1000000 \
  --n-envs 4 --lr 1e-4 --seed 2 --max-minutes 28 --out data/checkpoints/ppo_v2_ft_b
```

Mesure (pour `X` = `a` ou `b`) :

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/checkpoints/ppo_v2_ft_X.zip --static --episodes 20 --seed 0 --laps 3
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/eval.py --model data/checkpoints/ppo_v2_ft_X.zip --bench --laps 3
```

| Modèle | Statique temps | Statique chocs | Statique finis | Banc temps | Banc chocs moy. / total | Banc pistes fautives |
|---|---|---|---|---|---|---|
| Professeur | 14,12 s | 0 | – | – | – | – |
| v2_b (`best/`) | 14,16 s | 0 | 20/20 | 16,47 s | 0,16 / 8 | 6/50 |
| ft_a (lr 3e-5, graine 1) | 14,12 s | 0 | 20/20 | 16,47 s | 0,18 / 9 | 6/50 |
| ft_b (lr 1e-4, graine 2) | 14,12 s | 0 | 20/20 | 16,55 s | 0,48 / 24 | 16/50 |

(Banc : 50/50 finis pour les trois.)

**Meilleur : ft_a** (statique 20/20 et 0 choc pour les deux ; banc 50/50 des deux avec moins de chocs pour ft_a).

**Conclusion** : le critère A+B n'est pas atteint. ft_a gagne 0,04 s au statique sur v2_b (au niveau du professeur, 14,12 s, pas strictement en dessous : B exige < 14,12 s), mais ne bat pas v2_b sur les chocs du banc (0,18 contre 0,16, différence de 1 choc sur 50 courses, non significative). ft_b dégrade le banc (0,48, sous la limite d'1 choc/course mais nettement pire) : un lr plus fort détériore la robustesse sans gain de temps.
Levier proposé pour un dernier tour (via inbox) : lr 3e-5 comme ft_a mais `--wall-penalty -100` et `--timesteps 3000000` (~16 min), pour pousser les chocs du banc sous 0,16 ; le temps statique semble plafonné au professeur, donc B strict paraît hors d'atteinte par ce chemin.
