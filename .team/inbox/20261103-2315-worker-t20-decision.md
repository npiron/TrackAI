# T20 : décision et reste à faire
- Reprise de best (T19) avec `--laps 3`, 200k steps (~9 min) : eval 20 ép. `--laps 3` → finish_rate 0.0, mean_checkpoints 2.0 (1.0 avant), mean_laps_done 0.0, épisodes au timeout (6000 steps).
- Décision : `data/models/best/` NON mis à jour (finish_rate inchangé 0). Modèle : data/checkpoints/ppo_t20_final.zip.
- Cause probable : la récompense ne fait pas passer le 2e/3e checkpoint ; la voiture s'arrête vers 2 checkpoints. Pistes : examiner la récompense (progrès/checkpoints), entraîner laps=1 plus longtemps d'abord, ou curriculum. Reste : 20/20 à obtenir.
- rl_train_ppo.py : ajout `--laps` et reprise des stats VecNormalize avec `--load`.
