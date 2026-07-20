#!/bin/bash
# FOCUS WATCHER (persistent; the ONLY run manager for the focused search).
# Every 20 gens: PAUSE evolution (no auto-resume — review-gated), auto-report,
# write MILESTONE_READY marker. Claude's wake-monitor sees the marker and the
# operator does the deeds, then resumes via omni_resume.cmd + deletes the marker.
# Usage (loop-daemon): while :; do bash tools/focus_watch.sh; sleep 60; done
set -uo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
OMNI_DIR=$(ls -d /Users/chrisli/Developer/competition/OMNI-evo 2>/dev/null || echo "$HOME/Developer/competition/OMNI-evo")
cd "$REPO" || exit 0
READY="$REPO/mining/MILESTONE_READY"
[ -f "$READY" ] && exit 0                       # already paused, awaiting review
STATE=evolution_v2/state.json; [ -f "$STATE" ] || exit 0
G=$(python3 -c "import json;print(json.load(open('$STATE'))['generation'])" 2>/dev/null) || exit 0
LAST=$(cat mining/focus_last_milestone 2>/dev/null || echo 0)
[ "$G" -ge $((LAST + 20)) ] || exit 0

# PAUSE (no resume until operator review)
kill $(pgrep -f 'evolve_v2.py --run-id') 2>/dev/null; sleep 3
pkill -f 'simulation --headless' 2>/dev/null; sleep 2
echo "$(date -u +%FT%TZ) [focus] gen $G milestone — PAUSED for review" >> mining/focus_watch.log

# auto-report (fitness + gene distributions + elite-vs-chassis battery)
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/python3 ]; then
  PY=/Users/chrisli/Developer/competition/evolution-2/.venv/bin/python3; PAR=8
else
  source "$REPO/.venv/bin/activate"; PY=python3; PAR=8
fi
$PY tools/focus_report.py > "mining/focus_M$(printf %03d "$G")_report.md" 2>&1
echo "$G" > mining/focus_last_milestone
echo "gen=$G report=mining/focus_M$(printf %03d "$G")_report.md" > "$READY"
