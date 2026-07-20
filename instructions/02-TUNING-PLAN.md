# Tuning plan — what to test, in what order

## §1 Method: one-axis hill climbing

For each CONFIG knob: test one value on each side of current. If one side
wins, step further in that direction until it stops winning; the last winner
becomes the new baseline value. If both sides lose (like THREAT_IGNORE_DIST
7.0 vs 9.0 and 5.5), the axis is closed — record it in TUNING.md and don't
revisit unless the bot changes structurally (a structural change reopens
every axis, but retest only the big three: W_THREAT, THREAT_IGNORE_DIST,
W_PREY).

## §2 Immediate queue: batch-1 (may already be done on the MacBook)

`tools/run_batch1.sh` runs these; results land in `results/batch1_results.txt`.
If the Mac run never happened, run them one-by-one on Windows (2 at a time,
`--parallel 5`).

Priority order and what each probes:

| # | Variant | Axis | Hypothesis |
|---|---|---|---|
| 1 | preyhunt20 | W_PREY 14→20 | more hunting compounds the snowball |
| 2 | threat60 | W_THREAT 90→60 | current fear is overtuned inside 7 units |
| 3 | safety105 | SAFETY_RATIO 1.12→1.05 | daring closer margins wins more food races |
| 4 | blobs2 | SPLIT_MAX_BLOBS 4→2 | staying compact avoids picked-off fragments |
| 5 | lead8 | LEAD_TICKS 4→8 | longer extrapolation flees/chases smarter |
| 6 | foodfall07 | FOOD_FALLOFF 1.0→0.7 | stronger cluster-seeking out-farms |
| 7 | preyfarm9 | W_PREY 14→9 | hunting is a trap; farming compounds better |
| 8 | threat130 | W_THREAT 90→130 | more fear inside 7 units survives longer |
| 9 | safety125 | SAFETY_RATIO 1.12→1.25 | bigger buffer avoids coin-flip fights |
| 10 | panicdist55 | THREAT_PANIC_DIST 4→5.5 | panicking earlier escapes more |

For each winner: hill-climb one more step (e.g. if preyhunt20 wins, generate
W_PREY=28 and test that against the *new* baseline).

## §3 Refinement round (after batch-1 winners are merged)

- Retest the closed axes against the new baseline **only if ≥2 batch-1
  changes merged** (interactions can move optima): THREAT_IGNORE_DIST 6/8,
  SPLIT_MAX_RANGE 5/7.
- Untested axes that remain: W_FOOD (try 0.6, 1.6), W_WALL (4, 14),
  WALL_MARGIN (2.5, 6), PREY_FALLOFF (1.0, 2.0), THREAT_FALLOFF (1.5, 2.5),
  W_REGROUP (0.5, 5), SPLIT_SAFETY_RATIO (1.25, 1.5),
  SPLIT_THREAT_CLEARANCE (7, 12), VIRUS_AVOID_DIST (2.5, 5),
  CHASE_HORIZON (30, 100 — only if the intercept variant merged).
  These are second-tier: expect small effects, use 50 games.

## §4 Structural variants — verdicts in (2026-07-06 evening)

Both lost decisively (rows in TUNING.md):

- `intercept.py` rejected 26–4. Root cause hypothesis: single-frame velocity
  estimates make the intercept point jitter. **Only** revisit after adding
  EMA velocity smoothing (03-FEATURES §4) — smoothing alone is also worth an
  A/B on the baseline (it feeds LEAD_TICKS extrapolation too).
- `perblob2.py` rejected 22–8; with perblob's 19–11 this closes the per-blob
  family. Do not revisit (03-FEATURES §5).

## §5 Anti-meta round (days 8–11) — likely the biggest remaining edge

Mirror A/Bs optimize against *yourself*. The leaderboard opponents differ.

1. Watch replays / the visualiser of top leaderboard bots. Classify each into
   an archetype (from the AgarCL literature): **Aggressive** (hunts anything
   edible), **Aggressive-Shy** (hunts but flees bigger), **Hungry** (pure
   food, ignores players), **Hungry-Shy** (food + flees).
2. Reconstruct each archetype as a bot file (~30 lines each; template_bot.py
   is already "Hungry"; "Hungry-Shy" = template + flee-if-bigger-within-5;
   "Aggressive" = chase nearest smaller blob, else food).
3. Tune against the reconstruction of whatever is winning:

```powershell
python tools/tournament.py --games 30 --parallel 5 --tag meta `
    2:bots/my_bot.py 2:bots/variants/<candidate>.py 2:bots/meta/aggressive.py 2:bots/meta/hungryshy.py
```

Mixed fields like this are closer to real leaderboard conditions than 4v4
mirrors — from this round on, prefer them for all A/Bs.

## §5a Candidate-variable ladder (from the opening-ceremony plan)

The README's "Candidate variables" list (risk appetite, soft intercept
feasibility, late-game gamble-when-small, food memory, threat velocity,
virus shelter, crowding penalty) supersedes ad-hoc feature picking: each is
one hypothesis behind one weight (0 = off), laddered one at a time per 07's
promotion rule. Statuses are tracked in the README list; sketches for the
implemented/spec'd ones live in 03-FEATURES.

## §6 Statistical notes

- Screening: 30 games detects rank gaps ≳ 1.0 reliably. **Promotion**: ≥50
  games same-lineup, margin > 0.55 mean rank (≈2×SE at rank SD ~2) — see 07.
- Variance between identical runs is real. If a result surprises you
  (contradicts a prior run), re-run before acting — one 30-game tournament
  produced 24 wins for a config that later ideas resembled; trust repetition.
- The drafted scoring rewards **consistency** (sliding-window round-robins,
  +4/+2 for 1st/2nd): a bot with mean rank 3.0 and sd 1.5 likely outscores
  mean 2.8 / sd 2.5. When two variants tie on mean rank, prefer lower sd.
