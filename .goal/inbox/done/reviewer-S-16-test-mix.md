# Test du mix fixe/procédural trop faible (suite S-16)
`test_collect_mix_static_v2` ne vérifie que la taille d'obs v2, pas que les épisodes pairs sont sur piste fixe et les impairs sur piste procédurale. À renforcer (petite story). Aussi : `data/human_best.json` est écrit par les runs (PB) et traîne en untracked ; l'ajouter au .gitignore ?
