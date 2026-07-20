# Playbook overview — how to run this project solo (July 7–19)

This folder is a standalone operating manual for the SYNCS Bot Battle
2026 entry. Everything here works without an AI assistant: each file gives
exact commands and decision rules.

## Files

| File | When to read |
|---|---|
| `01-DAILY-WORKFLOW.md` | every day — the operating loop |
| `02-TUNING-PLAN.md` | when picking the next experiment to run |
| `03-FEATURES.md` | when you have a free half-day to build something |
| `04-ENGINE-WATCH.md` | whenever SYNCS ships an engine update (check daily!) |
| `05-TROUBLESHOOTING.md` | when something hangs, crashes, or looks wrong |
| `06-SUBMISSION-CHECKLIST.md` | before every leaderboard submission |
| `07-FOUR-MACHINE-PIPELINE.md` | when standing up the ladder/search/meta/soak boxes |

## Day-1 actions (July 7 — do these first)

1. **Ask in Discord how the leaderboard aggregates results** (largest-cell vs
   consistency round-robins — the slides and docs/scoring.md disagree). This
   sets the tuning objective; v0.1's endgame feature assumes consistency.
2. **Submit** as soon as the portal opens (checklist: 06). Early submission =
   free meta-intelligence from live games.
3. Stand up the four-machine pipeline (07).
4. Confirm the two bug-bounty candidates (README) still hold on the live
   engine version, then report them in Discord ($100 each).

## The three rules (never break these)

1. **Tournaments decide, never eyeballs.** No change ships without winning a
   ≥30-game A/B against the current `bots/my_bot.py` (see 02). Losing
   variants stay in `bots/variants/` and get a row in `TUNING.md` — negative
   results prevent re-testing dead ideas.
2. **One change per experiment.** If a variant differs from baseline in two
   ways and wins, you don't know which change won. CONFIG changes go through
   `tools/make_variant.py`; structural changes get a hand-written variant file.
3. **`bots/my_bot.py` is sacred.** Only merge a variant into it after the A/B
   win, immediately commit with the result in the commit message, and never
   edit it while any tournament is running (matches read the file at start).

## Suggested day-by-day shape

- **Day 1 (Jul 7):** the four actions above, then start batch-1/2 on the
  search box.
- **Days 2–4:** finish batch axes (02 §2–3), merge winners via the ladder
  promotion rule (07), run the candidate-variables list (README) through the
  ladder. Fast-clock screening (03 §6) if throughput is tight.
- **Days 5–8:** features (03) + anti-meta (02 §5): reconstruct what's beating
  you on the live leaderboard, tune against mixed fields. Resubmit on every
  promotion.
- **Days 9–11:** failure-driven search — review worst leaderboard losses each
  evening, encode each failure mode as a candidate term, ladder it.
- **Days 12–13 (Jul 18–19):** freeze. Only run 06's checklist, re-verify the
  submission at real clock speed on the newest engine version, polish
  ALGORITHM.md for the Best Algorithm prize.

## Current state (as of 2026-07-06 evening)

- `my_bot.py` beats the official template 20/20; virus-threshold bug fixed;
  crash guard installed (see README engine-facts table for verified mechanics).
- Tested & closed axes (see TUNING.md): THREAT_IGNORE_DIST=7.0 optimal,
  SPLIT_MAX_RANGE=6.0 optimal, per-blob mass-weighted forces rejected.
- Possibly still running / to check: intercept vs baseline, perblob2 vs
  baseline (check TUNING.md "Pending"; if unlogged, re-run them — commands in
  02 §4).
- batch-1 (10 experiments) queued for the MacBook: `tools/run_batch1.sh`,
  instructions in `MACBOOK.md`.

## Watch daily

- SYNCS Discord for rule/scoring changes (scoring formula was NOT final as of
  Jul 6 — consistency beats occasional 1st places under the drafted formula).
- `pip index versions agario-kit` (or the competitor template repo) for engine
  bumps → immediately do 04's procedure.
- The live leaderboard: note the top bots' visible behaviour for 02 §5.
