# PLANNER_REDESIGN.md — the proper receding-horizon planner (post-freeze work)

_Recorded 2026-07-17 from the verified failure analysis of PLANCORE and the
external review's specification. This is the build plan for the real thing.
Nothing here ships before the 2026-07-19 freeze._

## Why every planner attempt failed (two independent causes)

### Cause 1 — implementation: none of the attempts was a real planner
- PLAN v1/v2: surrogate value function (5 hand constants vs the bot's 260
  tuned weights); planner bolted downstream of all decisions.
- PLANCORE: engine-true physics but ZERO terminal value — only events
  completing within H=3-4 ticks scored. Two futures without an immediate eat
  or loss were indistinguishable; a farming override needed ~23-45 pellets
  contacted in 4 ticks. The 1.6% override rate was blindness, not restraint.
  Continuation policy `_pc_react` = 3-term toy, not the production policy —
  every rollout (including the baseline's) simulated a bot that doesn't
  exist. Residual defects: order-dependent candidate acceptance; PC_SPLIT=0
  still re-aimed reactive splits; downstream LA veto could strip the split
  bit off an evaluated action.
- Paired verdict at depth (n=574/arm): mean −1.92 mass, median −2.65,
  bootstrap 95% CI [−5.57, +1.77], P(positive) ≈ 15%.

### Cause 2 — evaluation: the gym structurally cannot validate architecture
The ladder is elitist: genes spread only via the top-6 pool; newborns get
GRACE then must beat champions. An architectural innovation flips behavior
before its interacting weights are re-tuned → starts in a fitness valley →
culled before refinement. Big-delta organs (planner) die immediately;
tiny-delta organs (VL/EV) drift neutrally; nothing is ever REFINED. This is
the classic problem that speciation/niche protection (NEAT) and novelty
search address. Carrier injection into an exploit-only ladder can validate
weight tweaks, never architecture. Correct instruments: SHADOW MODE
(measure without competing) and/or a NURSERY population (all-carriers pool
that tunes organ weights internally before graduating a champion).

## The proper planner (adopted specification)

1. **Refactor the production reactive policy into a pure callable**
   `reactive_policy(sim_state, sim_memory)` — CGP field, organs, locks,
   LA vetoes — with cloneable SimMemory. Planning with anything less is
   planning for a different bot.
2. **One authoritative transition function** shared by LA/PC/playbooks,
   mirroring engine order: splits → move (+eject/drag) → clamp → cooldown →
   decay → same-player stabilize → viruses → food (largest-blob order) →
   eating (size order, repeated) → death/respawn. Engine = test oracle.
3. **Search actual future decisions**: H≈12; decision points at ticks
   0/2/5/8; beam 8-12; candidates REGENERATED from simulated state at every
   depth; replan every real tick; event-triggered. Baseline = production
   policy recomputed every simulated tick, never pruned.
4. **Opponent ensemble, not frozen intent**: threats {continue, pursue
   most-vulnerable, intercept, split-strike at best legal moment}; prey
   {continue, flee, juke, wall escape}. Expected value for rewards;
   worst-case/CVaR for death and major bank loss.
5. **Meaningful leaf value** (the 50MB lever): distilled tables for expected
   future mass gain, death probability, bank loss, prey capture, virus
   outcomes — features per the review; value + support + uncertainty per
   bin; low support reduces planner authority. (The calibrated hazard table
   is the risk half, already built and validated; the OPPORTUNITY table is
   its unbuilt twin, mineable from the same 209-replay pipeline.)
6. **LCB acceptance, not arbitrary margin**: accept iff worst-case risk ≤
   baseline's AND advantage lower-confidence-bound > 0; then true argmax
   among qualifiers (fixes order-dependent acceptance).
7. **Structural action identity**: reactive proposal → ALL guards (incl. LA)
   → admissible baseline → only admissible candidates searched → selected
   action returned UNCHANGED. Emergency guards return the full guarded
   baseline, never a hybrid.
8. **Shadow mode before evolution**: planner proposes, reactive executes;
   every proposal counterfactually graded by engine forks (same state, same
   seed, 20-50 ticks, all bots live). Required evidence: positive mean
   counterfactual return, calibrated advantage predictions, reduced
   death/bank-loss, consistency across chassis, paired-seed CI > 0, zero
   governor trips. Only then live, movement first, split later, books
   (EV/VL/split tables) as candidate generators last.

## Build order
contain PC_ON (done 2026-07-17) → reactive-policy refactor → shared
transition + differential tests → shadow H12 search + opponent ensemble →
terminal value distillation → counterfactual grading → live movement →
split → book candidates.

## Build status (2026-07-17, same day)
1. **Reactive-policy refactor — DONE.** `_reactive_core(game, tracker, hunt)`
   extracted verbatim from choose_move in the body; bit-identity proven
   (equiv_test PASS + verify_moves hzws 1400 rounds, 0 mismatches).
2. **Authoritative transition — DONE.** `tools/sim_engine.py` mirrors
   StateMutator.commit_round; differential gate vs the REAL engine:
   **7200/7200 random rounds, 0 mismatches** (blob sets, positions at 1e-9,
   cooldowns, eject vectors, foods, viruses). Getting to zero required
   bit-exact FP association: engine computes `x*(r*r)` not `(x*r)*r` in the
   centroid, precomputes `move_a = ov*(mb/tm)` before `nx*move_a` in
   separation, and its constants are `0.9*0.9` / `0.15*0.15` — the literals
   0.81 / 0.0225 differ in the last bit and the engine compares at exactly
   those boundaries. Known sim divergences (documented): no respawns, no
   food/virus respawn within horizon.
3. **Planner v3 — BUILT (`tools/planner_v3.py`).** Vision-law censored view
   adapter (engine box rule incl. 20·(Σr/12)^0.4 scaling + view-center
   clamp) so the continuation policy IS `_reactive_core`; 4-member opponent
   ensemble (continue / pursue+flee / intercept+flee / split-strike+flee);
   ≤12 structural candidates (baseline + compass + flee-worst / chase-best +
   split variant); acceptance = worst-case not degraded AND advantage LCB>0,
   then argmax mean; selected tuple returned unchanged. Smoke: 20/20 random
   worlds, deterministic, identity holds, ~0.9 s/propose (offline budget).
4. **Counterfactual grader — BUILT (`tools/shadow_grade.py`).** Full-info
   world reconstruction from our replays (foods/viruses by id, ejects
   recovered from movement residuals; split-children seeded dir·1.6·0.82),
   tracker warmed 10 rounds, paired arms (planner vs reactive from the same
   state) simulated H=30 through the bit-exact sim with opponents replaying
   RECORDED moves.
5. **SHADOW VERDICT (2026-07-17) — POSITIVE.** 42 replays, 1050 decision
   points, 871 overrides: paired advantage **+0.68, bootstrap95
   [+0.14, +1.21]** (PLANCORE at the same instrument class: −1.92,
   P(pos)=15%). Deaths 116→96. Threat cells +1.14 CI-positive; calm cells
   neutral (no opportunity model yet — as designed). Calibration r=+0.12
   weak-positive, predictions overestimate 3.7×, but ordering is
   informative: authority dial at pred_adv ≥ 1.0 → +2.74 [+1.07, +4.43]
   (21% of points). Negative cell: mass 15–40 (−1.40). Evidence:
   reports/shadow_v3_20260717.jsonl. Next unlocks, in order: opportunity
   table (calm half of leaf value), mid-mass loss autopsy, then the live
   path (movement first) — all post-freeze, on explicit go.

## Assets already in hand
Calibrated hazard table (+17.8%/+17.0% Brier, leave-us-out validated);
EV/VL solved tables (candidate generators); replay pipeline (endpoint,
harvester, miner, calibration harness); pc_gates battery; ev_harness;
tier2 kit scaffold; this failure analysis.
