#!/usr/bin/env bash
# Batch 3 — analysis workloads that evolution/weight-search cannot cover:
#   A) A/A noise calibration (identical bots -> measured significance floor)
#   B) Ablation knockouts (which force terms carry the bot?)
#   C) Style payoff matrix (rock-paper-scissors structure of the meta)
#
#   ./tools/run_batch3.sh                 # 30 games/experiment, 6 parallel
#   GAMES=50 PAR=8 ./tools/run_batch3.sh
#
# Resumable like the other batches. All runs anchor on bots/baseline_v0.py
# (the frozen v0 champion) so results stay comparable even after promotions.
set -u
cd "$(dirname "$0")/.."

GAMES="${GAMES:-30}"
PAR="${PAR:-6}"
PYTHON="${PYTHON:-python3}"
OUT=results/batch3_results.txt
mkdir -p results
touch "$OUT"

run() {
    local name="$1"; shift
    local note="$1"; shift
    if grep -q "^=== $name " "$OUT"; then
        echo "skip $name (already in $OUT)"
        return
    fi
    echo ""
    echo "=== $name — $note"
    local tmp
    tmp=$(mktemp)
    {
        echo "=== $name games=$GAMES — $note"
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

B=bots/baseline_v0.py
V3=bots/variants/batch3

# --- A) A/A calibration: identical bots. Run FIVE independent blocks; the
#        spread of the five mean-rank "gaps" is our empirical noise floor.
#        Interpretation: if |gap| in A/A blocks reaches X, then a real A/B
#        needs a gap comfortably above X to mean anything.
for i in 1 2 3 4 5; do
    run "aa_block$i" "A/A block $i: identical bots, gap = pure noise" \
        "4:$B" "4:$V3/aa_copy.py"
done

# --- B) Ablations: each force term zeroed. Expect most to lose hard —
#        the *ordering* of how hard is the finding (term importance map).
run ab_nothreat  "knockout W_THREAT: how fatal is fearlessness?"        "4:$B" "4:$V3/ab_nothreat.py"
run ab_noprey    "knockout W_PREY: pure farmer vs hunter champion"      "4:$B" "4:$V3/ab_noprey.py"
run ab_nofood    "knockout W_FOOD: hunt-only, no farming"               "4:$B" "4:$V3/ab_nofood.py"
run ab_nopredict "knockout LEAD_TICKS: react to positions, not futures" "4:$B" "4:$V3/ab_nopredict.py"
run ab_nopanic   "knockout panic multiplier: flat threat response"      "4:$B" "4:$V3/ab_nopanic.py"
run ab_nowall    "knockout W_WALL: does wall fear earn its keep?"       "4:$B" "4:$V3/ab_nowall.py"
run ab_noregroup "knockout W_REGROUP: fragments fend for themselves"    "4:$B" "4:$V3/ab_noregroup.py"
run ab_novirus   "knockout W_VIRUS_BIG: ignore viruses entirely"        "4:$B" "4:$V3/ab_novirus.py"

# --- C) Style payoff matrix: pairwise 4v4 among the four known styles.
#        Read as: who exploits whom. Predicts leaderboard meta drift.
run pm_champ_aggr  "payoff: champion vs Aggressive"    "4:$B" "4:bots/meta/aggressive.py"
run pm_champ_shy   "payoff: champion vs Hungry-Shy"    "4:$B" "4:bots/meta/hungryshy.py"
run pm_champ_tmpl  "payoff: champion vs Template"      "4:$B" "4:bots/template_bot.py"
run pm_aggr_shy    "payoff: Aggressive vs Hungry-Shy"  "4:bots/meta/aggressive.py" "4:bots/meta/hungryshy.py"
run pm_aggr_tmpl   "payoff: Aggressive vs Template"    "4:bots/meta/aggressive.py" "4:bots/template_bot.py"
run pm_shy_tmpl    "payoff: Hungry-Shy vs Template"    "4:bots/meta/hungryshy.py" "4:bots/template_bot.py"

echo ""
echo "Batch 3 complete. Results in $OUT — commit and push:"
echo "  git add results && git commit -m 'batch3 results' && git push"
