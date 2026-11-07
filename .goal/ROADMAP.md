# Roadmap

> Maintained by the lead. Epics are the big steps toward the goal in `GOAL.md`, in priority order.
> Format of an epic (the loop reads the heading and the status line):
>
>     ### E1 · Title
>     - status: open | in-progress | done | dropped
>     - outcome: what is true when this epic is done, and how it is measured
>     - notes: scope, risks, what is out of scope

## Epics

### E1 · Vitesse : passer sous 15,30 s sans choc depuis best/ T65
- status: open
- outcome: un modèle candidat mesuré par eval.py (20 ép., seed 0, --static, laps 3) à 20/20, 0 choc, ≤ 15,30 s, copié dans `data/models/best/` avec sa mesure (ancien T65 dans `data/models/best_t65/`) ; sinon verdict chiffré de plateau.
- notes: fiabilité déjà atteinte (T65 15,84 s). Professeur H=29 à 14,62 s mais fragile au bruit ; seul le critère déterministe compte. Pas de changement de physique. Entraînements ≤ 10 min. Robustesse au bruit : hors critère, à noter seulement.

### E2 · Bonus : pistes aléatoires jamais vues
- status: open
- outcome: eval.py `--no-static` (20 ép., seed 0, laps 3) avec 20/20 finis et 0 choc moyen, sans casser le critère statique.
- notes: T67 mix statique/procédural : 19/20, 7,35 chocs. À refiner seulement après E1 ; priorité basse.

## Decisions

- 2026-11-07 : Goal repris de `.team` (T1-T71). Fiabilité déjà atteinte par T65 (20/20, 0 choc, 15,84 s). « Plus bas possible » rendu mesurable : ≤ 15,30 s. Robustesse au bruit (24/100 à eps 0,05) jugée hors critère. Le temps humain manquant (action humaine) n'est pas attendu.
