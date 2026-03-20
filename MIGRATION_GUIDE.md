# 🚀 Guide de Migration DQN → PPO

## TL;DR

**Ce qu'on a fait :**
1. ✅ Créé `rl_train_ppo.py` - version PPO optimisée
2. ✅ Analysé le code existant (voir `AMELIORATIONS.md`)
3. ✅ Gardé `rl_train.py` intact (DQN) pour comparaison

**Pour tester PPO immédiatement :**
```bash
python3 rl_train_ppo.py --steps 500000
```

---

## 📊 Différences Clés DQN vs PPO

| Aspect | DQN (ancien) | PPO (nouveau) |
|--------|--------------|---------------|
| **Fichier** | `rl_train.py` | `rl_train_ppo.py` |
| **Import** | `from stable_baselines3 import DQN` | `from stable_baselines3 import PPO` |
| **Steps recommandés** | 2M | **500k-1M** (4x plus rapide!) |
| **Buffer** | 200,000 (RAM intensive) | Pas de buffer (on-policy) |
| **Params clés** | `buffer_size`, `exploration_fraction` | `n_steps`, `n_epochs`, `gae_lambda` |
| **Convergence** | ~2M steps | **~500k steps** |

---

## 🎯 Quick Start

### 1. Entraînement PPO (Recommandé)

```bash
# Entraînement standard (500k steps = ~2h sur CPU)
python3 rl_train_ppo.py --steps 500000

# Avec procédural generation (évite overfitting)
python3 rl_train_ppo.py --steps 500000

# Avec curriculum learning (commence facile)
python3 rl_train_ppo.py --steps 500000 --curriculum

# Mode visuel (pour débugger)
python3 rl_train_ppo.py --steps 50000 --visual
```

### 2. Entraînement DQN (Comparaison)

```bash
# Ancien algorithme (pour comparaison)
python3 rl_train.py --steps 2000000
```

### 3. Tester les Modèles

```bash
# Tester modèle PPO
python3 rl_play.py --model data/checkpoints/ppo_XXXXXX_final.zip

# Tester modèle DQN
python3 rl_play.py --model data/checkpoints/XXXXXX_final.zip
```

---

## 📁 Nouveaux Fichiers

```
TackAI/
├── rl_train.py              # DQN (ancien, conservé)
├── rl_train_ppo.py          # PPO (NOUVEAU ✨)
├── AMELIORATIONS.md         # Analyse détaillée
├── MIGRATION_GUIDE.md       # Ce fichier
└── data/
    └── checkpoints/
        ├── ppo_*_final.zip  # Modèles PPO
        └── *_final.zip      # Modèles DQN
```

---

## ⚙️ Hyperparamètres PPO (optimisés)

### Dans `rl_train_ppo.py`

```python
ppo_params = {
    "n_steps": 2048,           # Rollout buffer (combien d'expérience avant update)
    "batch_size": 64,          # Taille mini-batch SGD
    "n_epochs": 10,            # Nombre d'epochs par update
    "gamma": 0.99,             # Facteur discount
    "gae_lambda": 0.95,        # Generalized Advantage Estimation
    "clip_range": 0.2,         # PPO clipping (stabilité)
    "ent_coef": 0.01,          # Bonus exploration
    "learning_rate": 3e-4,     # LR constant (marche bien)
}
```

### Comprendre les Paramètres Clés

**`n_steps` (2048)** :
- Combien de steps de jeu avant un update du réseau
- Plus grand = plus stable, mais updates moins fréquents
- 2048 * 16 envs = 32,768 steps par update

**`batch_size` (64)** :
- Taille des mini-batches pour SGD
- Plus petit = plus de bruit, plus d'exploration
- Plus grand = plus stable, mais peut overfit

**`n_epochs` (10)** :
- Combien de fois réutiliser chaque batch
- PPO peut réutiliser data (contrairement à A2C)
- 10 = bon compromis

**`gae_lambda` (0.95)** :
- Trade-off bias vs variance pour advantage
- 0.95 = recommandé pour tâches longues

**`ent_coef` (0.01)** :
- Bonus pour encourager exploration
- 0.01 = exploration modérée
- Plus haut = plus random (ex: 0.05)

---

## 🧪 Expérimentations Recommandées

### Test 1 : PPO vs DQN (Baseline)

```bash
# Terminal 1 - PPO
python3 rl_train_ppo.py --steps 500000 --run-id ppo_baseline

# Terminal 2 - DQN (pour comparer)
python3 rl_train.py --steps 2000000 --run-id dqn_baseline
```

**Attentes :**
- PPO converge en ~500k steps (2-3h)
- DQN converge en ~2M steps (8-10h)
- PPO devrait avoir comportement plus fluide

---

### Test 2 : Curriculum Learning

```bash
# Avec curriculum (commence facile)
python3 rl_train_ppo.py --steps 500000 --curriculum --run-id ppo_curriculum

# Sans curriculum
python3 rl_train_ppo.py --steps 500000 --run-id ppo_no_curriculum
```

**Attentes :**
- Curriculum apprend plus vite au début
- Peut généraliser mieux sur nouveaux circuits

---

### Test 3 : Architecture Réseau

Modifier dans `rl_train_ppo.py` ligne 128 :

```python
# Option A: Shared network (plus rapide)
policy_kwargs = dict(
    net_arch=[256, 256]
)

# Option B: Separate networks (plus expressif) - ACTUEL
policy_kwargs = dict(
    net_arch=[dict(pi=[256, 256], vf=[256, 256])]
)

# Option C: Deep network (plus de capacité)
policy_kwargs = dict(
    net_arch=[dict(pi=[512, 512, 256], vf=[512, 512, 256])]
)
```

---

## 📈 Monitoring TensorBoard

```bash
# Lancer TensorBoard
tensorboard --logdir=./logs/ppo_tensorboard/

# Ouvrir dans navigateur
# http://localhost:6006
```

**Métriques à surveiller :**
- `rollout/ep_rew_mean` - Récompense moyenne (doit monter)
- `train/explained_variance` - Qualité value function (proche de 1 = bon)
- `train/policy_loss` - Loss policy (doit converger)
- `train/value_loss` - Loss value (doit converger)
- `train/entropy_loss` - Exploration (décroit normalement)

---

## 🐛 Troubleshooting

### "ImportError: cannot import PPO"
```bash
pip install stable-baselines3 --upgrade
```

### "MPS backend not available"
C'est normal sur Mac sans Apple Silicon. Le code détecte automatiquement et utilise CPU.

### "RuntimeError: spawn already set"
Ignorable - c'est juste un warning multiprocessing.

### Modèle ne converge pas
1. Vérifier reward shaping (`rewards_config.json`)
2. Réduire `n_steps` (2048 → 1024)
3. Augmenter `ent_coef` (0.01 → 0.05) pour plus d'exploration

### RAM overflow (>16GB utilisé)
1. Réduire `n_cpu` (16 → 8) dans `rl_train_ppo.py` ligne 95
2. Réduire `n_steps` (2048 → 1024)

---

## 🔄 Continuer un Entraînement

```bash
# Reprendre depuis checkpoint
python3 rl_train_ppo.py --load data/checkpoints/ppo_XXXXX_500000_steps.zip --steps 1000000
```

---

## 📊 Comparer les Performances

### Script de Comparaison

```bash
# Créer un script de benchmark
cat > benchmark.sh << 'EOF'
#!/bin/bash
echo "🏁 Benchmarking DQN vs PPO"

# Test 10 episodes avec chaque modèle
python3 rl_play.py --model data/checkpoints/dqn_final.zip --episodes 10 > dqn_results.txt
python3 rl_play.py --model data/checkpoints/ppo_final.zip --episodes 10 > ppo_results.txt

echo "✅ Done! Check dqn_results.txt and ppo_results.txt"
EOF

chmod +x benchmark.sh
./benchmark.sh
```

---

## 🎯 Prochaines Étapes

### Après PPO fonctionne :

1. **Améliorer Observations** (voir `AMELIORATIONS.md` section 4)
   - Ajouter lidar (distances murs)
   - Ajouter vitesse angulaire
   - Ajouter angle vers checkpoint

2. **Reward Shaping Avancé** (section 5)
   - Récompenser trajectoires fluides
   - Bonus pour racing line optimale
   - Pénaliser collisions

3. **Curriculum Learning** (section 6)
   - Implémenter difficulté progressive
   - Générer circuits de complexité croissante

4. **Optimisation Optuna** 
   - Créer `rl_optimize_ppo.py` (adapter depuis `rl_optimize.py`)
   - Chercher meilleurs hyperparams automatiquement

---

## ✅ Checklist Migration

- [x] Créé `rl_train_ppo.py`
- [x] Testé que ça lance sans erreurs
- [ ] Entraîné modèle PPO (500k steps)
- [ ] Comparé avec DQN baseline
- [ ] Vérifié performance sur nouveaux circuits
- [ ] Optimisé hyperparams si nécessaire
- [ ] Documenté résultats

---

## 📞 Support

Si tu as des questions ou problèmes :
1. Vérifie `AMELIORATIONS.md` pour détails techniques
2. Check les logs dans `data/monitoring/`
3. Lance TensorBoard pour voir courbes d'apprentissage

---

**Bonne chance ! PPO devrait donner de bien meilleurs résultats que DQN pour ce projet. 🚀**
