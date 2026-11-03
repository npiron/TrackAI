# Équipe d'agents TrackAI

Trois agents Claude Code améliorent le projet en boucle, en se coordonnant uniquement par les fichiers de ce dossier.

| Agent | Rôle | Écrit dans |
|---|---|---|
| `planner` | Chef de projet : tient la feuille de route et la todo, ne code jamais | `ROADMAP.md`, `TODO.md`, `JOURNAL.md`, vide `inbox/` |
| `worker` | Développeur : réalise une tâche par itération, ne commit jamais | code, statut dans `TODO.md`, `JOURNAL.md`, `inbox/` |
| `reviewer` | Testeur : relit et teste tout le code, seul à commiter | `JOURNAL.md`, `inbox/`, statut dans `TODO.md`, commits |

## Fichiers partagés

- `ROADMAP.md` : vision, jalons, décisions. Change de direction quand les faits l'exigent.
- `TODO.md` : tâches priorisées avec un critère de fin vérifiable.
- `inbox/` : un fichier par message (`AAAAMMJJ-HHMM-<auteur>-<sujet>.md`). N'importe quel agent y propose une tâche, signale un blocage ou une découverte. Le planificateur les intègre puis les déplace dans `inbox/traite/`.
- `JOURNAL.md` : historique partagé, on ajoute en bas, on ne réécrit jamais.
- `metrics.json` : résultats du banc d'éval, une entrée par mesure.
- `REPLAN` : si ce fichier existe, la boucle lance le planificateur avant la prochaine tâche.
- `STOP` : si ce fichier existe, la boucle s'arrête proprement à la fin de l'étape en cours.
- `logs/` : sortie brute de chaque appel (hors git).

## Cycle d'une tâche

```
[ ] à faire → [~] en cours (worker) → [?] à relire (worker)
   → [x] validée + commit (reviewer)
   → [-] à reprendre + retour dans inbox (reviewer) → le worker la reprend
   → [!] bloquée après 3 essais → le planificateur décide
```

## Lancer

```bash
./team_loop.sh          # 10 itérations
./team_loop.sh 25       # 25 itérations
touch .team/STOP        # arrêter proprement depuis un autre terminal
```
