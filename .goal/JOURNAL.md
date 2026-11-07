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
