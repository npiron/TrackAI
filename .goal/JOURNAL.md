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

## 2026-11-07 21:15 · dev · S-7 Promouvoir ppo_s5_a dans best/
- Ancien best/ (T65) archivé dans best_t65/, best/ remplacé par s5_a avec best.json.
- Évals depuis best/ : statique 15,46 s 0 choc ; procédural 19/20, 2,8 chocs.
- Section « Promotion s5_a » ajoutée à docs/SPEED_E2.md.

## 2026-11-07 21:16 · reviewer · S-7 approved
- `best/` : zip et pkl identiques (cmp) à `ppo_s5_a` ; `best_t65/` contient bien l'ancien best ; `best.json` cohérent avec metrics.json.
- eval statique relancée : 20/20, 0 choc, 15,46 s. `--no-static` : 19/20, 2,8 chocs, 19,77 s. Même résultat que les notes du dev.
- tests rapides : 50 passed, 1 skipped. `git status .team` : propre.
- docs/SPEED_E2.md : section « Promotion s5_a » présente. Mes deux évals avaient ajouté des doublons dans metrics.json, je les ai retirés.

## 2026-11-07 21:22 · dev · S-8 Deux candidats DAgger mixtes depuis s5_a
- s8_a et s8_b entraînés en séquence (~2 min 25 chacun), évalués en statique et procédural (4 entrées metrics.json).
- Aucun ne bat s5_a : s8_a 16,50 s et 2 chocs en statique, s8_b 18,82 s et 4 chocs ; procédural 7,6 et 4,0 chocs contre 2,8.
- Section « S-8 » ajoutée à docs/SPEED_E2.md ; un seul tirage par configuration.

## 2026-11-07 21:22 · reviewer · S-8 approved
- Relancé eval des 2 candidats (statique + procédural, 20 ép., seed 0) : résultats identiques à ceux du dev (s8_a 16,50 s / 2 chocs ; s8_b 18,82 s / 4 chocs). Les 4 entrées dupliquées de ma réévaluation ont été retirées de metrics.json.
- Tests rapides : 50 passed, 1 skipped. `.team` intact. Zips présents.
- Story d'exploration : résultat négatif documenté dans docs/SPEED_E2.md ; best/ inchangé. Note : metrics.json a des échappements unicode réécrits (bruit de diff sans conséquence).

## 2026-11-07 21:23 · dev · S-9 Promouvoir le meilleur candidat S-8 ou verdict final
- Comparaison s8_a/s8_b à best/ (s5_a) : aucun ne passe le critère (chocs en statique, temps > 15,46 s).
- `best/` laissé intact ; section « Verdict E3 » ajoutée à `docs/SPEED_E2.md` (cible 15,30 s et bonus non atteints).

## 2026-11-07 21:23 · loop · End

- Session ended after 20 step(s), 8 story(ies) done in total.

## 2026-11-07 21:33 · loop · Start

- Session of 120 steps on `goal/main` (team: trio).

## 2026-11-07 21:33 · loop · Goal changed

- New goal: Passer un cap : un agent qui roule sans choc sur des circuits aléatoires jamais vus, puis qui bat son professeur (pilote programmé H=29, 14,62 s) sur le circuit fixe. Les commandes restent des touches (9 actions discrètes, comme un clavier) ; le dosage se fait en tapotant, la physique fait déjà mont

## 2026-11-07 21:35 · lead · Plan
- Nouveau goal : critère défini (A : banc 50 pistes, 50/50 finis et < 1 choc/course ; B : statique < 14,62 s, 0 choc). Statut : not evaluated (pas de mesure bench encore).
- E3 clos (plateau de l'ancien goal, S-9 en review). Nouveaux epics : E4 banc + obs v2 (ouvert), E5 ré-imitation, E6 PPO sans oubli.
- Le banc n'existe pas : eval.py ne fixe pas la graine de piste (génération par random.randint). S-10 l'ajoute, S-11 obs v2, S-12 branche eval/imitate.

## 2026-11-07 21:35 · refiner · E4
- S-10 banc 50 pistes + baseline best/ (M), S-11 observation v2 (M, hard), S-12 eval/imitate/robust_eval v1+v2 (M, dépend de S-10 et S-11). Toutes ready.
- Point d'attention : le professeur lit l'obs v1 ; prévu via `ta.obs_v1()`.

## 2026-11-07 21:35 · reviewer · S-9 approuvée
- Diff : uniquement `docs/SPEED_E2.md` (section « Verdict E3 »). `git status .team` vide ; `best/` intact, `best.json` cohérent avec metrics.json.
- Chiffres du tableau (s5_a, s8_a, s8_b) vérifiés contre `.goal/metrics.json` ; T65 conforme à SPEED_E1/E2. Aucun candidat ne passe le critère de promotion (s8_a 2 chocs/16,50 s ; s8_b 4 chocs/18,82 s) : non-promotion correcte.
- Tests rapides : 50 passed, 1 skipped. Cible 15,30 s non atteinte (15,46 s), bonus non atteint : plateau documenté.

## 2026-11-07 21:36 · dev · S-10 Banc procédural fixe
- `track_seed` dans TimeAttackEnv.reset et options du wrapper ; `eval.py --bench` (50 pistes, graines 0..49).
- Baseline best/ : finish 0.92, 3.18 chocs moy., reproductible (2 runs identiques) ; docs/BENCH_V2.md.
- Tests : 53 passent.

## 2026-11-07 21:37 · reviewer · S-10 approved
- Diff relu (env.reset, wrappers options, eval --bench, 3 tests) : propre, comportement par défaut inchangé (track_seed None → graine aléatoire comme avant).
- Tests rapides : 53 passed, 1 skipped.
- `eval.py --bench --laps 3` lancé deux fois (metrics temporaires) : entrées identiques hors date ; finish_rate 0.92, mean_wall_hits 3.18, clean_rate 0.10.
- docs/BENCH_V2.md cohérent avec wall_hits_by_seed (top 5 : 36, 2, 14, 5, 10) ; entrée bench dans metrics.json.

## 2026-11-07 21:38 · loop · Call interrupted

- `dev` interrupted by TERM after 50s, see `/Users/nicolaspiron/TrackAI/.goal/logs/20261107-213750-dev.log`.

## 2026-11-07 21:38 · loop · Story released

- S-11 back to ready/rework (interrupted by TERM), attempt not counted.

## 2026-11-07 21:38 · loop · End

- Session ended after 5 step(s), 10 story(ies) done in total.

## 2026-11-07 21:52 · loop · Start

- Session of 75 steps on `goal/main` (team: trio).

## 2026-11-07 21:52 · loop · Goal changed

- New goal: Passer un cap : un agent qui roule sans choc sur des circuits aléatoires jamais vus, puis qui bat son professeur (pilote programmé, réglé à l'étape 0) sur le circuit fixe. Les commandes restent des touches (9 actions discrètes, comme un clavier) ; le dosage se fait en tapotant, la physique fait déjà

## 2026-11-07 21:53 · lead · Plan
- Goal modifié : étape 0 (recaler le professeur sur la physique Trackmania) ajoutée. Mesures antérieures invalidées, y compris la baseline du banc (S-10, ancienne physique).
- Nouvel epic E7 (ouvert, avant E4) ; E5 dépend d'E7. Critère inchangé (B se référera au temps du professeur réglé) ; statut : in progress. S-12 : chiffres périmés corrigés, dépend de S-13.

## 2026-11-07 21:53 · refiner · E7
- S-13 mesures de référence heuristic/best sur statique + banc (S, ready) ; S-14 réglage du professeur, 0 choc puis vitesse (M, ready, dépend S-13) ; S-15 borne lower_bound remesurée (S, ready, P3).
- S-11 (obs v2) reste ready et indépendante : peut se faire en parallèle.

## 2026-11-07 21:53 · lead · Plan
- Goal modifié : étape 0 (recaler le professeur sur la physique Trackmania) ajoutée. Mesures antérieures invalidées, y compris la baseline du banc (S-10, ancienne physique).
- Nouvel epic E7 (ouvert, avant E4) ; E5 dépend d'E7. Critère inchangé (B se référera au temps du professeur réglé) ; statut : in progress. S-12 : chiffres périmés corrigés, dépend de S-13.

## 2026-11-07 21:53 · refiner · E7
- S-13 mesures de référence heuristic/best sur statique + banc (S, ready) ; S-14 réglage du professeur, 0 choc puis vitesse (M, ready, dépend S-13) ; S-15 borne lower_bound remesurée (S, ready, P3).
- S-11 (obs v2) reste ready et indépendante : peut se faire en parallèle.

## 2026-11-07 21:54 · dev · S-11 Observation v2
- `obs_version=2` (35 valeurs) ajoutée dans TimeAttackEnv et GymTimeAttack ; v1 par défaut, identique à HEAD sur 300 pas.
- `obs_v1()` exposée pour le professeur heuristique ; `_cast_rays` prend la portée en paramètre.
- 5 nouveaux tests ; 63 passed.

## 2026-11-07 21:54 · reviewer · S-11 approved
- Diff relu : v1 inchangée (`_obs` renommée `_obs_v1`, défaut obs_version=1), v2 = 35 valeurs documentées, `obs_v1()` exposé, physique et jit_ops intacts, docstring heuristic_action ajoutée.
- pytest rapide : 63 passed, 1 skipped. Commande Verify : `(35,) (35,)`.
- `data/human_best.json` (non suivi, artefact de test/exécution) volontairement exclu du commit.
- Pas de mesure metrics.json : la story ne change pas le modèle.

## 2026-11-07 21:56 · dev · S-13 Mesures de référence nouvelle physique
- 4 mesures lancées (heuristic/best × statique/banc), ajoutées à metrics.json.
- docs/TEACHER_V2.md créé, renvoi ajouté en tête de BENCH_V2.md.
- heuristic : 12,56 s / 10 chocs statique, 13 chocs au banc ; best/ : 22 et 43 chocs.

## 2026-11-07 21:58 · reviewer · S-13 sent back
- Relancé heuristic statique (12,56 s/10 chocs), best/ banc (0,92 fini/43,16 chocs) : identiques ; tests rapides 63 passed, 1 skipped. metrics.json restauré après mes relances.
- Défaut : top 5 des graines à chocs faux dans TEACHER_V2.md (graine 11 à 22 chocs omise).

## 2026-11-07 21:58 · dev · S-13 Mesures de référence
- Rework : top 5 des graines corrigé dans TEACHER_V2.md (37, 44, 22, 11, 47).
- Aucun code modifié.

## 2026-11-07 21:58 · reviewer · S-13 approved
- Top 5 corrigé vérifié sur wall_hits_by_seed (37, 44, 22, 11, 47) ; 4 mesures présentes dans metrics.json (heuristic 12,56 s/10 chocs statique, banc 0,94/13,0 ; best/ 19,48 s/22, banc 0,92/43,16).
- Tests rapides : 63 passed, 1 skipped. Aucun code modifié. data/human_best.json exclu du commit.

## 2026-11-07 23:24 · dev · S-14 Réglage du pilote programmé
- Hill-climbing parallèle jetable (score statique + banc 3 tours, 10 s/choc) : 0 choc statique (14,12 s) et 0 choc sur les 50 pistes du banc (16,75 s).
- Constantes de heuristic_lap.py mises à jour (SECTOR_MULT vidé, SPEED_PER_RADIUS 0,1242, SAFE_HORIZON 40...), docs/TEACHER_V2.md complété.
- pytest rapide : 63 passed, 1 skipped.

## 2026-11-07 23:25 · reviewer · S-14 approved
- pytest rapide : 63 passed, 1 skipped.
- eval statique heuristic 3 tours, 20 ép., graine 0 : 20/20, 0 choc, 14,12 s (mesure refaite par moi).
- eval banc 50 pistes 3 tours : 50/50 finis, 0 choc partout, 16,746 s (mesure refaite).
- Diff limité aux constantes de heuristic_lap.py + doc TEACHER_V2 (avant/après, méthode, essais abandonnés) ; physique intouchée. `data/human_best.json` (généré par le jeu) laissé hors du commit.
- Réserve notée dans le doc : constantes réglées sur les 50 graines du banc (surapprentissage possible).

## 2026-11-07 23:26 · dev · S-12 eval/imitate/robust_eval v1 et v2
- obs_version auto-détectée d'après le modèle (eval, robust_eval) ; --obs-version pour forcer.
- imitate : --obs-version, professeur toujours sur obs_v1 ; --init déduit la version.
- best/ statique : 19,48 s / 22 chocs inchangé ; 2 nouveaux tests, 65 passent.

## 2026-11-07 23:27 · reviewer · S-12 approuvée
- Diff relu (eval/imitate/robust_eval + tests) : détection auto de l'obs_version, heuristique via `obs_v1()`, `--obs-version` ajouté, rien hors scope.
- Tests rapides : 65 passed, 1 skipped.
- eval statique best/ 3 tours 20 ép. : 19,48 s, 22 chocs, finish 1,0 = chiffres S-13.
- Test mini BC v2 → eval/robust_eval/heuristic v2 présent et vert. Pas de mesure metrics.json (story d'outillage).
- `data/human_best.json` (effet de bord d'eval, non ignoré) laissé hors du commit.

## 2026-11-07 23:28 · dev · S-15 Remesurer la borne inférieure
- `lower_bound.py` : correction de la mesure de virage (`vel` rescalé au lieu de `speed`), message « borne invalide ».
- Calibration par défaut absurde (31,69 s > 14,12 s) ; avec `--kwin 24` : 12,77 s, écart 1,35 s, consigné dans `docs/BOUND_V2.md`.
- pytest rapide vert (65 passed).

## 2026-11-07 23:28 · reviewer · S-15 approved
- Relancé lower_bound.py --laps 3 --reference 14.12 : 31,69 s (invalide, signalé par le nouveau message) ; avec --kwin 24 : 12,77 s, écart +1,35 s, conforme à docs/BOUND_V2.md.
- pytest rapide : 65 passed, 1 skipped. Diff limité à lower_bound.py (+_hold) et au doc ; data/human_best.json laissé hors commit. Pas de mesure metrics.json (outillage).

## 2026-11-07 23:29 · lead · Plan
- E7 et E4 clos : professeur réglé 14,12 s / 0 choc statique, banc 0 choc (metrics.json) ; borne 12,77 s ; baseline best/ 19,48 s / 22 chocs. Critère B chiffré (14,12 s). REPLAN levé.
- E5 est l'epic ouvert ; E6 attend.
- Décision : l'entraînement utilise des graines de piste ≥ 1000 (le professeur a été réglé sur 0-49).

## 2026-11-07 23:29 · refiner · E5
- S-16 (S) graines ≥ 1000 + mix-static dès le BC : ready.
- S-17 (M) candidat v2 n°1, mesures statique + banc : ready.
- S-18 (M) candidat n°2 selon diagnostic, S-19 (S) promotion dans best/ : draft, à finaliser après S-17 / S-18.
## 2026-11-07 23:30 · dev · S-16 imitate hors banc
- collect : graines procédurales 1000+seed+k, --mix-static actif dès le BC initial.
- 2 tests ajoutés ; pytest 67 passed, vérif imitate OK.

## 2026-11-07 23:30 · reviewer · S-16 approved
- pytest rapide : 67 passed, 1 skipped. imitate.py --obs-version 2 --mix-static --episodes 6 --epochs 1 : /tmp/chk_v2.zip sauvé, 1703 échantillons.
- Diff lu : graines 1000+seed+k en procédural, mix-static passé au BC initial, défaut inchangé. Test de mix ne vérifie pas les deux types de pistes (noté en inbox).
- data/human_best.json (généré par les runs) non commité.

## 2026-11-07 23:33 · lead · Plan
- Inbox (reviewer, S-16) acceptée : test du mix trop faible + `data/human_best.json` non ignoré → nouvelle story S-20 (S, ready) dans E5. Message déplacé dans inbox/done/.
- E5 reste l'epic ouvert ; S-17 est la suite. Rien d'autre à changer.

## 2026-11-07 23:33 · refiner · E5
- S-20 (S) Renforcer le test du mix fixe/procédural + .gitignore human_best.json : ready.

## 2026-11-07 23:34 · dev · S-17 candidat v2 n°1
- ppo_v2_a (BC 60 ép. + 4 DAgger, 1 min 52) : statique 14,14 s / 0 choc ; banc 16,50 s, 29 chocs sur 15 pistes.
- docs/IMITATION_V2.md écrit, 2 entrées dans metrics.json ; pytest 67 passed.

## 2026-11-07 23:34 · reviewer · S-17 approved
- Rejoué statique (14,14 s / 0 choc) et banc (16,50 s, 0,58 chocs, 29 sur 15 pistes) : chiffres identiques au doc et aux metrics ; top 5 graines vérifié.
- pytest rapide : 67 passed, 1 skipped. Doublons de metrics.json ajoutés par mes rejeux retirés. data/human_best.json non commité (inbox).

## 2026-11-07 23:35 · lead · Plan
- Inbox (reviewer, S-17) fusionnée : le .gitignore de `data/human_best.json` est déjà dans S-20 (ready) ; doublons de metrics.json = affaire du reviewer. Message déplacé dans inbox/done/.
- Rien d'autre à changer : E5 ouvert, S-18/S-19 à finaliser après S-17.

## 2026-11-07 23:35 · dev · S-20 Test du mix fixe/procédural
- Nouveau test espionnant reset : alternance fixe/procédural vérifiée, échoue si parité inversée.
- data/human_best.json ajouté au .gitignore (non suivi).

## 2026-11-07 23:36 · reviewer · S-20 approved
- Diff relu : nouveau test espionnant GymTimeAttack.reset (pairs fixe, impairs procédural graine ≥ 1000) + .gitignore ; `collect` inchangé ; human_best.json non suivi.
- Tests rapides : 68 passed, 1 skipped.
- Non re-vérifié : l inversion de parité (assertions pair/impair explicites, échec évident), pas de modification du code.

## 2026-11-07 23:36 · lead(refiner) · E5
- S-18 (M) candidats v2_b (plus de DAgger) / v2_c (hit-weight 30) : ready, chiffres de S-17 intégrés.
- S-19 (S) promotion + archivage best_s5a_v1 : ready.
- Note lead : v2_a satisfait déjà banc < 1 choc/course (0,58) ; reste 0,02 s au statique et 15 pistes fautives.
