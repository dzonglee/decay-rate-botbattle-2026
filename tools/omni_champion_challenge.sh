#!/bin/bash
# TEST A — CHAMPION CHALLENGE. Candidate vs the CONFIG-pointer champion, mirrored,
# fixed hall-of-ancestors fillers (no dumb, no siblings, no dynamic fillers).
# Self-verifying: prints the full resolved config + hashes BEFORE simulating.
# Args: $1=candidate_path  $2=tag  [$3=N total, default 40]  [$4=parallel, default 4]
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/simulation ]; then VENV=/Users/chrisli/Developer/competition/evolution-2/.venv; else VENV=$REPO/.venv; fi
cd "$REPO"; source "$VENV/bin/activate"
SCRIPT_VER="omni_cc_v1 $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo nogit)"

CAND="$1"; TAG="$2"; N=${3:-40}; HALF=$((N/2)); PAR=${4:-4}
CHAMP=$(cat "$REPO/config/current_development_champion.txt")          # single source of truth
# ROOM comes from the config file — NEVER hardcode seats here. Any change to that
# file requires an acknowledgment line in the next report (see file header).
FILLERS=($(grep -v '^#' "$REPO/config/milestone_room.txt"))
CHAL=".agario_tourney/challenge_${TAG}"; REPORT="mining/cc_${TAG}_report.txt"
rm -rf "$CHAL"; mkdir -p "$CHAL/A" "$CHAL/B" mining
h(){ shasum -a 256 "$1" 2>/dev/null | cut -c1-16; }

# ---------- SELF-VERIFYING CONFIG HEADER (printed before any simulation) ----------
{
echo "[$(cat "$REPO/config/run_identity.txt" 2>/dev/null || echo RUN) / candidate=$(basename "$CAND" .py)]"
echo "================ CHAMPION CHALLENGE — CONFIG VERIFICATION ================"
echo "script_version : $SCRIPT_VER"
echo "champion path  : $CHAMP   sha256=$(h "$CHAMP")"
echo "candidate path : $CAND   sha256=$(h "$CAND")"
echo "seat map (mirrored):"
echo "  half A -> slot0,1=CANDIDATE  slot2,3=CHAMPION  slot4-7=FILLERS"
echo "  half B -> slot0,1=CHAMPION   slot2,3=CANDIDATE slot4-7=FILLERS"
echo "room config    : config/milestone_room.txt (order of record in its header comments)"
grep '^#' "$REPO/config/milestone_room.txt" | sed 's/^/    /'
echo "fillers (seats 4-7, from room config):"
for f in "${FILLERS[@]}"; do echo "  $f  sha256=$(h "$f")"; done
echo "games          : $N total ($HALF per mirror half)  parallel=$PAR"
echo "seeds          : engine-managed per match (tournament.py has no external seed control; both machines use the same engine build 2026.1.12)"
echo "scoring        : final blob mass (sum radius^2); win = event_player_won only"
echo "void rule      : any match with result_type != SUCCESS is voided (LAW 2); reported separately, excluded from metrics"
echo "timeout rule   : result_type containing TIMEOUT counted as timeout-typed void"
echo "promotion gate : candidate mean_mass - champion mean_mass >= +2.5 AND CI lower bound > 0, at n>=100"
echo "=========================================================================="
} | tee "$REPORT"

preserve(){ for w in .agario_tourney/ws*; do b=$(basename "$w"); mkdir -p "$CHAL/$1/$b/output"
    cp -p "$w/output/results.json" "$w/output/game.json" "$CHAL/$1/$b/output/" 2>/dev/null || true; done; }
FILL_SPEC=""; for f in "${FILLERS[@]}"; do FILL_SPEC="$FILL_SPEC 1:$f"; done

rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" 2:"$CAND" 2:"$CHAMP" $FILL_SPEC > "mining/cc_${TAG}_A.log" 2>&1
preserve A
rm -rf .agario_tourney/ws*
python3 tools/tournament.py --games "$HALF" --parallel "$PAR" 2:"$CHAMP" 2:"$CAND" $FILL_SPEC > "mining/cc_${TAG}_B.log" 2>&1
preserve B

{
  echo ""; echo "================ RESULTS (champion=$(basename "$CHAMP" .py)  candidate=$(basename "$CAND" .py)) ================"
  python3 tools/omni_cc_parse.py "$CHAL"
  echo ""; echo "================ FULL CANDIDATE GENOTYPE ================"
  python3 - "$CAND" <<'PY'
import ast, re, sys
cfg = ast.literal_eval("{" + re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", open(sys.argv[1]).read(), re.S).group(1) + "\n}")
SW={"CORNER_SKIP_ON","STALL_KICK_ON","AGGRO_ON","SPLIT_CYCLE_ON","VETO_ENABLED","LOCK_ENABLED","SPLIT_ENABLED","SPLIT_RUN_ENABLED"}
def m(g,v): return ("" if g not in SW else ("  <ACTIVE>" if (v if isinstance(v,(int,float)) else 0)>0.5 else "  off"))
GROUPS={
 "DOCTRINE":["W_PREY","W_THREAT","W_FOOD","W_VIRUS_FEAST","SAFETY_RATIO","FEAST_MIN_MASS","FEAST_SLOT_SAT","THREAT_IGNORE_DIST"],
 "CYCLE":["SPLIT_CYCLE_ON","CYCLE_MIN_MASS","CYCLE_TARGET_BLOBS","CYCLE_THREAT_CLEAR","SPLIT_ENABLED","SPLIT_MAX_MASS"],
 "16 ORGANS":["CORNER_SKIP_ON","CORNER_TUCK","CORNER_MARGIN","THREAT_SIZE_GATE","W_VIRUS_SHIELD","SHIELD_MAX_MASS",
   "W_FRAG_HUNT","FRAG_HUNT_MIN_BLOBS","W_PIECE_GUARD","PIECE_GUARD_TICKS","W_MERGE_IDLE","W_CENTER","FOOD_HUNGER_EXP",
   "STALL_KICK_ON","STALL_TICKS","STALL_DIST","W_STALL_KICK","ENDGAME_START","ENDGAME_FEAR_MULT","W_ENVELOPE_SCALE","AGGRO_ON","W_AGGRO"],
}
for grp,keys in GROUPS.items():
    print(f"  -- {grp} --")
    for k in keys:
        if k in cfg: print(f"    {k:20}= {cfg[k]}{m(k,cfg[k])}")
print("  (note: 'active' = gene past its neutral default; runtime per-tick organ-firing instrumentation is not wired — genotype only)")
PY
} >> "$REPORT" 2>&1
echo DONE > "mining/cc_${TAG}.done"
echo "[champion-challenge $TAG] report -> $REPORT"
