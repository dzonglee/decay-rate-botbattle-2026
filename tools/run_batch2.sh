#!/usr/bin/env bash
# Batch 2 tuning experiments — second-tier CONFIG axes, two structural
# variants (endgame awareness, velocity smoothing), and mixed-field
# benchmarks vs opponent archetypes.
#
#   ./tools/run_batch2.sh                 # 30 games/experiment, 6 parallel
#   GAMES=50 PAR=8 ./tools/run_batch2.sh
#
# ~23 experiments; ~4.5h at defaults on an M-series Mac. Resumable: re-running
# skips experiments already present in results/batch2_results.txt.
# Run order: highest expected information first, so partial runs still pay.
set -u
cd "$(dirname "$0")/.."

GAMES="${GAMES:-30}"
PAR="${PAR:-6}"
PYTHON="${PYTHON:-python3}"
OUT=results/batch2_results.txt
mkdir -p results
touch "$OUT"

run() {
    local name="$1"; shift
    local hypothesis="$1"; shift
    if grep -q "^=== $name " "$OUT"; then
        echo "skip $name (already in $OUT)"
        return
    fi
    echo ""
    echo "=== $name — $hypothesis"
    local tmp
    tmp=$(mktemp)
    {
        echo "=== $name games=$GAMES — $hypothesis"
        "$PYTHON" tools/tournament.py --games "$GAMES" --parallel "$PAR" --tag "$name" "$@"
        echo ""
    } | tee "$tmp"
    # only mark the experiment done if it produced a result table, so
    # interrupted runs (machine asleep, WSL frozen) retry next invocation
    if grep -q "mean rank" "$tmp"; then
        cat "$tmp" >> "$OUT"
    else
        echo "[warn] $name produced no results; it will re-run next time"
    fi
    rm -f "$tmp"
}

B=bots/my_bot.py
V=bots/variants

# --- structural (highest value) ---
run endgame  "endgame awareness: protect rank in final 150 rounds when leading" \
    "4:$B" "4:$V/endgame.py"
run smooth   "EMA velocity smoothing (alpha .3) steadies LEAD_TICKS prediction" \
    "4:$B" "4:$V/smooth.py"

# --- mixed-field benchmarks (how the baseline fares vs archetypes; also
#     validates endgame in realistic company) ---
run mixed_baseline "benchmark: baseline vs archetype field (note my_bot mean rank)" \
    "4:$B" "2:bots/meta/aggressive.py" "2:bots/meta/hungryshy.py"
run mixed_endgame  "endgame vs baseline in archetype company (closer to leaderboard)" \
    "3:$B" "3:$V/endgame.py" "1:bots/meta/aggressive.py" "1:bots/meta/hungryshy.py"

# --- split axes ---
run splitoff       "is splitting worth anything at all? SPLIT_ENABLED=False" "4:$B" "4:$V/batch2/splitoff.py"
run splitclear7    "SPLIT_THREAT_CLEARANCE 9->7: lunge in busier fields"     "4:$B" "4:$V/batch2/splitclear7.py"
run splitclear12   "SPLIT_THREAT_CLEARANCE 9->12: only lunge when very safe" "4:$B" "4:$V/batch2/splitclear12.py"
run splitsafety125 "SPLIT_SAFETY_RATIO 1.35->1.25: lunge at thinner margins" "4:$B" "4:$V/batch2/splitsafety125.py"
run splitsafety15  "SPLIT_SAFETY_RATIO 1.35->1.5: bigger post-split margin"  "4:$B" "4:$V/batch2/splitsafety15.py"

# --- panic shaping ---
run panicmult25    "THREAT_PANIC_MULT 4->2.5: calmer close-quarters"         "4:$B" "4:$V/batch2/panicmult25.py"
run panicmult6     "THREAT_PANIC_MULT 4->6: harder flinch"                   "4:$B" "4:$V/batch2/panicmult6.py"

# --- falloff shaping ---
run preyfall10     "PREY_FALLOFF 1.5->1.0: chase distant prey more"          "4:$B" "4:$V/batch2/preyfall10.py"
run preyfall20     "PREY_FALLOFF 1.5->2.0: only close prey matters"          "4:$B" "4:$V/batch2/preyfall20.py"
run threatfall15   "THREAT_FALLOFF 2->1.5: fear reaches further"             "4:$B" "4:$V/batch2/threatfall15.py"
run threatfall25   "THREAT_FALLOFF 2->2.5: fear more local"                  "4:$B" "4:$V/batch2/threatfall25.py"

# --- food/wall/regroup/virus ---
run wfood16        "W_FOOD 1->1.6: food matters more"                        "4:$B" "4:$V/batch2/wfood16.py"
run wfood06        "W_FOOD 1->0.6: food matters less"                        "4:$B" "4:$V/batch2/wfood06.py"
run wwall14        "W_WALL 8->14: stronger corner aversion"                  "4:$B" "4:$V/batch2/wwall14.py"
run wwall4         "W_WALL 8->4: braver near walls"                          "4:$B" "4:$V/batch2/wwall4.py"
run wallmargin6    "WALL_MARGIN 4->6: keep further from walls"               "4:$B" "4:$V/batch2/wallmargin6.py"
run wallmargin25   "WALL_MARGIN 4->2.5: use more of the arena"               "4:$B" "4:$V/batch2/wallmargin25.py"
run regroup5       "W_REGROUP 2->5: recombine harder under threat"           "4:$B" "4:$V/batch2/regroup5.py"
run regroup05      "W_REGROUP 2->0.5: barely recombine"                      "4:$B" "4:$V/batch2/regroup05.py"
run virusavoid5    "VIRUS_AVOID_DIST 3.5->5: wider virus berth when big"     "4:$B" "4:$V/batch2/virusavoid5.py"

echo ""
echo "Batch 2 complete. Results in $OUT — commit and push:"
echo "  git add results && git commit -m 'batch2 results' && git push"
