import sys
import warnings
import time
sys.stdout.reconfigure(line_buffering=True)
print("🚀 Starting PPO Training Script (OPTIMIZED VERSION)...")

import argparse
import os
import ast

# Lightweight imports only
print("⏳ Loading lightweight libraries...")
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import torch.nn as nn

print("✅ Ready. Heavy libraries will load when training starts...")


def _tb_log_dir():
    """Dossier tensorboard, ou None si tensorboard n'est pas installé."""
    try:
        import tensorboard  # noqa: F401
        return "./logs/ppo_tensorboard/"
    except ImportError:
        return None


def main():
    # Parse args first (fast)
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=1_000_000, help="Total timesteps (PPO needs less than DQN!)")
    parser.add_argument("--visual", action="store_true", help="Render training (slower, single core)")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning Rate")
    parser.add_argument("--run-id", type=str, default=str(int(time.time())), help="Unique run identifier")
    parser.add_argument("--load", type=str, default=None, help="Path to existing model to continue training")
    parser.add_argument("--use-best-params", action="store_true", help="Load hyperparameters from logs/best_hyperparams.txt")
    parser.add_argument("--static", action="store_true", help="Disable procedural generation (use fixed track)")
    parser.add_argument("--curriculum", action="store_true", help="Enable curriculum learning (progressive difficulty)")
    parser.add_argument("--laps", type=int, default=1, help="Nombre de tours par épisode")
    parser.add_argument("--rewards", type=str, default=None, help="Fichier JSON de récompenses (remplace rewards_config.json, hérité par les sous-processus)")
    args = parser.parse_args()
    if args.rewards:
        os.environ["TRACKAI_REWARDS_CONFIG"] = args.rewards
    
    # NOW load the heavy stuff (only when actually training)
    print("⏳ Loading Pytorch (~1s)...")
    import torch
    
    print("⏳ Loading Stable Baselines3...")
    from stable_baselines3 import PPO  # ✨ Changed from DQN to PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize, SubprocVecEnv
    from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.monitor import Monitor
    
    print("⏳ Loading Game Components...")
    # Suppress Pygame's pkg_resources warning
    warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
    import pygame
    from src.rl.wrappers import GymTimeAttack
    
    print("✅ All imports loaded.")

    import multiprocessing

    # Device selection
    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
        print("⚡️ Apple Silicon GPU detected (MPS).")
    elif torch.cuda.is_available():
        device = "cuda"
        print("⚡️ NVIDIA GPU detected (CUDA).")
    else:
        print("🖥️  Using CPU.")
    
    # Environment setup
    procedural_mode = not args.static
    if procedural_mode:
        print("🔀 Procedural Generation ENABLED")
    else:
        print("⏹️ Procedural Generation DISABLED (Static Track)")
    
    # Curriculum Learning (optional)
    curriculum_difficulty = 0.3 if args.curriculum else 1.0  # Start easier if curriculum
    if args.curriculum:
        print(f"📚 Curriculum Learning ENABLED (starting difficulty: {curriculum_difficulty})")

    if args.visual:
        # Single-core visual training
        n_cpu = 1
        print("🎨 Launching Visual training mode (single core)...")
        
        def make_env():
            env = GymTimeAttack(render_mode="human", procedural=procedural_mode, laps=args.laps)
            os.makedirs("data/monitoring", exist_ok=True)
            return Monitor(env, f"data/monitoring/monitor_visual_{args.run_id}.csv", info_keywords=("checkpoints_reached", "is_success", "lap_time"))
        
        venv = DummyVecEnv([make_env])
    else:
        # Headless Multi-core
        # PPO benefits GREATLY from parallel environments (on-policy algorithm)
        n_cpu = 16  # 16 parallel environments for optimal PPO training
        print(f"🚀 Launching Headless training on {n_cpu} parallel environments...")
        
        def make_env():
            env = GymTimeAttack(render_mode=None, procedural=procedural_mode, laps=args.laps)
            os.makedirs("data/monitoring", exist_ok=True)
            return Monitor(env, f"data/monitoring/monitor_headless_{args.run_id}_{os.getpid()}.csv", info_keywords=("checkpoints_reached", "is_success", "lap_time"))

        print("⏳ Creating environments...")
        venv = make_vec_env(make_env, n_envs=n_cpu, vec_env_cls=SubprocVecEnv)
        print("✅ Environments ready.")

    # Wrap in VecNormalize (critical for PPO)
    load_stats = args.load.replace(".zip", "_vecnormalize.pkl") if args.load else None
    if load_stats and os.path.exists(load_stats):
        print(f"📥 Reprise des stats VecNormalize: {load_stats}")
        venv = VecNormalize.load(load_stats, venv)
        venv.training = True
        venv.norm_reward = True
    else:
        venv = VecNormalize(venv, norm_obs=True, norm_reward=True, clip_obs=10.0)

    # Checkpoint callback (PPO converges faster, so checkpoint more frequently)
    checkpoint_callback = CheckpointCallback(
        save_freq=max(1000, 20000 // n_cpu),  # More frequent than DQN
        save_path="./data/checkpoints/",
        name_prefix=f"ppo_{args.run_id}",
        save_vecnormalize=True,
        verbose=1
    )
    
    # Custom callback for curriculum learning
    class CurriculumCallback(BaseCallback):
        def __init__(self, verbose=0):
            super().__init__(verbose)
            self.difficulty = 0.3
            self.success_window = []
            
        def _on_step(self):
            # Check success rate every 10k steps
            if self.n_calls % 10000 == 0 and len(self.success_window) > 0:
                success_rate = np.mean(self.success_window[-100:])
                
                if success_rate > 0.7 and self.difficulty < 1.0:
                    self.difficulty = min(1.0, self.difficulty + 0.1)
                    print(f"📈 Curriculum: Increased difficulty to {self.difficulty:.1f}")
                elif success_rate < 0.3 and self.difficulty > 0.1:
                    self.difficulty = max(0.1, self.difficulty - 0.05)
                    print(f"📉 Curriculum: Decreased difficulty to {self.difficulty:.1f}")
                    
            return True

    print(f"🧠 Initializing PPO model (OPTIMIZED for vehicle control)...")
    print(f"   Algorithm: PPO (On-Policy)")
    print(f"   N-Steps: 2048")
    print(f"   Batch Size: 64")
    print(f"   Epochs: 10")
    print(f"   Learning Rate: 3e-4")
    print(f"   Architecture: [256, 256] (shared)")
    
    # Network Architecture (PPO)
    policy_kwargs = dict(
        net_arch=[dict(pi=[256, 256], vf=[256, 256])]  # Separate policy and value networks
        # Alternative: net_arch=[256, 256] for shared network (faster but less expressive)
    )
    
    # Learning Rate Schedule (optional - PPO works well with constant LR)
    def lr_schedule(progress_remaining):
        """
        Optional learning rate schedule for PPO:
        - Start: 3e-4
        - End: 1e-5
        Most of the time, constant 3e-4 works great for PPO
        """
        return 1e-5 + (3e-4 - 1e-5) * progress_remaining

    # PPO Hyperparameters (OPTIMIZED for racing game)
    ppo_params = {
        "n_steps": 2048,           # Rollout length (how many steps before update)
        "batch_size": 64,          # Minibatch size for SGD
        "n_epochs": 10,            # Number of epochs per update
        "gamma": 0.99,             # Discount factor
        "gae_lambda": 0.95,        # GAE parameter (advantage estimation)
        "clip_range": 0.2,         # PPO clipping parameter
        "clip_range_vf": None,     # Value function clipping (None = no clipping)
        "ent_coef": 0.01,          # Entropy coefficient (exploration bonus)
        "vf_coef": 0.5,            # Value function coefficient
        "max_grad_norm": 0.5,      # Gradient clipping
        "learning_rate": 3e-4,     # Constant LR (or use lr_schedule)
        "use_sde": False,          # State Dependent Exploration (advanced)
        "sde_sample_freq": -1,
    }

    if args.use_best_params and os.path.exists("data/optimization/best_hyperparams_ppo.txt"):
        print("🧪 Loading optimized PPO hyperparameters from data/optimization/best_hyperparams_ppo.txt...")
        try:
            with open("data/optimization/best_hyperparams_ppo.txt", "r") as f:
                best_params = ast.literal_eval(f.read())
            
            # Update params with best_params
            net_arch_type = best_params.pop("net_arch", None)
            
            if net_arch_type:
                architectures = {
                    "small": [dict(pi=[128, 128], vf=[128, 128])],
                    "medium": [dict(pi=[256, 256], vf=[256, 256])],
                    "large": [dict(pi=[512, 512], vf=[512, 512])]
                }
                policy_kwargs["net_arch"] = architectures.get(net_arch_type, architectures["medium"])
                print(f"   Architecture: {net_arch_type}")

            for k, v in best_params.items():
                if k in ppo_params:
                    ppo_params[k] = v
                else:
                    print(f"⚠️ Warning: Unknown param '{k}' in best_params. Ignoring.")
                    
            print(f"✅ Applied params: {ppo_params}")
        except Exception as e:
            print(f"⚠️ Failed to load best params: {e}")

    if args.load and os.path.exists(args.load):
        print(f"🔄 Loading existing PPO model from {args.load}...")
        
        # Load the model and attach new environment
        model = PPO.load(
            args.load,
            env=venv,
            device=device,
            print_system_info=True,
            # PPO.load garde sinon le LR sauvegardé : on applique --lr (constant)
            custom_objects={"learning_rate": args.lr, "lr_schedule": (lambda _: args.lr)},
        )
        print("✅ Model loaded successfully. Resuming training...")
    else:
        print(f"🧠 Initializing NEW PPO model...")
        model = PPO(
            "MlpPolicy",
            venv,
            device=device,
            verbose=1,
            tensorboard_log=_tb_log_dir(),
            policy_kwargs=policy_kwargs,
            **ppo_params
        )

    print("🏃 Starting PPO training...")
    print("ℹ️  PPO is on-policy: it learns from fresh experience collected with current policy")
    print(f"ℹ️  Each update uses {ppo_params['n_steps']} * {n_cpu} = {ppo_params['n_steps'] * n_cpu} steps")
    
    callbacks = [checkpoint_callback]
    if args.curriculum:
        callbacks.append(CurriculumCallback())
    
    try:
        model.learn(total_timesteps=args.steps, callback=callbacks)
    except KeyboardInterrupt:
        print("\n🛑 Training interrupted manually.")
    
    print("💾 Saving model...")
    os.makedirs("data/models/production", exist_ok=True)
    model.save(f"data/checkpoints/ppo_{args.run_id}_final")
    venv.save(f"data/checkpoints/ppo_{args.run_id}_final_vecnormalize.pkl")
    print(f"✅ Saved to data/checkpoints/ppo_{args.run_id}_final.zip")
    print(f"💡 To use this model, copy it to data/models/production/")
    
    # Print training summary
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print(f"📊 Total timesteps: {args.steps:,}")
    print(f"🧠 Algorithm: PPO (On-Policy)")
    print(f"💾 Model saved to: data/checkpoints/ppo_{args.run_id}_final.zip")
    print(f"📈 To monitor training: tensorboard --logdir=./logs/ppo_tensorboard/")
    print(f"🎮 To watch AI play: python3 rl_play.py --model data/checkpoints/ppo_{args.run_id}_final.zip")
    print("="*60)
    
    try:
        venv.close()
    except:
        pass


if __name__ == "__main__":
    # On macOS, 'spawn' is safer than 'fork' for libraries like Pygame/Torch
    try:
        import multiprocessing
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass
    main()
