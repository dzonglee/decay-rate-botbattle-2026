# SYNCS Bot Battle 2026 — Agar.io Bot

Competition bot for the SYNCS x Susquehanna Bot Battle 2026 (July 6–19).
This README is a **handover document for Claude Code**: it contains everything
needed to continue development without re-deriving the engine's behaviour.

## Competition facts (confirmed from opening-ceremony slides, 6 July)

- Submission portal: **opens 7 July, closes 19 July midnight**. Resubmission is
  continuous — submit v1 on day 1 for leaderboard meta-intelligence.
- Engine updates pushed via `uv sync --upgrade`, announced in the Bot Battle
  Discord. Check Discord daily; mid-comp rule changes are precedented.
- Slides say "largest cell wins, 8-player timed matches" — but docs/scoring.md
  describes consistency-weighted round-robins. **OPEN QUESTION (ask in Discord):
  how does the leaderboard aggregate match results?** Pure per-match mass
  ranking favours boom-bust aggression; consistency weighting favours reliable
  top-3 play. This changes the tuning objective — resolve it early.
- **Bug bounty: $100.** We have read the engine source closely. Log any engine
  anomaly (physics edge cases, desyncs, split/merge oddities) — report, don't
  silently work around.
- Chris is competing **solo** with **four always-on machines**. Prize money
  undivided; the constraint is his replay-review time, not compute.

## Status at handover

- `bots/my_bot.py` — working potential-field bot, verified against engine
  `agario-kit==2026.1.6`. In mixed 8-player matches vs the official template
  bot it **won 4/4 tournament games** (mean rank 3.12 vs 5.88, mean mass ~23 vs ~3)
  and has hit final masses of 40–76 when the snowball gets going.
- `bots/template_bot.py` — the official starter (nearest-food chaser). Keep as
  a tuning baseline; never delete.
- `tools/tournament.py` — parallel headless tournament harness. **All changes
  must be judged by this script**, ≥20 games, never by watching one match.

## Environment / running

Official template uses `uv` (see github.com/syncs-usyd/agario-competitor), but
plain pip works too:

```bash
pip install agario-kit            # engine + helper published on PyPI
simulation --headless 4:bots/template_bot.py 4:bots/my_bot.py   # one match
interactive 7:bots/my_bot.py      # play manually vs 7 copies (GUI)
python3 tools/tournament.py --games 20 --parallel 4 \
    4:bots/template_bot.py 4:bots/my_bot.py                     # tuning run
```

- Counts in `count:path` specs must sum to **8** (or 7 for `interactive`).
- Match outcome line: `ranking=[...] final_masses={...}` — slot order matches
  the order bots were listed in the specs.
- Per-slot logs land in `<workspace>/submission<N>/` (app1.log + io/submission.log).
- When SYNCS publishes a new engine version: `pip install -U agario-kit`
  (or bump the pin in the official uv template). **Check the changelog/diff
  every time — rules may change mid-competition.**

## Engine facts (from lib/config, v2026.1.6 — re-verify after any kit update)

| Constant | Value | Implication |
|---|---|---|
| ARENA_SIZE | 60×60 | small map, contact is constant |
| NUM_PLAYERS | 8 | spawn in corners |
| MAX_ROUNDS | 1400 @ 0.1s | ~2.3 min real-time games |
| Vision | square ~20, scales with Σradii | you never see the whole map |
| EAT_SIZE_RATIO | 1.2 | need 20% larger **radius**, centre inside you |
| Speed | 1.1 − 0.08·r, floor 0.25 | big = slow; small bots outrun giants |
| MASS_DECAY_RATE | 0.2%/tick | mass ~ radius²; floor ≈ starting mass 0.81 |
| FOOD | 160 pellets, r=0.15 | +0.0225 mass each; ~1 pellet/14 ticks breaks even vs decay |
| SPLIT | mass ≥ 2.0, cooldown 18 ticks, max 16 blobs | eject speed 1.6, drag 0.82 → lunge reach ≈ 8.9 units |
| VIRUS | 6, r=1.5 | eating one force-splits you (mass must be ≥1.2× virus to consume) |
| Respawn | 30 rounds after death | death ≈ losing all mass + 3s |

Scoring/rank (docs/scoring.md in engine repo) is **not finalised**: currently
described as repeated round-robins in a sliding window, with score offsets by
opponent strength and +4/+2 bonuses for finishing 1st/2nd. **Consistency across
many games beats occasional dominance.** Watch their Discord for changes.

## Bot architecture (`bots/my_bot.py`)

Single file (submission format). Four parts:

1. **CONFIG** — every tunable weight. Tune here only.
2. **Tracker** — per-enemy-blob velocity from frame-to-frame positions;
   `predict(blob, ticks)` extrapolates. Used for interception and fleeing.
3. **compute_forces** — potential fields: food attracts (falloff 1.0 so
   clusters beat lone pellets), edible enemies attract ∝ mass, dangerous
   enemies repel ∝ mass with panic multiplier < 4.0 units, viruses repel when
   we're big enough to pop, walls repel inside 4-unit margin, own blobs pull
   together when threatened.
4. **should_split** — lunge only if: predicted prey ≤ SPLIT_MAX_RANGE, each
   post-split half ≥ 1.35× prey radius, no threat within 9 units, ≤ 4 blobs,
   and current movement already points at the prey (dot > 0.7).

Key lesson already learned the hard way: an early version had unbounded
threat repulsion — small bots fled visible giants forever and starved at the
mass floor. Fix was `THREAT_IGNORE_DIST` (big = slow = harmless at range).
Expect more bugs of this shape: **starvation-by-fear and death-by-greed are
the two failure modes; every weight change trades between them.**

## Four-machine research pipeline (set this up first)

Games are sleep-bound (engine runs wall-clock at 0.1s/tick), so parallelism per
machine is limited by memory/process/file-descriptor overhead, not cores.
Expect 15–30 concurrent matches per box ≈ ~2,000 games/hour across four
machines. Verify the practical ceiling per box before committing to run sizes.

Standing jobs — one per machine:

1. **Ladder box** — champion vs challengers, continuously. Promotion rule:
   a challenger replaces the champion only if its mean rank beats the
   champion's over **≥50 games in the same lineup** by a margin exceeding
   noise (rough guide: difference > 2×SE of mean rank; with rank SD ~2 and
   n=50, that's ≈0.55 mean-rank improvement). Log every promotion with the
   CONFIG diff that caused it.
2. **Search box** — runs the evolution strategy (`tools/evolve.py`): maintains
   a population of CONFIG genomes, evaluates each over N matches vs a reference
   pool, keeps elites, refills via mutation+crossover. Checkpointed to
   `evolution/state.json` (resumable). Recommended overnight loop:
   ```bash
   python3 tools/speed_patch.py set 0.01     # ~10x faster games
   python3 tools/evolve.py --pop 16 --gens 15 --games 20 --parallel <calibrated>
   python3 tools/speed_patch.py restore
   ```
   **Calibrate --parallel per machine first** (start low, raise until matches
   start failing — failures are logged to evolution/failures.log; in a small
   container 8 concurrent was already too many, real machines take 15-30).
   Ship each night's best genome to the ladder for real-speed verification.
   Never promote from this box directly.
3. **Meta box** — champion vs hand-written reconstructions of whatever is
   beating us on the live leaderboard (start with the four archetypes:
   Aggressive, Aggressive-Shy, Hungry, Hungry-Shy). Retune when the meta shifts.
4. **Soak box** — long unattended runs hunting crashes/hangs/anomalies.
   Protects against the leaderboard error-ban; anomalies feed the bug bounty.

Coordination: one git repo; each box pulls, runs, appends outcome lines to
`results/<box>.log` (the `ranking=/final_masses=` lines plus variant id), and
pushes. Review aggregates each evening; pick next day's hypotheses from the
worst replays. Screening runs may use a locally patched TURN_DURATION_SECONDS
(site-packages) for speed, but **all promotion decisions re-verified at real
speed** — bot compute-per-tick matters at 0.1s.

## Candidate variables (test one at a time via the ladder; expect most to die)

Each encodes one ruleset hypothesis; implement behind a single weight
(weight=0 disables):

1. Risk appetite ∝ (mass − 0.81 floor): gamble when near-broke, coward when fat.
2. Intercept feasibility: chase only if closing speed × time-to-cover > distance.
3. Round-number term: last ~150 rounds, freeze risk if big / max gamble if small.
4. Food memory: revisit pellet-dense regions that left the vision square.
5. Threat velocity: a giant moving away is not a threat; intercept courses are.
6. Virus shelter: when hunted, keep a virus between us and the pursuer.
7. Crowding penalty: avoid 3+ blob melees regardless of sizes (third-party risk).

After these, source new candidates from **failure-driven search**: watch the
worst losses, name the failure mode, encode it as a term, ladder it.

## Roadmap (in priority order)

1. **Stand up the four-machine pipeline above**, then run the candidate list
   through the ladder. Variant generation: copy my_bot.py, regex-replace CONFIG
   values — never hand-edit two changes at once.
2. **Per-blob forces.** Currently forces are computed from the mass centroid.
   When split, each of our blobs has its own threats/prey. Compute the force
   sum per own-blob, then combine (the engine takes one direction for all
   blobs, so weight by mass — but the *threat classification* should already
   be per-blob, which it partially is via `my_smallest`).
3. **Interception geometry.** Replace "predict N ticks ahead" with a proper
   intercept: solve for the point where our speed can meet prey's projected
   path; abandon chases with no intercept before prey reaches cover/vision edge.
4. **Virus tactics.** (a) When small: bias pathing to keep a virus between us
   and the nearest threat. (b) When big and a rival is 1.2×+ our size near a
   virus: consider feeding/pushing them onto it — check engine rules for
   whether split-eject can shove viruses (it can in classic Agar.io; unverified
   here — read `src/lib/game/` in github.com/syncs-usyd/agario-public).
5. **Endgame awareness.** `game.state.round` vs MAX_ROUNDS=1400: final ~150
   rounds, stop risky chases if our current mass likely ranks top-2 (we can't
   see the leaderboard, but visible-blob sizes are a proxy).
6. **Anti-meta.** Re-run tournaments against reconstructions of whatever is
   winning on the live leaderboard (Aggressive / Aggressive-Shy / Hungry /
   Hungry-Shy archetypes from the AgarCL literature). Retune weekly.
7. **Best Algorithm prize**: maintain `ALGORITHM.md` describing: potential
   fields, velocity-prediction interception, split-safety gating, and
   empirical weight tuning via automated parallel self-play tournaments.

## Known unknowns / risks

- Scoring formula not final; an expansion-pack-style rules change mid-event is
  likely (last year's Carcassonne comp had one). Keep everything data-driven
  from CONFIG and engine constants — never hardcode derived numbers inline.
- `me.radius` semantics when multi-blob (aggregate vs largest) — verified
  per-blob logic is used everywhere it matters, but re-check after kit updates.
- Repeated bot errors ⇒ leaderboard ban until fixed (per comp rules): the main
  loop must never raise. Consider wrapping `choose_move` in try/except that
  falls back to fleeing toward arena centre.
- Per-tick time budget: keep decision code O(visible objects); no heavy
  allocations in the loop.

## Repo layout

```
botbattle/
├── README.md            ← this file
├── bots/
│   ├── my_bot.py        ← the submission (single file)
│   └── template_bot.py  ← official baseline, do not modify
└── tools/
    └── tournament.py    ← parallel tuning harness
```
