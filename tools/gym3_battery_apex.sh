#!/bin/bash
# feastgym-3 milestone battery: elite vs seated champion, mirrored 2x(n/2), LAW 1+2.
# Args: $1=BASE(champion bot stem)  $2=GEN  $3=ELITE_BOT_PATH  [$4=total N, default 40]
# Runs detached-safe (no foreground wait); writes a full report file at the end.
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
VENV=/Users/chrisli/Developer/competition/evolution-2/.venv
cd "$REPO"; source "$VENV/bin/activate"

BASE="$1"; GEN="$2"; ELITE="$3"
MILESTONE_N=${4:-40}                # total games = 2 x (MILESTONE_N/2); gated trial passes 20 -> 2x10
HALF=$((MILESTONE_N/2))
PAR=${5:-2}                          # --parallel; confirmation passes 4 to fit around the live evolution
PRES=".agario_tourney/milestone_g${GEN}"
REPORT="mining/gym3_g${GEN}_report.txt"
PRESSURE="1:bots/mimic_t1.py 1:bots/mimic_t15.py 1:bots/mimic_t1b.py 1:bots/mimic_t15b.py"
rm -rf "$PRES"; mkdir -p "$PRES/A" "$PRES/B" mining

preserve () {  # copy only output/ (results.json+game.json); never the FIFOs
  for w in .agario_tourney/ws*; do b=$(basename "$w"); mkdir -p "$PRES/$1/$b/output"
    cp -p "$w/output/results.json" "$w/output/game.json" "$PRES/$1/$b/output/" 2>/dev/null || true
  done
}

# Half A: elite @ slots 0-1 ; champion @ 2-3
rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" \
  2:"$ELITE" 2:bots/$BASE.py $PRESSURE > "mining/gym3_g${GEN}_A.log" 2>&1
preserve A
# Half B: champion @ slots 0-1 ; elite @ 2-3   (mirror)
rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" \
  2:bots/$BASE.py 2:"$ELITE" $PRESSURE > "mining/gym3_g${GEN}_B.log" 2>&1
preserve B

{
  echo "=== feastgym-3 MILESTONE g${GEN}  (elite vs champion=$BASE, mirrored 2x${HALF}, --parallel ${PAR}, ban-void) ==="
  echo "elite bot: $ELITE"
  python3 tools/gym3_batteryparse.py elite champion \
    "elite,elite,champion,champion,mimic_t1,mimic_t15,mimic_t1b,mimic_t15b::$PRES/A/ws*" \
    "champion,champion,elite,elite,mimic_t1,mimic_t15,mimic_t1b,mimic_t15b::$PRES/B/ws*"
  echo
  echo "=== GENE READOUT (elite: all feast genes + W_THREAT) ==="
  python3 - "$ELITE" <<'PY'
import ast, re, sys
src = open(sys.argv[1]).read()
cfg = ast.literal_eval("{" + re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S).group(1) + "\n}")
for g in ["FEAST_MIN_MASS","FEAST_SLOT_SAT","W_VIRUS_FEAST","VIRUS_FEAST_CLEAR","VIRUS_AVOID_DIST","W_THREAT"]:
    print(f"    {g:18} = {cfg.get(g)}")
PY
} > "$REPORT" 2>&1
echo DONE > "mining/gym3_g${GEN}.done"
echo "[milestone g${GEN}] report -> $REPORT"
