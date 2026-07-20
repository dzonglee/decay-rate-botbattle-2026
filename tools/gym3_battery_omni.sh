#!/bin/bash
# OMNI milestone battery: elite vs seated champion, mirrored 2x(n/2), ban-void.
# Champion is a PARAM ($1) — never hardcoded. ROOM = HALL OF ANCESTORS (fixed,
# known, non-sibling opponents): a courtroom, not the breeding room. No dumb seats,
# no converging relatives. Gene readout = FULL organ table (reading an omni elite
# is about WHICH ORGANS FIRED).
# Args: $1=champion stem  $2=GEN/tag  $3=ELITE_BOT_PATH  [$4=total N=40]  [$5=parallel]
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/simulation ]; then VENV=/Users/chrisli/Developer/competition/evolution-2/.venv; else VENV=/Users/chrisli/Developer/competition/botbattle/.venv; fi
cd "$REPO"; source "$VENV/bin/activate"

BASE="$1"; GEN="$2"; ELITE="$3"
MILESTONE_N=${4:-40}; HALF=$((MILESTONE_N/2)); PAR=${5:-4}
PRES=".agario_tourney/milestone_g${GEN}"
REPORT="mining/gym3_g${GEN}_report.txt"
# HALL OF ANCESTORS — fixed known opponents (historical floors), NOT dumb bots, NOT siblings.
PRESSURE="1:bots/split_feaster_v3.py 1:bots/split_feaster.py 1:bots/elite_g30.py 1:bots/gen51_feast.py"
LABELS="v3,split_feaster,elite_g30,gen51_feast"
rm -rf "$PRES"; mkdir -p "$PRES/A" "$PRES/B" mining

preserve () { for w in .agario_tourney/ws*; do b=$(basename "$w"); mkdir -p "$PRES/$1/$b/output"
    cp -p "$w/output/results.json" "$w/output/game.json" "$PRES/$1/$b/output/" 2>/dev/null || true; done; }

# Half A: elite @ 0-1 ; champion @ 2-3
rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" \
  2:"$ELITE" 2:bots/$BASE.py $PRESSURE > "mining/gym3_g${GEN}_A.log" 2>&1
preserve A
# Half B: champion @ 0-1 ; elite @ 2-3  (mirror)
rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" \
  2:bots/$BASE.py 2:"$ELITE" $PRESSURE > "mining/gym3_g${GEN}_B.log" 2>&1
preserve B

{
  echo "=== OMNI MILESTONE g${GEN}  (elite vs champion=$BASE, HALL-OF-ANCESTORS room, mirrored 2x${HALF}, --parallel ${PAR}, ban-void) ==="
  echo "elite bot: $ELITE  |  room fill: $LABELS  (fixed floors, no dumb/no siblings)"
  python3 tools/gym3_batteryparse.py elite champion \
    "elite,elite,champion,champion,${LABELS}::$PRES/A/ws*" \
    "champion,champion,elite,elite,${LABELS}::$PRES/B/ws*"
  echo
  echo "=== FULL ORGAN READOUT (elite: 16 organs + cycle + W_PREY/W_THREAT) ==="
  python3 - "$ELITE" <<'PY'
import ast, re, sys
cfg = ast.literal_eval("{" + re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", open(sys.argv[1]).read(), re.S).group(1) + "\n}")
SW={"CORNER_SKIP_ON","STALL_KICK_ON","AGGRO_ON","SPLIT_CYCLE_ON"}
def mark(g,v):
    if v is None: return "  (absent)"
    if g in SW: return "  <ON>" if v>0.5 else "  off"
    return ""
print("  -- doctrine --")
for g in ["W_PREY","W_THREAT","SAFETY_RATIO","W_VIRUS_FEAST","FEAST_MIN_MASS"]:
    print(f"    {g:20}= {cfg.get(g)}")
print("  -- cycle --")
for g in ["SPLIT_CYCLE_ON","CYCLE_MIN_MASS","CYCLE_TARGET_BLOBS","CYCLE_THREAT_CLEAR"]:
    v=cfg.get(g); print(f"    {g:20}= {v}{mark(g,v)}")
print("  -- 16 organs --")
for g in ["CORNER_SKIP_ON","THREAT_SIZE_GATE","W_VIRUS_SHIELD","W_FRAG_HUNT","W_PIECE_GUARD",
          "W_MERGE_IDLE","W_CENTER","FOOD_HUNGER_EXP","STALL_KICK_ON","W_ENVELOPE_SCALE",
          "AGGRO_ON","ENDGAME_START","ENDGAME_FEAR_MULT","CORNER_TUCK","STALL_DIST","W_STALL_KICK"]:
    v=cfg.get(g); print(f"    {g:20}= {v}{mark(g,v)}")
PY
} > "$REPORT" 2>&1
echo DONE > "mining/gym3_g${GEN}.done"
echo "[milestone g${GEN}] report -> $REPORT"
