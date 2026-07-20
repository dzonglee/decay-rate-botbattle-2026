#!/bin/bash
# feastgym-3 milestone/peak cron ENTRY. Idempotent; safe to run every ~10 min.
# Reads evolution_v2/state.json, archives peaks every 5 gens, fires a milestone
# battery every 30 gens (>= trigger, so a missed exact gen still fires on catch-up).
# Launches batteries DETACHED and returns immediately (never foreground-waits).
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
VENV=/Users/chrisli/Developer/competition/evolution-2/.venv
cd "$REPO"; source "$VENV/bin/activate"
mkdir -p mining

STATE=evolution_v2/state.json
[ -f "$STATE" ] || { echo "$(date -u +%FT%TZ) no state.json yet"; exit 0; }
[ -f feastgym3.base ] || { echo "$(date -u +%FT%TZ) no feastgym3.base (not launched)"; exit 0; }
BASE=$(awk -F= '/^BASE=/{print $2}' feastgym3.base)
G=$(python3 -c "import json;print(json.load(open('$STATE'))['generation'])")

LP=$(cat mining/gym3_last_peak 2>/dev/null || echo 0)
LM=$(cat mining/gym3_last_milestone 2>/dev/null || echo 0)

materialize () {  # $1 = output path -> writes current best genome as a real bot
  python3 - "$BASE" "$STATE" "$1" <<'PY'
import json, sys; sys.path.insert(0, "tools"); import evolve_v2 as E
from pathlib import Path
E.BASE_BOT = Path("bots") / f"{sys.argv[1]}.py"
best = json.load(open(sys.argv[2]))["best"]
E.write_variant(best, Path(sys.argv[3]))
PY
}

# --- PEAK every 5 gens (>=) ---
if [ "$G" -ge $((LP + 5)) ]; then
  materialize "bots/peak_g${G}.py"
  echo "$G" > mining/gym3_last_peak
  echo "$(date -u +%FT%TZ) [peak] archived bots/peak_g${G}.py (best of gen $G)"
fi

# --- MILESTONE every 30 gens (>=) ---
if [ "$G" -ge $((LM + 30)) ]; then
  ELITE="bots/gym3_elite_g${G}.py"
  materialize "$ELITE"
  echo "$G" > mining/gym3_last_milestone
  rm -f "mining/gym3_g${G}.done"
  # milestones judged vs seated elite_g30 (the shipped .12 champion); i19 is now an ancestor
  nohup bash tools/gym3_battery.sh elite_g30 "$G" "$ELITE" \
    > "mining/gym3_g${G}_battery.driver.log" 2>&1 &
  echo "$(date -u +%FT%TZ) [milestone] gen $G >= $((LM+30)); launched battery PID $! (detached)"
fi
