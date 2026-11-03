# Diagnostic T21 — pourquoi t19/t20 s'arrêtent

Commandes (piste fixe, déterministe ; les 5 épisodes sont identiques, résultat reproduit à l'identique sur 2 lancements) :

    SDL_VIDEODRIVER=dummy .venv/bin/python scripts/diagnose.py --model data/checkpoints/ppo_t19_final.zip --static --laps 1 --episodes 5 --seed 0
    SDL_VIDEODRIVER=dummy .venv/bin/python scripts/diagnose.py --model data/checkpoints/ppo_t20_final.zip --static --laps 3 --episodes 5 --seed 0

## Résultats (par épisode, identiques)

| modèle | dernier cp | position finale | vitesse moy. (px/frame) | frames à l'arrêt (<1) | fin |
|---|---|---|---|---|---|
| t19 (1 tour) | 1/8 | (1199, 649) | 0.095 | 1928 / 2000 (96 %) | timeout |
| t20 (3 tours) | 2/8 | (793, 928) | 0.115 | 5840 / 6000 (97 %) | timeout |

Récompense cumulée par composante :

| composante | t19 | t20 |
|---|---|---|
| progress | -410.4 | -210.0 |
| alignment | +192.5 | +114.6 |
| checkpoint | +172.5 | +367.5 |
| speed | +92.2 | +135.4 |
| urgency | -199.9 | -592.6 |
| track (+0.1/frame sur piste) | +199.9 | +599.9 |
| env / timeout | -50 | -50 |
| total | -3.2 | +364.8 |

## Cause dominante

La voiture **s'immobilise contre un mur (distance au centre ≈ 58 sur un rayon de route de 60 pour t20 ; 17.7 pour t19) peu après le dernier checkpoint** (t19 : arrêt dès la frame ~32, t20 : frame ~81), puis reste à l'arrêt en spammant des actions « frein » (2, 7, 8) jusqu'au timeout. Ce n'est pas un détecteur « bloqué » : `wall_stuck` ne se déclenche jamais car la voiture est considérée sur la piste (`inside_track`).

Ce qui rend l'arrêt « rentable » (récompense par frame immobile) :
- `track_penalty` donne **+0.1 par frame sur piste**, même à l'arrêt : +200 (t19) / +600 (t20) cumulés, ce qui compense presque entièrement `urgency` (-0.1/frame) ;
- le `progress` n'est pas une pénalité par frame : immobile = 0, il n'y a donc aucun coût à rester arrêté, à part -50 de timeout ;
- le bonus de checkpoint (+100/+150) est ponctuel ; après le dernier atteint, le gradient de progress est la seule incitation et PPO préfère visiblement le bruit nul.
- le total de t20 (+365) est positif alors que la voiture est bloquée à 2/8 : le score masque l'échec.

Piste de correction pour T23 (config de récompense, pas la physique) : supprimer/neutraliser le +0.1 « sur piste » (ou le conditionner à la vitesse), pénaliser l'arrêt (urgency sans seuil de distance, plus forte), terminer l'épisode sur arrêt prolongé (> ~150 frames à vitesse < 1, pas seulement hors piste).

## Limites
- Un seul scénario (piste fixe, politique déterministe) : un seul comportement observé ; la raison pour laquelle l'agent choisit le frein au premier virage n'est pas élucidée (probable sortie de distribution des observations après le premier choc mural).
- Position/obs exacts du mur non cartographiés au-delà des deux instantanés.
