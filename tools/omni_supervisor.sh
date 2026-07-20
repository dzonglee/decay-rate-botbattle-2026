#!/bin/bash
# OMNI evolution SUPERVISOR — the ONLY resumer of evolve_v2.
# MUST be launched from an interactive session (Claude Code Bash / terminal),
# NEVER from cron: cron-spawned trees get clamped to the macOS background band
# (E-cores only, ~3x slower). The milestone cron pauses evolution and holds
# .milestone.lock; this loop resumes within 60s of the lock clearing.
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
OMNI=$(dirname "$REPO")/OMNI-evo
[ -d "$OMNI" ] || OMNI="$HOME/Developer/competition/OMNI-evo"
while :; do
  if ! pgrep -f 'evolve_v2.py' >/dev/null 2>&1 && [ ! -d "$OMNI/.milestone.lock" ]; then
    cd "$REPO" || exit 1
    nohup bash "$OMNI/omni_resume.cmd" >> "$OMNI/evolution_run.log" 2>&1 &
    echo "$!" > "$OMNI/omni_evo.pid"
    echo "$(date -u +%FT%TZ) [supervisor] resumed evolution PID $(cat "$OMNI/omni_evo.pid")" >> "$OMNI/milestone_cron.log"
  fi
  sleep 60
done
