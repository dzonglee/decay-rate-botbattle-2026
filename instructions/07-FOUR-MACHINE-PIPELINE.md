# Four-machine pipeline — concrete setup

README describes the design (ladder / search / meta / soak). This file is the
setup procedure per box. Machines: the Windows/WSL box, the M5 MacBook, plus
two more always-on boxes (any Unix works; macOS/Linux run the engine natively).

## Per-box setup (identical everywhere)

```bash
git clone https://github.com/dzonglee/botbattle.git && cd botbattle
python3 -m venv ~/agario-venv && ~/agario-venv/bin/pip install agario-kit
export AGARIO_SIM=~/agario-venv/bin/simulation      # add to shell profile
```

Windows box: already set up (WSL Ubuntu-24.04, `tools/tournament.py` wraps it
automatically). Memory cap: ~10 concurrent matches. Since engine 2026.1.8,
headless games run unthrottled (~5 s each) — a single box does thousands of
games/hour, so 50-game rungs finish in ~2 minutes. Statistical power is
cheap now: default to 50-game screens and 100-game promotions.

**Find each box's ceiling once**: run a 20-game tournament at `--parallel 10`,
then 15, then 20 — the ceiling is the last setting with zero
`[warn] match ... hung` lines. Use ~80% of that ceiling for standing jobs.

## Box 1 — Ladder (champion vs challengers)

The champion is `bots/my_bot.py` on `main`. Challengers come from the search
box, batch results, or hand-written features.

```bash
# one ladder rung = 50 games, same lineup:
python3 tools/tournament.py --games 50 --parallel 8 --tag ladder_<challenger> \
    4:bots/my_bot.py 4:bots/variants/<challenger>.py \
  | tee -a results/ladder.log
```

**Promotion rule** (from the opening-ceremony plan): challenger wins if its
mean rank beats the champion's by **> 0.55** over ≥50 games (that's ≈2×SE with
rank SD ~2, n=50). On promotion:

1. Merge the change into `bots/my_bot.py`; keep the old champion as
   `bots/baseline_v<N>.py`.
2. Row in TUNING.md with the diff and numbers; commit; push; resubmit to the
   portal (after instructions/06 checklist).
3. Re-queue the top 2–3 previously-rejected challengers against the new
   champion (a new champion reopens closed axes — but only the big ones:
   W_THREAT, W_PREY, THREAT_IGNORE_DIST).

## Box 2 — Search (automated CONFIG exploration)

Seeded version: `run_batch1.sh` / `run_batch2.sh`. After those, hill-climb:

```bash
# example: perturb one weight ±30% around the champion value
python3 tools/make_variant.py bots/my_bot.py -o bots/variants/search/wthreat_63.py W_THREAT=63.0
python3 tools/tournament.py --games 30 --parallel 8 --tag s_wthreat63 \
    4:bots/my_bot.py 4:bots/variants/search/wthreat_63.py | tee -a results/search.log
```

Anything that wins a 30-game screen here goes to the ladder for the 50-game
promotion test. **Never promote from this box directly** — screening wins are
noisy and fast-clock screens (03 §6) are approximations.

## Box 3 — Meta (anti-leaderboard)

Watch the leaderboard daily; classify the top bots (archetypes: Aggressive,
Aggressive-Shy, Hungry, Hungry-Shy). `bots/meta/` has Aggressive + Hungry-Shy;
write the others the same way (~40 lines each) when needed.

```bash
python3 tools/tournament.py --games 50 --parallel 8 --tag meta_$(date +%m%d) \
    2:bots/my_bot.py 2:bots/variants/<candidate>.py \
    2:bots/meta/aggressive.py 2:bots/meta/hungryshy.py | tee -a results/meta.log
```

Mixed fields are closer to leaderboard reality than mirrors — README's
"Known unknowns" explains why mirror wins can mislead. When meta-box and
ladder-box disagree about a candidate, **trust the meta box**.

## Box 4 — Soak (crash hunting + bug bounty)

Long, boring, valuable: the leaderboard bans erroring bots.

```bash
# run forever, log everything, grep later
while true; do
  python3 tools/tournament.py --games 100 --parallel 5 --tag soak \
      8:bots/my_bot.py >> results/soak.log 2>&1
  grep -rl Traceback ~/.agario_tourney/soak_ws*/submission*/io/submission.log \
      >> results/soak_tracebacks.txt 2>/dev/null
done
```

Also watch for engine anomalies (weird masses, desyncs, blobs outside the
arena in logs) — each is a $100 bounty candidate. Two candidates are already
documented in README ("Bug-bounty candidates"); confirm them on the live
engine version before reporting in Discord.

## Coordination

- One repo. Every box: `git pull` before a run block, `git add results &&
  git commit -m '<box>: <what>' && git push` after. Pull-before-push; if two
  boxes race, `git pull --rebase` resolves it (results files are append-only).
- Variants are only ever *generated* on one machine at a time per name —
  prefix search-box variants with `search/` to avoid collisions.
- Evening review (the real bottleneck is your time, not compute): read the
  day's `results/*.log` tails + TUNING.md, pick tomorrow's hypotheses, queue
  them as variant files, push.
