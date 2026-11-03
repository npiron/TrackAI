# Objectif

verifier le gameplay et la physique du jeu, et avoir une simulation realiste

## Contraintes

- pas de scxreenshot de l' app

## Critère de réussite

> Rempli par le planificateur, ne pas éditer à la main.

- critère : `scripts/physics_check.py` (headless, sans capture d'écran, graine fixe) exécute des scénarios déterministes sur `src/game/env.py` (accélération, vitesse max, freinage, friction, virage/rayon, adhérence latérale, mur, boost, checkpoints/arrivée, reproductibilité) et écrit une entrée `physics_check` dans `.team/metrics.json` ; atteint quand 100 % des scénarios passent leurs bornes réalistes documentées (seuils dans le script) ET que les écarts de réalisme trouvés sont corrigés ou documentés comme choix arcade assumé, validé par le reviewer.
- statut : en cours (banc T7-T10 validé, écarts triés ; 4 corrections à faire T11-T15 ; entrée `physics_check` pas encore dans metrics.json)
