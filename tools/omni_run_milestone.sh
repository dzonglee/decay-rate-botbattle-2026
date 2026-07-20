#!/bin/bash
# OMNI milestone cron entry (per machine). Idempotent, resume-GUARANTEED.
# Fires every 30 gens: current elite vs seated elite_g30 in the CORRECTED room
# (2 elite + 2 champion + 2 evolution top-performers + 2 dumb feeders), mirrored,
# ban-void. Writes OMNI-evo/milestones/gen_NNN.md and updates the marker. If it
# flags (>+4) it leaves a FLAGGED note for the operator to run the n=100 confirm.
# Safe to run every ~15 min. macOS-compatible (no flock).
set -uo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
OMNI=/Users/chrisli/Developer/competition/OMNI-evo
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/simulation ]; then
  VENV=/Users/chrisli/Developer/competition/evolution-2/.venv     # laptop (omni-A)
else
  VENV=$REPO/.venv                                                # studio (omni-B)
fi
cd "$REPO" || exit 0
source "$VENV/bin/activate"
CHAMP=$(basename "$(cat "$REPO/config/current_development_champion.txt" 2>/dev/null)" .py)   # pointer (label only; challenge script reads the path itself)

# every-5-gens PEAK archive folded in (standalone crontab write hangs on macOS TCC)
bash "$REPO/tools/omni_peak.sh" >> "$OMNI/peak_cron.log" 2>&1 || true

LOCK="$OMNI/.milestone.lock"
mkdir "$LOCK" 2>/dev/null || exit 0            # atomic lock; another run in progress -> bail
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

STATE=evolution_v2/state.json
[ -f "$STATE" ] || exit 0
G=$(python3 -c "import json;print(json.load(open('$STATE'))['generation'])" 2>/dev/null) || exit 0
LM=$(cat mining/omni_last_milestone 2>/dev/null || echo 0)
[ "$G" -ge $((LM + 30)) ] || exit 0            # not due yet
[ -f "$OMNI/omni_resume.cmd" ] || { echo "$(date -u +%FT%TZ) no omni_resume.cmd"; exit 0; }

echo "$(date -u +%FT%TZ) [milestone] gen $G due (last=$LM) -> running" >> "$OMNI/milestone_cron.log"

# resume-GUARANTEED: on ANY exit, if no evolve is running, relaunch it
resume() {
  rmdir "$LOCK" 2>/dev/null   # clear lock FIRST so the supervisor may resume
  if pgrep -f 'omni_supervisor.sh' >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) [milestone] deferring resume to supervisor (foreground band)" >> "$OMNI/milestone_cron.log"
    return  # supervisor resumes within 60s from an interactive-session coalition (full speed)
  fi
  # FALLBACK only (no supervisor alive): cron-spawned resume — may land in the
  # macOS background band (E-cores only, ~3x slower). Keep a supervisor running.
  if ! pgrep -f 'evolve_v2.py' >/dev/null 2>&1; then
    nohup bash "$OMNI/omni_resume.cmd" >> "$OMNI/evolution_run.log" 2>&1 &
    echo "$!" > "$OMNI/omni_evo.pid"
    echo "$(date -u +%FT%TZ) [milestone] resumed evolution PID $(cat "$OMNI/omni_evo.pid") (FALLBACK path, may be E-core clamped)" >> "$OMNI/milestone_cron.log"
  fi
}
trap resume EXIT

# materialize elite + 2 top performers from the current population
python3 - <<'PY'
import sys; sys.path.insert(0,"tools")
import json; from pathlib import Path; import evolve_v2 as E
import re as _re
_cmd=open("/Users/chrisli/Developer/competition/OMNI-evo/omni_resume.cmd").read()
E.BASE_BOT=Path(_re.search(r"--base (\S+)", _cmd).group(1))   # machine-agnostic: matches the running body
pop=json.load(open("evolution_v2/state.json"))["population"]
E.write_variant(pop[0], Path("bots/omniMS_elite.py"))
E.write_variant(pop[1], Path("bots/omniA_top1.py"))
E.write_variant(pop[2], Path("bots/omniA_top2.py"))
PY

# PAUSE evolution (clean)
PID=$(cat "$OMNI/omni_evo.pid" 2>/dev/null || echo "")
[ -n "$PID" ] && kill "$PID" 2>/dev/null
sleep 2; pkill -f 'simulation --headless' 2>/dev/null; sleep 2

# run the milestone battery (evolution is paused -> use the cores; parallel 8 halves the pause)
rm -f "mining/cc_omniMS${G}.done"
bash tools/omni_gym_compare.sh bots/omniMS_elite.py omniMS${G} 40 8 || true   # GYM COMPARISON (Chris 2026-07-10: non-adversarial, live-aligned)

# record result + doc + marker — POOLED delta only (never a half's)
REP="mining/gc_omniMS${G}_report.txt"
DELTA=$(grep -m1 "GYM COMPARISON DELTA" "$REP" 2>/dev/null | grep -oE '[+-][0-9.]+' | head -1 || echo NA)
FLAG=$(awk -v d="$DELTA" 'BEGIN{ if (d+0 > 4.0) print "FLAGGED" }')
{
  echo "[$(cat "$REPO/config/run_identity.txt" 2>/dev/null || echo RUN) / gen $G]"
  echo "# MILESTONE (n=40 SCREEN) — gen $G — elite vs $CHAMP (config champion) — flag>+4 escalates to n>=100 confirm"
  echo "ROOM (gym comparison, both sides): 3x focal + anchor($CHAMP) + v3 + rotating bench from config/gym_room.txt + 2 fodder"
  echo "test doctrine changed: adversarial 2+2+2+2 courtroom -> GYM-ENVIRONMENT COMPARISON (absolute mass), on Chris's order 2026-07-10"
  echo "MASS DELTA = ${DELTA}  ${FLAG:+*** $FLAG: run n=100 confirmation before promoting ***}"
  echo ""
  cat "$REP" 2>/dev/null
} > "$OMNI/milestones/gen_$(printf %03d "$G").md"
echo "$G" > mining/omni_last_milestone
echo "$(date -u +%FT%TZ) [milestone] gen $G done delta=$DELTA $FLAG" >> "$OMNI/milestone_cron.log"
# resume + unlock handled by trap
