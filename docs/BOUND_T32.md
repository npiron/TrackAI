# Borne inférieure du temps sur 3 tours (T32)

Généré par `scripts/lower_bound.py` (déterministe). Physique mesurée sur `env.step`, non modifiée.

## Mesures de la physique

- Constantes : ACCEL=0.18, FRICTION=0.992, COAST_FRICTION=0.975, BRAKE=0.5, TURN_SPEED=0.08, MAX_SPEED=23.0.
- Vitesse terminale mesurée (gain nul plein gaz) : **22.50 px/frame** (= 1125 px/s).
- Gain de vitesse par frame (px/frame²) :

| v | plein gaz | frein seul | frein+gaz |
|---|---|---|---|
| 0 | +0.179 | +0.000 | +0.000 |
| 5 | +0.139 | -0.612 | -0.357 |
| 10 | +0.099 | -0.738 | -0.397 |
| 15 | +0.059 | -0.863 | -0.437 |
| 20 | +0.019 | -0.988 | -0.477 |

- Courbure max en régime établi (braquage plein, vitesse maintenue), rayon mini correspondant :

| v | kappa_max (1/px) | rayon mini (px) |
|---|---|---|
| 2 | 0.04234 | 24 |
| 5 | 0.01620 | 62 |
| 8 | 0.00968 | 103 |
| 11 | 0.00671 | 149 |
| 14 | 0.00502 | 199 |
| 17 | 0.00393 | 255 |
| 20 | 0.00317 | 316 |
| 23 | 0.00260 | 384 |

## Calibration de la fenêtre de courbure

La courbure ponctuelle est trop pessimiste (le cap peut changer sur une distance, la voiture a une largeur de route) : on mesure sur la trajectoire réelle du meilleur tour (heuristique, 795 frames = 15.90 s) la part des points où sa vitesse dépasse la limite `vmax(kappa)` pour une courbure de Menger de demi-fenêtre k nœuds (7,6 px/nœud). Aucune fenêtre n'élimine toutes les violations (transitoires, glissements) : on retient celle qui en a le moins (k le plus petit à égalité).

| k (nœuds) | portée ± (px) | points en violation | v/vmax max |
|---|---|---|---|
| 2 | 15 | 5.0 % | 11.15 |
| 4 | 30 | 5.2 % | 5.73 |
| 6 | 46 | 4.4 % | 3.81 |
| 8 | 61 | 3.7 % | 2.90 |
| 10 | 76 | 3.4 % | 2.39 |
| 12 | 91 | 2.8 % | 2.08 |
| 14 | 106 | 1.9 % | 1.86 |
| 16 | 122 | 1.4 % | 1.70 |
| 20 | 152 | 1.7 % | 1.48 |
| 24 | 182 | 1.9 % | 1.33 |

- Fenêtre retenue : **k = 16** (±122 px).


## Trajectoires

- Piste fixe, spline de 2400 points (pas 6 -> 400 nœuds), demi-largeur de route minimale mesurée 58 px (marge 0 : le centre de la voiture peut raser le bord, optimiste).
- Ligne de course : décalages relaxés (lissage) bornés par le couloir ; aucune contrainte de dynamique.

| trajectoire | longueur/tour (px) | courbure max (1/px) | v moy (px/frame) | 1er tour (s) | tour lancé (s) | crédit arrivée (s) | **total (s)** |
|---|---|---|---|---|---|---|---|
| ligne centrale | 3032 | 0.00792 | 13.03 | 5.63 | 4.65 | 0.17 | **14.77** |
| ligne de course | 2591 | 0.01015 | 11.58 | 5.20 | 4.48 | 0.20 | **13.96** |

### Sensibilité à la fenêtre

| k | ligne centrale (s) | ligne de course (s) |
|---|---|---|
| 8 | 17.62 | 16.62 |
| 12 | 15.98 | 14.96 |
| 16 | 14.77 | 13.96 |
| 20 | 13.94 | 13.32 |
| 24 | 13.57 | 12.92 |

La borne est **modèle-dépendante** : plus la fenêtre est large, plus elle est optimiste (donc plus basse).

## Hypothèses (toutes favorables à la borne, donc elle est optimiste)

- Voiture = point ; tangage/latéral du modèle ignorés : la limite de virage est la courbure en régime établi à vitesse constante (le transitoire du volant, ~7 frames, et le glissement `LATERAL_GRIP` sont ignorés).
- Accélération/freinage en ligne droite, courbure indépendante du freinage, freinage optimal (frein seul ou frein+gaz, le plus fort).
- Aucun mur, marge de bord 0, pas de boost (aucune zone sur cette piste).
- Fin du dernier tour dès que la voiture est à FINISH_RADIUS=100 px de l'arrivée (crédit ci-dessus ; en pratique les checkpoints exigent aussi de passer à moins de 100 px de chacun).
- Distance/temps par segment : v² = v0² + 2 a ds, temps = 2 ds / (v0 + v1).

## Résultat

- Borne (meilleure des deux trajectoires) : **13.96 s** sur 3 tours.
- Meilleur temps atteint : **15.90 s** -> écart **+1.94 s** (+12.2 %).
- Intervalle de sensibilité (k=12..24, ligne de course) : 12.92-14.96 s.
- Recommandation : **Continuer la recherche** : la borne laisse plus d'une seconde (heuristique/imitation à paramétrer par secteur, cf. T33).
- Limite : la fenêtre est calibrée sur la trajectoire réelle (1,4 % de ses points restent en violation), ce n'est donc pas une borne mathématiquement rigoureuse mais une estimation du plafond du modèle.
