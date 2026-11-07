# Borne inférieure du temps, physique Trackmania (S-15)

Remplace `docs/BOUND_T32.md` (13,96 s, invalide : ancienne physique).

## Commandes

```
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/lower_bound.py --laps 3 --reference 14.12            # k calibré
SDL_VIDEODRIVER=dummy .venv/bin/python scripts/lower_bound.py --laps 3 --reference 14.12 --kwin 24  # k forcé
```

Référence : professeur réglé de S-14, 3 tours, piste fixe : **14,12 s** (706 frames).

## Adaptation du script (≈10 lignes)

`measure_cornering` forçait `car.speed = v` pour tenir la vitesse, mais la physique lit désormais `vel` (`speed` en est la projection) : la limite de virage était fausse (rayon mini ~101-131 px quasi constant). Ajout de `_hold()` qui rescale `vel`. Nouvelle mesure : kappa_max décroît avec la vitesse (rayon mini 107 px à v=2, 282 px à v=20, 388 px à v=23), conforme au braquage utile qui baisse avec la vitesse. Mesures longitudinales inchangées et cohérentes (terminal 22,5 px/frame ; départ +0,268, plein gaz +0,028 à v=20). La phrase de recommandation signale désormais une borne invalide si elle dépasse le temps atteint.

## Résultats

| fenêtre k | ligne centrale | ligne de course |
|---|---|---|
| **6 (calibré par le script)** | 32,59 s | 31,69 s |
| 12 | 20,24 s | 24,12 s |
| 16 | 15,08 s | 19,92 s |
| 20 | 13,34 s | 16,20 s |
| **24 (forcé)** | **12,77 s** | 14,55 s |

- **Calibration par défaut : échec, borne absurde** (31,69 s > 14,12 s). Le script choisit le plus petit k sans violation sur la trajectoire réelle (k=6, ±46 px) ; or la ligne centrale/relaxée a une courbure plus forte que la trajectoire réelle sur cette fenêtre, donc la limite de vitesse est trop basse. Tout k ≥ 6 ne produit aucune violation sur la trajectoire réelle (v/vmax max 1,00 à k=6, 0,93 à k=24) : la calibration ne départage pas.
- **Avec k=24 (±182 px, plus grande fenêtre testée)** : borne **12,77 s** (ligne centrale), soit un écart de **1,35 s (9,5 %)** avec le professeur réglé. Plus k est grand, plus la borne baisse : ce chiffre est une estimation optimiste dépendante du modèle, pas une borne rigoureuse.
- Ancienne borne 13,96 s pour 15,90 s (écart 1,94 s) ; nouvelle estimation 12,77 s pour 14,12 s.

## Conclusion

Le professeur réglé est à environ 1,3 s (≈ 9 %) de l'estimation optimiste, avec la réserve ci-dessus : sans critère objectif pour fixer k, l'écart réel est plus petit (la borne à k=16-20 est à 13,3-15,1 s, soit un écart de 0 à 0,8 s). Marge faible mais non nulle pour l'étape 4 optionnelle.
