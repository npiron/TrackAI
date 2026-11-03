#!/usr/bin/env bash
# Boucle de l'équipe d'agents TrackAI : planner -> (worker -> reviewer) x N
# Usage : ./team_loop.sh [iterations=10]   |   arrêt propre : touch .team/STOP
set -uo pipefail

cd "$(dirname "$0")"
MAX_ITER="${1:-10}"
PLAN_EVERY="${PLAN_EVERY:-5}"     # replanifier toutes les N itérations
MAX_IDLE="${MAX_IDLE:-3}"         # itérations sans tâche validée avant arrêt
TEAM=.team
LOGS="$TEAM/logs"
mkdir -p "$LOGS" "$TEAM/inbox/traite"

ALLOWED=(Read Write Edit Glob Grep Bash)
DENIED=("Bash(git push:*)" "Bash(git reset --hard:*)" "Bash(git rebase:*)" "Bash(rm -rf:*)" "Bash(sudo:*)")

ts() { date '+%Y-%m-%d %H:%M'; }
log() { echo "[$(ts)] $*"; }
journal() { printf '\n## %s · boucle · %s\n\n- %s\n' "$(ts)" "$1" "$2" >> "$TEAM/JOURNAL.md"; }

run_agent() {  # $1=agent  $2=consigne
  local agent="$1" out="$LOGS/$(date +%Y%m%d-%H%M%S)-$1.log"
  log "→ $agent (log : $out)"
  # Utiliser le login claude.ai (abonnement), pas une clé API du shell
  env -u ANTHROPIC_API_KEY claude -p "$2" \
    --agent "$agent" \
    --permission-mode acceptEdits \
    --allowedTools "${ALLOWED[@]}" \
    --disallowedTools "${DENIED[@]}" \
    < /dev/null > "$out" 2>&1
  local rc=$?
  tail -n 4 "$out" | sed 's/^/    /'
  if [ $rc -ne 0 ]; then
    log "❌ $agent a échoué (code $rc) : arrêt de la boucle."
    journal "Arrêt sur erreur" "\`$agent\` a échoué (code $rc), voir \`$out\`."
    exit $rc
  fi
}

count_done() { grep -c '^- \[x\]' "$TEAM/TODO.md" 2>/dev/null || true; }

# Travailler sur une branche dédiée
branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != team/* ]]; then
  echo "Il faut être sur une branche team/* (actuelle : $branch). Ex. : git switch team/main" >&2
  exit 1
fi

rm -f "$TEAM/STOP"
journal "Démarrage" "Session de $MAX_ITER itérations sur \`$branch\`."
idle=0

for ((i = 1; i <= MAX_ITER; i++)); do
  log "===== Itération $i/$MAX_ITER ====="

  if (( i == 1 || (i - 1) % PLAN_EVERY == 0 )) || [ -f "$TEAM/REPLAN" ]; then
    run_agent planner "Fais un passage de planification complet selon tes instructions."
    git add "$TEAM" && git commit -qm "chore(team): replanification" -m "Co-Authored-By: Claude <noreply@anthropic.com>" 2>/dev/null || true
  fi
  [ -f "$TEAM/STOP" ] && break

  before="$(count_done)"
  run_agent worker "Réalise une itération selon tes instructions."
  [ -f "$TEAM/STOP" ] && break

  if grep -q '^- \[?\]' "$TEAM/TODO.md"; then
    run_agent reviewer "Relis et teste la tâche en attente selon tes instructions."
  else
    log "Aucune tâche à relire."
  fi

  after="$(count_done)"
  if (( after > before )); then idle=0; else idle=$((idle + 1)); fi
  if (( idle >= MAX_IDLE )); then
    log "$idle itérations sans tâche validée : on replanifie."
    touch "$TEAM/REPLAN"
  fi
  if (( idle >= MAX_IDLE * 2 )); then
    journal "Arrêt" "$idle itérations sans progrès, intervention humaine nécessaire."
    log "Arrêt : pas de progrès."
    break
  fi
  [ -f "$TEAM/STOP" ] && break
done

rm -f "$TEAM/STOP"
journal "Fin" "Session terminée après $((i > MAX_ITER ? MAX_ITER : i)) itération(s), $(count_done) tâche(s) validée(s) au total."
git add "$TEAM" && git commit -qm "chore(team): journal de fin de session" -m "Co-Authored-By: Claude <noreply@anthropic.com>" 2>/dev/null || true
log "Terminé. Voir $TEAM/JOURNAL.md"
