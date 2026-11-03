# Audit T29

### data/models/best/best.zip

success=True, temps total=17.74 s, steps=887, demi-largeur route=59 px, longueur ligne centrale=3032 px (2400 pts), checkpoints=8

| tour | temps s | v moy | v max | chemin px | couverture ligne | ordre cp | min dist bord px (demi-largeur mesurée) | frames hors piste | frames contact mur | max saut idx |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6.12 | 9.13 | 15.62 | 2658 | 0.960 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.8 | 0 | 0 | 42 |
| 2 | 5.74 | 10.35 | 16.43 | 2834 | 1.002 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.2 | 0 | 0 | 39 |
| 3 | 5.88 | 10.11 | 16.89 | 2841 | 1.000 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.9 | 0 | 0 | 47 |

### heuristic

success=True, temps total=17.94 s, steps=897, demi-largeur route=59 px, longueur ligne centrale=3032 px (2400 pts), checkpoints=8

| tour | temps s | v moy | v max | chemin px | couverture ligne | ordre cp | min dist bord px (demi-largeur mesurée) | frames hors piste | frames contact mur | max saut idx |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6.06 | 9.27 | 15.98 | 2672 | 0.963 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.8 | 0 | 0 | 42 |
| 2 | 6.06 | 9.81 | 16.66 | 2823 | 0.999 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.6 | 0 | 0 | 32 |
| 3 | 5.82 | 10.00 | 15.40 | 2768 | 1.000 | [0, 1, 2, 3, 4, 5, 6, 7] OK | -0.8 | 0 | 0 | 35 |


## Verdict : VALIDE (pas de faille de comptage)

- Commande : `SDL_VIDEODRIVER=dummy .venv/bin/python scripts/audit_lap.py --static --laps 3 --out docs/AUDIT_T29.md` (deux lancements → fichier identique, `cmp`).
- Les 8 checkpoints sont franchis dans l'ordre 0..7 à chacun des 3 tours, pour `best/` (17,74 s) et l'heuristique (17,94 s) : aucun checkpoint sauté.
- Couverture de la ligne centrale ≈ 1,00 par tour (0,96 au 1er tour : départ ~4 % après l'indice 0 de la spline) ; plus grand saut d'indice entre deux frames : 47 points sur 2400 (≈ 59 px) → aucune téléportation ni raccourci de section. Chemin parcouru 2660-2840 px par tour pour une ligne centrale de 3032 px : la trajectoire est tendue (coupe des cordes à l'intérieur des virages) mais reste dans la route.
- 0 frame hors piste, 0 frame de contact mur (déplacement = vitesse à chaque frame). Distance au bord min ≈ -0,9 px (nulle à la précision de l'échantillonnage de la spline, demi-largeur route 59 px mesurée sur le masque ; `TRACK_WIDTH/2 = 45` n'est pas la largeur réelle) : la voiture rase le bord dans les virages sans le dépasser.
- Remarque : `CHECKPOINT_RADIUS = FINISH_RADIUS = 100 px` est supérieur à la largeur de route (118 px) ; un checkpoint est validé à ~100 px, donc très permissif, mais l'ordre et la couverture complets montrent qu'il n'est pas exploité ici. Pas de correctif nécessaire.
- Limite : audit sur piste fixe, seed 0, politique déterministe ; la couverture est calculée par indice de spline le plus proche.
