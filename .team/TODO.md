# Todo

> Tenue par le planificateur. Le worker et le reviewer ne changent que le statut et le compteur d'essais.
> Statuts : `[ ]` à faire · `[~]` en cours · `[?]` à relire · `[-]` à reprendre · `[x]` validée · `[!]` bloquée
> Le worker prend d'abord une tâche `[-]`, sinon la première `[ ]` dont les dépendances sont validées.

## En cours / à faire

- [ ] **T7** · Banc physique `scripts/physics_check.py` : mouvement longitudinal · P1
  - but : script headless (SDL_VIDEODRIVER=dummy) qui crée l'env sur une piste fixe (non procédurale, ou graine fixe) et mesure : vitesse terminale en pleine accélération (valeur vs MAX_SPEED), temps 0→90 % de vitesse, distance de freinage depuis vitesse max, décélération en roue libre ; affiche un JSON et ajoute une entrée `physics_check` à `metrics.json` (`--metrics` pour changer)
  - fini quand : commande lancée 2× donne le même JSON ; chiffres commentés dans le journal (en m/s-équivalents px/frame et px/s) ; test pytest `tests/test_physics.py` minimal
  - dépend de : T2
  - essais : 0

- [ ] **T8** · Banc physique : virage et adhérence · P1
  - but : étendre le script : rayon de virage à braquage plein à vitesses 5/15/22, angle de dérive (heading vs vel) en régime établi, temps de réaction du volant (STEER_SPEED), absence de glissement irréaliste ; vérifie aussi que actions hors bornes (steer=5, accel=-1) ne cassent pas la physique
  - fini quand : valeurs dans le JSON + journal ; chaque scénario a un seuil « réaliste » écrit dans le script et un statut pass/fail
  - dépend de : T7
  - essais : 0

- [ ] **T9** · Banc physique : murs, boost, checkpoints, arrivée · P1
  - but : scénarios : voiture lancée perpendiculairement/en biais contre un mur (reste dans la piste, jamais de téléportation, `speed` cohérent avec `|vel|` après choc), traversée de boost (vitesse plafonnée), checkpoints dans l'ordre et pas de saut, finish uniquement après tous les checkpoints, départ à vitesse 0 ; reproductibilité à graine égale
  - fini quand : scénarios dans le JSON avec pass/fail ; les échecs sont listés dans le journal comme « écarts de réalisme » numérotés
  - dépend de : T7
  - essais : 0

- [ ] **T10** · Triage des écarts de réalisme · P2
  - but : à partir des résultats T7-T9, lister dans `docs/PHYSICS.md` chaque écart (confirmé/infirmé) avec décision : corriger (ex. vitesse max inatteignable, désynchro speed/vel, marche arrière, dt) ou assumer comme choix arcade. Pas de changement de code
  - fini quand : `docs/PHYSICS.md` créé, chaque écart a mesure + décision ; le planner convertira les « corriger » en tâches
  - dépend de : T8, T9
  - essais : 0

- [ ] **T3** · Mesurer la référence random (reporté, utile comme test de bon sens) · P3
  - but : entrée `random` dans `metrics.json`
  - fini quand : chiffres dans `metrics.json` et journal
  - dépend de : T2
  - essais : 0

> Reportées (plan RL en pause) : T4 smoke PPO, T5 éval du modèle, T6 PPO 50k. À reprendre après correction de la physique, car changer la physique invalide les entraînements.

## Terminées

