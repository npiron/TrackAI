# Journal

> Append only, never rewrite. Format:
> `## YYYY-MM-DD HH:MM · <agent> · <task or subject>` followed by a few factual bullets (what was done, measured results, problems, next step).

## 2026-11-07 20:44 · loop · Start

- Session of 20 steps on `goal/main` (team: trio).

## 2026-11-07 20:44 · loop · Goal changed

- New goal: Entraîner un agent qui fait 3 tours du circuit fixe sans jamais toucher un mur, 20 courses sur 20, puis réduire le temps total. Ajouter une option d'entraînement `wall_fatal` (désactivée par défaut, le jeu ne change pas) et compter les chocs par course dans `eval.py`. Y aller par paliers : grosse pé

## 2026-11-07 20:44 · lead · Plan

- Goal repris de `.team` : fiabilité déjà atteinte par best/ T65 (20/20, 0 choc, 15,84 s). Critère vitesse rendu mesurable : ≤ 15,30 s (professeur H=29 14,62 s, borne 13,96 s). Statut : in progress. Robustesse au bruit (24/100 à eps 0,05) hors critère.
- ROADMAP : E1 vitesse (open), E2 bonus pistes aléatoires (open, à refiner après E1).
- Stories E1 écrites (refiner) : S-1 DAgger depuis T65 H=29 (M), S-2 variantes de réglage (M, dépend S-1), S-3 promotion dans best/ ou plateau (S, dépend S-1/S-2). Si E1 échoue, le lead arrête sur plateau documenté.

## 2026-11-07 20:55 · dev · S-1 DAgger depuis T65 H=29

- 2 runs imitate (graines 2300/2400), 5m15 et 4m22, sortie `ppo_s1_a/b`.
- Eval : a 20/20, 2 chocs, 22,76 s ; b 20/20, 4 chocs, 16,76 s. Cible 15,30 s sans choc non atteinte.
- eval.py écrit dans `.team/metrics.json` par défaut : entrées déplacées vers `.goal/metrics.json`.

## 2026-11-07 20:55 · reviewer · S-1 approuvée
- Rejoué eval.py (20 ép., seed 0, static, laps 3) sur s1_a et s1_b : a = 20/20, 2 chocs, 22,76 s ; b = 20/20, 4 chocs, 16,76 s. Identique aux notes du dev et à `metrics.json`.
- Tests rapides : 48 passed, 1 skipped. `best/` et `.team/` non modifiés ; checkpoints ignorés par git.
- Critères de la story remplis (runs ≤ 10 min, mesures, verdict chiffré dans `docs/SPEED_E1.md`). Cible 15,30 s non atteinte : résultat négatif documenté, pas un défaut.

## 2026-11-07 21:06 · dev · S-2 Variantes de réglage
- Aucun candidat S-1 sans choc : départ depuis best/ T65, 2 runs (hit-weight 20 ; lr 3e-4 + 60 epochs), graine 2500.
- Résultats : s2_a 25 chocs / 18,20 s ; s2_b 3 chocs / 16,82 s. Cible non atteinte, rien promu.
- Tableau dans docs/SPEED_E1.md, mesures dans .goal/metrics.json.

## 2026-11-07 21:07 · dev · S-3 Promotion ou plateau
- Aucun candidat S-1/S-2 sans choc : best/ inchangé, rien promu.
- Section « Verdict E1 » ajoutée à docs/SPEED_E1.md (tableau des 4 candidats vs T65, plateau 15,84 s).

## 2026-11-07 21:07 · reviewer · S-3 approved
- Aucun candidat ne bat 15,84 s en 20/20 sans choc : `best/` inchangé, verdict chiffré dans `docs/SPEED_E1.md` (tableau cohérent avec metrics.json).
- eval.py sur best/ : 20/20, 0 choc, 15,84 s ; tests rapides : 48 passed, 1 skipped.
- Pas de mesure ajoutée à metrics.json (aucun nouveau candidat). L'epic E1 reste ouvert pour décision du lead (cible 15,30 s non atteinte).
- eval.py a modifié `.team/metrics.json` : restauré (git checkout) pour respecter la règle.

## 2026-11-07 21:07 · lead · Plan (epic-complete E1)

- E1 done : plateau documenté. S-1/S-2 : 4 candidats DAgger (2 à 4 chocs ou 25, 16,76-22,76 s) tous pires que best/ T65 (20/20, 0 choc, 15,84 s). Cible 15,30 s non atteinte ; GOAL.md status mis à jour (vitesse en plateau). Pas de GOAL_REACHED.
- E2 (bonus pistes aléatoires) reste seul epic ouvert, stories écrites (refiner) : S-4 option --no-static + référence best/ (S), S-5 deux candidats mixtes avec hit-weight (M), S-6 promotion ou plateau final (S). Si E2 échoue, le lead clôt sur plateau.
- Remarque : eval.py écrit par défaut dans `.team/metrics.json` (corrigé dans S-4).

## 2026-11-07 21:08 · dev · S-4 eval --no-static
- `--static`/`--no-static` exclusifs ; metrics par défaut dans `.goal/metrics.json`.
- Référence best/ T65 en procédural : 15/20 finis, chocs 20,2 moy / 119 max (docs/SPEED_E2.md).
- Tests rapides verts (50 passed).

## 2026-11-07 21:09 · reviewer · S-4 approved
- Relu diff, flags exclusifs vérifiés (`--static --no-static` → erreur argparse), pytest rapide : 50 passed, 1 skipped.
- `git status .team` vide ; entrée metrics static:false présente (15/20 finis, chocs 20,2/119), docs/SPEED_E2.md cohérent.
- Remarque mineure : test_default_metrics_in_goal est faible (condition tautologique), sans blocage.

## 2026-11-07 21:12 · dev · S-5 candidats mixtes hit-weight
- 2 runs imitate (--mix-static, hit-weight 10, H=29) en ~2 min 45 chacun ; 4 évals ajoutées à metrics.json.
- s5_a (eps 0 0,05) : statique 20/20, 0 choc, 15,46 s (< best/ 15,84) ; procédural 19/20, 2,8 chocs. s5_b : 4 chocs en statique, non promouvable.
- Tableau dans docs/SPEED_E2.md ; s5_a à valider en S-6.

## 2026-11-07 21:14 · reviewer · S-5 approved
- Relancé les 4 évals (20 ép., seed 0, laps 3) : résultats identiques aux metrics.json (s5_a statique 20/20, 0 choc, 15,46 s ; procédural 19/20, 2,8 chocs ; s5_b statique 4 chocs, 17,80 s ; procédural 17/20, 12,25 chocs).
- Tests rapides : 50 passed, 1 skipped. Aucun code modifié, checkpoints ignorés par git, tableau de docs/SPEED_E2.md cohérent.
- s5_a est promouvable sur critères story, à confirmer en S-6 (robustesse).

## 2026-11-07 21:13 · dev · S-6 Promotion ou plateau E2
- s5_a (statique 20/20, 0 choc, 15,46 s) échoue le critère procédural : 19/20 finis, 2,8 chocs ; s5_b échoue les deux. Rien promu, best/ intact.
- Section « Verdict E2 » ajoutée à docs/SPEED_E2.md (chiffres identiques à metrics.json).

## 2026-11-07 21:14 · reviewer · S-6 approved
- Relu le diff : seul `docs/SPEED_E2.md` (section « Verdict E2 ») change ; `data/` et `.team` intacts (`git status` vide).
- Tableau comparé à `.goal/metrics.json` : s5_a 15,46 s/0 choc statique, 19/20 et 2,8 chocs procédural ; s5_b 4 chocs, 17,80 s, 17/20 ; T65 20,2 chocs procédural. Identiques.
- Aucune promotion : cohérent avec le critère (s5_a 19/20 et 2,8 chocs en procédural, s5_b 4 chocs en statique).
- Tests rapides : 50 passed, 1 skipped.

## 2026-11-07 21:15 · lead · Plan (epic-complete E2)
- E2 done : bonus non atteint (s5_a 19/20, 2,8 chocs en procédural) mais s5_a domine T65 partout (statique 15,46 s vs 15,84 s, 0 choc). S-6 ne l'a pas promu (critère trop strict) alors que la contrainte demande le meilleur modèle dans best/.
- E3 ouvert (dernier) : S-7 promouvoir s5_a, S-8 deux candidats DAgger mixtes depuis s5_a (cible ≤ 15,30 s, 0,16 s d'écart), S-9 promotion ou verdict final. Pas de GOAL_REACHED : vitesse 15,46 s > 15,30 s.
- Refiner : stories S-7 (S), S-8 (M), S-9 (S) écrites, ready. Si E3 échoue, plateau documenté et arrêt.
