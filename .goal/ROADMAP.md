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
- status: done
- outcome: un modèle candidat mesuré par eval.py (20 ép., seed 0, --static, laps 3) à 20/20, 0 choc, ≤ 15,30 s, copié dans `data/models/best/` avec sa mesure (ancien T65 dans `data/models/best_t65/`) ; sinon verdict chiffré de plateau.
- result: plateau documenté (docs/SPEED_E1.md) : 4 candidats DAgger (S-1, S-2), aucun sans choc ni plus rapide que T65 15,84 s.
- notes: fiabilité déjà atteinte (T65 15,84 s). Professeur H=29 à 14,62 s mais fragile au bruit ; seul le critère déterministe compte. Pas de changement de physique. Entraînements ≤ 10 min. Robustesse au bruit : hors critère, à noter seulement.

### E2 · Bonus : pistes aléatoires jamais vues
- status: done
- result: s5_a (mix statique+procédural, hit-weight 10) : statique 20/20, 0 choc, 15,46 s ; procédural 19/20, 2,8 chocs. Critère bonus non atteint, mais s5_a domine T65 sur toutes les mesures (non promu par S-6, critère de promotion trop strict).
- outcome: eval.py `--no-static` (20 ép., seed 0, laps 3) avec 20/20 finis et 0 choc moyen, sans casser le critère statique.
- notes: T67 mix statique/procédural : 19/20, 7,35 chocs. Stories S-4 à S-6. Si échec, plateau final (deuxième epic sans gain).

### E3 · Promouvoir s5_a puis dernier essai depuis lui (vitesse ≤ 15,30 s, procédural propre)
- status: open
- outcome: `best/` = meilleur modèle mesuré (s5_a au minimum, 15,46 s) ; puis 2 candidats DAgger mixtes depuis s5_a, mesurés statique et procédural ; promotion si strictement meilleur, sinon verdict final de plateau.
- notes: dernier epic (règle « deux epics vitesse sans gain » : E3 est l'ultime tentative, ensuite plateau et arrêt). Pas de changement de physique, entraînements ≤ 10 min.

## Decisions

- 2026-11-07 : Goal repris de `.team` (T1-T71). Fiabilité déjà atteinte par T65 (20/20, 0 choc, 15,84 s). « Plus bas possible » rendu mesurable : ≤ 15,30 s. Robustesse au bruit (24/100 à eps 0,05) jugée hors critère. Le temps humain manquant (action humaine) n'est pas attendu.

- 2026-11-07 : E1 clos sur plateau (15,84 s, 4 candidats DAgger plus lents et avec chocs, mesures reviewer dans metrics.json). Cible 15,30 s abandonnée ; on passe au bonus E2 (seul epic restant) avec la contrainte de ne pas dégrader best/.

- 2026-11-07 : E2 clos. Bonus procédural non atteint (19/20, 2,8 chocs) mais s5_a bat T65 partout (statique 15,46 s vs 15,84 s ; procédural 2,8 vs 20,2 chocs). Contrainte « garder le meilleur modèle dans best/ » : S-6 aurait dû le promouvoir ; E3 corrige (S-7), puis tente une dernière itération depuis s5_a (15,46 s est à 0,16 s de la cible 15,30 s). Si E3 échoue, GOAL en plateau documenté, arrêt.
