# ASSISTANT.md — how the assistant operates the evolver and assists Chris

_Created 2026-07-16 (Chris's standing order). Companion to OPERATOR.md (the
operation itself) and JOURNAL.md (the record). This file is about HOW the
assistant works: the loops it runs, the standards it reports to, and the
division of labor between it and Chris. Keep current alongside OPERATOR.md._

## 1. Division of labor
- **Chris decides**: what to train (world/room shape), what to ship, when to
  upload (he uploads to SYNCS himself — assistant only stages in
  `~/Desktop/ship_staging/`), pool changes (BEST_BOTS frozen otherwise), any
  auto-launch/cron, anything exposing services to the internet.
- **Assistant executes**: runs the gym day-to-day, designs + queues injection
  batches, mines results, archives/switches worlds on order, builds and
  verifies ships/bundles, pulls competition intel, restarts infra after
  failures (restart of the *campaign* requires Chris's explicit order; a
  crashed component mid-session may be restored per OPERATOR procedures).
- **Assistant proposes, never assumes**: new mechanisms (lookahead, modes),
  registry changes, engine migrations — pitched with evidence + cost, executed
  only on Chris's word.

## 2. Operating the evolver — the assistant's loop
1. **Watch**: portal `/api` counter movement (not tput right after restart),
   `ladder_log.jsonl` results, INJECT events, tracebacks in `logs/ladder_v3.log`.
2. **Steer with injections** (2/cull): design batches as named experiments —
   wave 1 style (archive-derived: take proven genomes, transplant organ
   families/graphs across lineages) and wave 2 style (hypothesis-driven:
   explicit best-guesses encoded as gene payloads, 8–12 variants each, control
   arms where cheap). Lineage tags must encode the experiment (`e3r10-j09`,
   `h7-modsplit-004`) so survival statistics answer the hypothesis.
   - Injectables carry the FULL ~260-gene space. Only registry genes
     (`config/exposed_genes_ACTIVE.json`, currently 144 CGP-heavy) evolve;
     non-registry genes ride via injection and inherit from parent A in
     crossover — injection is the ONLY lever for those families. Pin LA
     invariants AFTER jitter; clamp to bounds; py_compile samples under the
     gym's 3.12 before queueing.
3. **Mine**: at each visit, rank the pool (depth-qualified n≥150–300 only;
   never quote window peaks), track which lineage tags survive/lead, feed the
   findings into the next batch design and into JOURNAL.md.
4. **Escalate to Chris** when: a champion is deep-n + flat-trajectory
   (ship-worthy), a world's purpose is exhausted, live meta shifts (room
   composition, elite band), or evidence contradicts a standing assumption.

## 3. Assisting Chris — reporting standards
- **Lead with the answer**; detail after. Compact **Summary** block at the end
  of every action-bearing reply.
- **Sydney time (AEST, UTC+10)** always; laptop clock is CST (+2h), server UTC (+10h).
- **Sample discipline**: state n everywhere; ⚠ small samples; never mix win%
  and mass columns from different samples unflagged; classify opponents by
  CURRENT leaderboard avg (E>20 / C 10–20 / G<10; Chris 2026-07-16), not
  per-game mass.
- **Mode-switch elite set (SUPERSEDED 2026-07-17)**: Chris's endgame rule is
  `ELITE_TEAM_IDS` = CURRENT top-10 leaderboard ids minus us, refreshed from
  meta_report at every build ("compute the top 10 as the elite now"). The
  old hard-room-survivor gate (current-first n=300, hard n>=100, win>=18.75%,
  rank<=3.00) is retired for mode IDs but remains the right instrument for
  judging who is a REAL threat in reports. Pins still possible on Chris's
  word (2026-07-17: chimken_wingz 49 fell out of the top 10 and is NOT
  pinned unless he says so). Reporting tables retain E>20 for continuity.
- **Elite comparison format (Chris preference, 2026-07-16)**: when comparing
  submissions against elites, include `non-successful/ban rows` (`ours banned`
  separately) and the per-opponent table `times faced | times we placed above
  them | above%`. Chris explicitly likes this table; preserve it, state each n,
  and mark small opponent cells ⚠.
- **Trajectory discipline**: bots are quoted at depth (n≥150+, flat/rising
  per-chunk), never at window peaks. The anchor is the honest floor.
- **Falsifiability**: when Chris challenges a conclusion ("but that doesn't
  explain X?"), re-derive from raw data — his challenges have twice found the
  real cause (kill-feed retraction; room-composition root cause). Cross-check
  causal claims across ≥2 windows; verify mechanisms in source before
  believing timing coincidences.
- **Local data first**: named local source missing data → report the gap and
  STOP; remote fetches only through the established, Chris-sanctioned channels
  (Hermes meta_extend pattern) or on his explicit word.
- **Verification before staging**: every body change proves itself inert
  (equiv_test bit-identical + verify_moves 0 mismatches); every bundle passes
  the full gate battery (fold audit, per-mode CONFIG fidelity, ladder walk,
  pre/post-cutover witnesses, live-engine smoke with 0 bans) BEFORE the sha
  goes in the vault log and the file goes to ship_staging.
- **Journal selectively, same day** (JOURNAL.md): it is source material for the
  final `algorithm.md` / best-algorithm-award submission. Record durable
  algorithmic discoveries, verified mechanisms/incidents, consequential
  operational actions, and final decisions. Do NOT add routine small-n
  refreshes, repeated statistical clarifications, ordinary health checks, or
  every tool call. Update OPERATOR.md when procedures/infra/state materially
  change; update this file when the assistant's own working method changes.

## 4. Session rhythm (what a good assistant-day looks like)
1. Health sweep: ladder alive, portal counter moving, all nodes ok, no
   tracebacks, inject queue depth.
2. Pool review: depth-qualified leaders, lineage-tag survival, anchor floor.
3. Live intel (when warranted): run `python3 tools/meta_report.py` — the
   canonical, self-contained meta analysis (extends the Hermes cache with
   sims paused/resumed, prints composition windows, per-submission conditional
   performance, elite head-to-head, and each current elite's latest-submission
   hard-era placement proxy so cumulative easy-room buffers are separated from
   current form). Do NOT hand-roll this analysis; the tool encodes the schema,
   tiers, sample guards, and the separate hard-room-survivor gate used for
   bundle mode IDs. Compare submissions only on
   same-composition cells; headline averages across different room mixes are
   meaningless.
   **RULE (Chris 2026-07-16): every meta analysis pulls the latest results
   first — extending the cache is cheap (seconds), a stale snapshot is not.
   The tool extends by default; `--no-extend` exists only for offline reruns
   over an already-fresh cache within the same session. Time-confounding
   guard: compare submissions only over their overlap era (`--since`), never
   against a long-lived sub's full history.**
4. Act on divergence: propose room re-aim / new injection wave / bundle
   rebuild to Chris with evidence.
5. Close the loop: journal entries, doc updates, staged artifacts sha-logged.

## 5. Hard-won heuristics (assistant-specific)
- ARCHITECTURE cannot be validated by carrier injection into the elitist
  ladder (2026-07-17, Chris's diagnosis): genes spread only via top-6, so an
  innovation must beat champions while UNTUNED — big-delta organs die in the
  valley, small-delta organs drift; nothing is refined. Architectural changes
  go through SHADOW MODE (propose-log-grade counterfactually, execute
  reactive) and/or a NURSERY pool (all-carrier population tunes organ weights
  internally, graduate the champion). Carrier injection is for weight-level
  tweaks only. See PLANNER_REDESIGN.md.
- Solved tables/playbooks: integration tests prove SAFE WIRING, never policy
  quality. Before any book's carriers enter evolution it must beat the
  reactive baseline in a continuous-state paired-seed harness (see
  tools/ev_harness.py; 2026-07-16: a tie-break bug made the v1 EV table lose
  to dead-away 25x — only the harness caught it). Books integrate as
  CANDIDATE GENERATORS for the planner, not raw overrides.
- Fat tails dominate single-genome results: n=8–12 medians/means swing wildly;
  don't diagnose code from small-n performance gaps — prove behavior with
  bit-exact tools instead (the switch-bundle investigation: machinery was
  faithful; the "defect" was variance + a live meta shift).
- `/tmp` dies with the laptop: anything load-bearing (genomes, venvs,
  backups) must live in the repo/archives; re-source from archives after any
  reboot rather than trusting stale /tmp paths.
- The gym's seat ids collide with real elite team ids (1/4/5) — local witness
  matches DO exercise ship-mode switching (useful), and local 0E behavior is
  under-tested (use pinned-id builds to force branches).
- Every ship regression investigation starts with: what changed in the WORLD
  (engine version, room composition, opponent set) before what changed in the
  code.
- PL3 organ + carrier campaign (2026-07-17 evening): the lite planner is IN
  THE BODY as ORGAN PL3 (movement-only, threat<PL3_RANGE, mass<PL3_MAXM,
  authority dial; per-fire 200ms deadline, graduated 5.0s wall-clock governor
  -> degrade to reactive, never ban). Campaign tooling: `tools/pl3_score.py`
  scorecard per cull; persistent ladder_log monitor wakes on CULL_BREED/
  INJECT; injection waves are DESIGNED experiments (exact off-twins +
  authority levels; insurance clones of elite carriers when churn is hot;
  root-lane-only injection once breeding carries the genes). Bundle codegen
  is make_bundle.py v4: modes 0/1/2/FINAL, ELITE_IDS = top-10 minus us
  refreshed at every build, three-lever finals detection in the body.
- Planner-v3 instrument suite (2026-07-17, all durable): `tools/sim_engine.py`
  is the ONE authoritative transition (differential gate vs real engine:
  7200/7200 rounds bit-exact — rerun it under the gym venv after ANY engine
  version bump); `tools/planner_v3.py` plans over the body's real
  `_reactive_core` with a censored-vision adapter + opponent ensemble +
  CVaR/LCB acceptance; `tools/shadow_grade.py` produces paired counterfactual
  evidence from harvested replays (opponents replay recorded moves). Bit-exact
  sim work requires FP-association fidelity: engine computes `x*(r*r)`,
  `move_a = ov*(mb/tm)` pre-multiplied, constants as `0.9*0.9`/`0.15*0.15` —
  literals like 0.81 differ in the last bit and flip boundary branches.

## Delta 2026-07-19 midday
- ranking field in server match metadata is 0-INDEXED (0 = win). era2500.py/tables2.py use it right.
- Studio homebrew python3.14 wiped websocket-client; reinstall needs --break-system-packages.
- Elite list rule (Chris): everyone above spaghetti on the live leaderboard, refresh at every build.
- PL4 body gene is PL4_CRIT_TTC (not the spec's PL4_CRIT_RANGE).
- HARDWARE LAW (2026-07-19): competition server ~5x slower than our machines (PL3 fire 203ms vs
  42ms). Organ budget-seconds are wall-clock and DO cap correctly, but ungoverned base load
  (reactive/parse) is ~2-3s at server speed — total organ caps must stay <= 2.5s (v8's proven
  987-game envelope). Never upload >= 4.5s organ budgets. v13 retracted on these grounds.
