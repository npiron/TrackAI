# Roadmap

> Maintained by the lead. Epics are the big steps toward the goal in `GOAL.md`, in priority order.
> Format of an epic (the loop reads the heading and the status line):
>
>     ### E1 · Title
>     - status: open | in-progress | done | dropped
>     - outcome: what is true when this epic is done, and how it is measured
>     - notes: scope, risks, what is out of scope

## Epics

### E7 · Étape 0 : recaler le professeur sur la physique Trackmania
- status: open
- outcome: pilote programmé réglé (constantes de `scripts/heuristic_lap.py`) : statique 20/20 sans choc et banc 50 pistes sans choc, temps minimal ; son temps statique (le « professeur réglé ») est écrit dans `metrics.json` et dans le critère ; borne `lower_bound.py` remesurée (ou échec documenté) ; baselines best/ (s5_a, v1) sur le banc remesurées avec la nouvelle physique.
- notes: stories S-13 à S-15. À faire AVANT E4 (obs v2) : S-11/S-12 peuvent tourner en parallèle mais E5 attend E7. Mesures d'avant la physique invalides (baseline S-10 : 3,18 chocs, ancienne physique).

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
- status: done
- result: s5_a promu (S-7) ; s8_a/s8_b (DAgger depuis s5_a) pires (S-8) ; plateau de l'ancien goal (obs v1), clos.
- outcome: `best/` = meilleur modèle mesuré (s5_a au minimum, 15,46 s) ; puis 2 candidats DAgger mixtes depuis s5_a, mesurés statique et procédural ; promotion si strictement meilleur, sinon verdict final de plateau.
- notes: dernier epic (règle « deux epics vitesse sans gain » : E3 est l'ultime tentative, ensuite plateau et arrêt). Pas de changement de physique, entraînements ≤ 10 min.

### E4 · Banc 50 pistes et observation v2
- status: open
- outcome: `eval.py --bench` (50 pistes graines 0-49) mesure best/ (baseline en metrics.json) ; `obs_version=2` disponible (steering réel, 5 points de ligne centrale en repère voiture, courbure, 9 lidars longs), v1 (14 valeurs) intacte par défaut ; eval/imitate chargent un modèle v1 ou v2 sans erreur.
- notes: stories S-10 à S-12. Physique inchangée. Mesure d'abord.

### E5 · Ré-imitation avec observation v2 (BC + DAgger, mix fixe + procédural)
- status: open
- outcome: modèle v2 au moins aussi rapide que le professeur réglé (E7) en statique, 0 choc et < 1 choc/course sur le banc 50 pistes ; promu dans best/ (ancien archivé).
- notes: dépend d'E7 (professeur réglé). Professeur étiqueté depuis `ta` (pas depuis obs v2). Entraînements ≤ 30 min. Stories écrites quand E4 est fini.

### E6 · Affinage PPO sans oubli depuis le modèle E5
- status: open
- outcome: PPO (lr faible, petit clip, perte d'imitation auxiliaire décroissante, récompense progression + pénalité de temps + forte pénalité par choc, 8 envs, mix fixe + procédural) : statique < 14,62 s, 0 choc ; banc procédural encore réduit. Critère A+B atteint.
- notes: dépend d'E5. Étape 4 du goal (professeur optimisé hors ligne) seulement si E6 plafonne.

## Decisions

- 2026-11-07 : Goal repris de `.team` (T1-T71). Fiabilité déjà atteinte par T65 (20/20, 0 choc, 15,84 s). « Plus bas possible » rendu mesurable : ≤ 15,30 s. Robustesse au bruit (24/100 à eps 0,05) jugée hors critère. Le temps humain manquant (action humaine) n'est pas attendu.

- 2026-11-07 : E1 clos sur plateau (15,84 s, 4 candidats DAgger plus lents et avec chocs, mesures reviewer dans metrics.json). Cible 15,30 s abandonnée ; on passe au bonus E2 (seul epic restant) avec la contrainte de ne pas dégrader best/.

- 2026-11-07 : E2 clos. Bonus procédural non atteint (19/20, 2,8 chocs) mais s5_a bat T65 partout (statique 15,46 s vs 15,84 s ; procédural 2,8 vs 20,2 chocs). Contrainte « garder le meilleur modèle dans best/ » : S-6 aurait dû le promouvoir ; E3 corrige (S-7), puis tente une dernière itération depuis s5_a (15,46 s est à 0,16 s de la cible 15,30 s). Si E3 échoue, GOAL en plateau documenté, arrêt.

- 2026-11-07 : Nouveau goal (cap : zéro choc sur pistes jamais vues, puis battre le professeur 14,62 s). Plateau de l'ancien goal (best/ = s5_a, 15,46 s statique, 2,8 chocs procédural) = point de départ. Critère mesurable A (banc 50 pistes < 1 choc/course) + B (statique < 14,62 s). Ordre : banc + obs v2 (E4), ré-imitation (E5), PPO (E6). Le banc manque : eval.py actuel tire des pistes aléatoires non fixées par graine de piste.

- 2026-11-07 : Goal modifié (étape 0 ajoutée, physique Trackmania). Mesures d'avant invalidées (pilote 12,56 s mais 10 chocs/course, best/ 19,48 s, 22 chocs). Nouvel epic E7 (recalage du professeur) placé avant E4/E5/E6 ; critère B se référera au temps du professeur réglé, mesuré par S-13/S-14. E5 dépend d'E7.
