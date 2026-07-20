#!/usr/bin/env bash
# Batch 1 tuning experiments — designed for macOS (any Unix with agario-kit works).
#
#   ./tools/run_batch1.sh                 # 30 games/experiment, 6 parallel
#   GAMES=50 PAR=8 ./tools/run_batch1.sh  # more statistical power / more cores
#
# Results append to results/batch1_results.txt (safe to re-run; each experiment
# is skipped if its header is already in the file, so you can resume).
# Progress prints to the terminal only; the file gets clean result tables.
set -u
cd "$(dirname "$0")/.."

GAMES="${GAMES:-30}"
PAR="${PAR:-6}"
PYTHON="${PYTHON:-python3}"
OUT=results/batch1_results.txt
mkdir -p results
touch "$OUT"

run() {
    local name="$1" variant="$2" hypothesis="$3"
    if grep -q "^=== $name " "$OUT"; then
        echo "skip $name (already in $OUT)"
        return
    fi
    echo ""
    echo "=== $name — $hypothesis"
    local tmp
    tmp=$(mktemp)
    {
        echo "=== $name ($variant) games=$GAMES — $hypothesis"
        "$PYTHON" tools/tournament.py --games "$GAMES" --parallel "$PAR" --tag "$name" \
            "4:bots/my_bot.py" "4:$variant"
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

# Ordered by expected information value.
run preyhunt20  bots/variants/batch1/preyhunt20.py  "W_PREY 14->20: hunt harder (greed side untested on this axis)"
run threat60    bots/variants/batch1/threat60.py    "W_THREAT 90->60: less flight inside ignore radius"
run safety105   bots/variants/batch1/safety105.py   "SAFETY_RATIO 1.12->1.05: dare closer size margins"
run blobs2      bots/variants/batch1/blobs2.py      "SPLIT_MAX_BLOBS 4->2: stay compact, split only from whole"
run lead8       bots/variants/batch1/lead8.py       "LEAD_TICKS 4->8: longer velocity extrapolation"
run foodfall07  bots/variants/batch1/foodfall07.py  "FOOD_FALLOFF 1.0->0.7: stronger cluster preference"
run preyfarm9   bots/variants/batch1/preyfarm9.py   "W_PREY 14->9: farm more, hunt less"
run threat130   bots/variants/batch1/threat130.py   "W_THREAT 90->130: more flight inside ignore radius"
run safety125   bots/variants/batch1/safety125.py   "SAFETY_RATIO 1.12->1.25: bigger safety buffer"
run panicdist55 bots/variants/batch1/panicdist55.py "THREAT_PANIC_DIST 4->5.5: panic earlier"

echo ""
echo "Batch complete. Results in $OUT — commit and push it:"
echo "  git add results && git commit -m 'batch1 results' && git push"
