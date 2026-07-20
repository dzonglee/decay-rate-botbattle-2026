# Tuning log

Every entry: 30-game 4v4 mirror A/B via `tools/tournament.py`, engine
agario-kit 2026.1.7 under WSL, parallel 5. Lower mean rank is better; wins
count 1st places out of 30. Head-to-head mirror matches suppress final masses
for both sides — judge by rank/wins, not mass.

| Date | A (kept) | B (variant) | mean rank A/B | wins A/B | Verdict |
|---|---|---|---|---|---|
| 2026-07-06 | my_bot THREAT_IGNORE_DIST=7.0 | 9.0 (more fear) | 2.98 / 6.03 | 24 / 6 | 7.0 kept — extra caution starves |
| 2026-07-06 | my_bot THREAT_IGNORE_DIST=7.0 | 5.5 (more greed) | 3.48 / 5.52 | 22 / 8 | 7.0 kept — extra greed dies |
| 2026-07-06 | my_bot (centroid forces) | perblob (per-blob, mass-weighted) | 3.37 / 5.63 | 19 / 11 | rejected — farmed fatter (3.65 vs 1.59 mass) but died more: mass-weighting mutes a small blob's fear |
| 2026-07-06 | my_bot SPLIT_MAX_RANGE=6.0 | 8.0 (longer lunges) | 3.17 / 5.83 | 24 / 6 | 6.0 kept — long lunges overextend |

THREAT_IGNORE_DIST=7.0 is a local optimum on the fear/greed axis (both
directions lost decisively). Axis closed 2026-07-06.

~~Methodology check (2026-07-06): spawns are uniform random, so listing
baseline first is fine.~~ **WRONG — RETRACTED 2026-07-07.** Spawns are
random, but the engine breaks every eating/food-contention tie by **lower
player_id** (state_mutator sort key `(-radius, player_id, blob_id)`). A/A
calibration (batch-3 block 1, identical bots) measured slots 0–3 beating
slots 4–7 at **3.11 vs 5.89 mean rank, 22–8 wins** — the same signature as
our "decisive" results.

**⚠ Every row above this line ran baseline in slots 0–3 (the favored
slots) and is contaminated by slot bias to an unknown degree. Treat all
pre-2026-07-07 verdicts as UNPROVEN, not as rejections.** Gaps *larger*
than the A/A gap (v0.1's 27–3, intercept's 26–4) probably reflect some real
deficit; gaps at or below it (ignore55 22–8, perblob 19–11, preyhunt20
39–11@50) are indistinguishable from bias — some "rejected" variants may
even be improvements. The template-vs-champion result survives: template
held the favored slots and still lost 20/20 with a 7× mass gap.

Harness fixed 2026-07-07: tournament.py and league.py now shuffle slot
assignment per game (`--no-shuffle` exists only for measuring the bias).
All experiments from here on are unbiased; key old experiments should be
re-run. This is also **bug-bounty candidate #3** (see README) — on the
live leaderboard, low player_id is a systematic advantage.

| 2026-07-06 | my_bot (LEAD_TICKS extrapolation) | intercept (true intercept + abandon uncatchable) | 2.97 / 6.03 | 26 / 4 | rejected — intercept points computed from single-frame velocity are noisy; steady short lead wins. Try again only with velocity smoothing (03-FEATURES §4) |
| 2026-07-06 | my_bot (centroid forces) | perblob2 (per-blob, equal-voice threats) | 3.19 / 5.81 | 22 / 8 | rejected — per-blob family dead (both weightings lost); one shared direction cancels per-blob nuance |

| 2026-07-06 | baseline_v0 | **v0.1** (endgame + EMA smoothing α=0.3) | 3.00 / 6.00 | 27 / 3 | **rejected** — worst loss yet; EMA lag is the prime suspect (see JOURNAL). Do NOT merge branch v0.1 to main |

| 2026-07-06 | baseline_v0 | endgame_only (endgame protection, EMA off) | 3.06 / 5.94 | 24 / 6 | **rejected** — passivity loses mass races even from in front; within a match, rank = final mass. v0.1 fully dead (both components individually convicted) |
| 2026-07-07 | my_bot W_PREY=14 | preyhunt20 (W_PREY=20) | 3.30 / 5.70 | 39 / 11 (50 games, MacBook) | rejected — hunting harder loses; W_PREY-up closed |
| 2026-07-07 | my_bot W_THREAT=90 | threat60 (W_THREAT=60) | 3.25 / 5.75 | 40 / 10 (50 games, MacBook) | rejected — less fear inside ignore radius loses; W_THREAT-down closed |

## ⚠ OBJECTIVE CHANGE (2026-07-07): optimize MASS, not rank

The leaderboard scores **Avg Final Weight (mean final mass)** — confirmed
from the first-match results chart. Every verdict above was judged by mean
*rank*; re-judge by **mean mass** (both columns are in every result table).
`tournament.py --sort mass` is now the default. Promotion rule updated:
a challenger promotes if its **mean final mass** beats the champion's over
≥50 shared games by more than noise. Rank/wins are now secondary diagnostics
(survival still matters only because a death scores 0 mass).

Highest-priority re-judgements (variants that lost on rank but had HIGHER
mean mass in their A/B — potential wins under the real objective):
- **perblob** (mean mass 3.65 vs 1.59 — 2.3× fatter)
- **perblob2** (2.04 vs 1.91), **splitrange8** (2.51 vs 2.46),
  **threat60** (2.81 vs 2.36), the endgame/aggression variants

## Pending

- batch-1 / batch-2 / batch-3 — queued for other machines (`tools/run_batch*.sh`).
  batch-2 note: `endgame` and `smooth` are now expected losers (skippable;
  they'd only confirm the two rejections above). The mixed-field runs and
  CONFIG axes remain informative.

Champion remains **v0** (`bots/my_bot.py` on main = `bots/baseline_v0.py`),
now 11 straight A/B defenses.

MacBook batch-1 note (2026-07-07): experiments 3–10 of the first run produced
empty results — the machine likely slept mid-run (use `caffeinate -i`).
Fixed since: tournament.py no longer crashes on zero parseable games, and
batch scripts only mark an experiment done when a result table exists.
To recover on the Mac: `git pull`, delete the broken blocks
(`sed -i '' '/^=== safety105 /,$d' results/batch1_results.txt`), re-run
under caffeinate.
- batch-1 (10 CONFIG axes) — queued for MacBook, `tools/run_batch1.sh`
- batch-2 (20 CONFIG axes + endgame + mixed-field benchmarks) — queued for
  MacBook, `tools/run_batch2.sh`

Baseline my_bot.py has defended 6 straight A/Bs (2 fear/greed probes,
2 per-blob attempts, split range, intercept). The obvious single-axis and
structural-rewrite space is looking exhausted — remaining edges are likely
in: batch-1/2 fine axes, endgame behaviour, and anti-meta tuning vs
archetypes (02-TUNING-PLAN §5).

## Notes

- 2026-07-06 baseline vs template: my_bot 20/20 wins, mean mass 20.8 vs 2.8
  (that run mixed pre/post virus-fix bots mid-run; template comparison only).
- The virus-threshold fix (VIRUS_MASS=1.5, see README engine facts) went in
  before any A/B in this table; all rows use the fixed bot.
