# Feature roadmap — what to build, with implementation sketches

Build each as a **variant file** (copy `bots/my_bot.py`, modify, A/B it).
Priority order below = expected value ÷ implementation risk. All engine
facts referenced are verified against agario-public source v2026.1.7 —
re-verify after any engine update (04).

## §1 Endgame awareness — TESTED, REJECTED as designed (2026-07-06, 24–6)

The passive version below lost decisively: within a match, ranking is a
mass race to the buzzer, so throttling growth while leading just lets
rivals snowball past. Any revival must keep farming/hunting at full
strength and only veto *splits and marginal fights* while leading. The
"gamble when small late" mirror-image idea (03 §7) is untested and
unaffected. Original design kept for reference:

The API exposes `game.state.round` and `game.state.max_rounds` (1400).
In the last ~150 rounds, holding rank beats growing: chases and splits stop
paying because a failed gamble can't be recovered before the clock ends.

Sketch — in `compute_forces` and `should_split`:

```python
ENDGAME_ROUNDS = 150          # add to CONFIG as "ENDGAME_ROUNDS"
def is_endgame(st):
    return st.max_rounds > 0 and st.round >= st.max_rounds - CONFIG["ENDGAME_ROUNDS"]
```

- In `should_split`: `if is_endgame(st): return False` — never lunge late.
- In `compute_forces`: when endgame AND our total mass > every visible enemy
  blob's mass (visible sizes are the only leaderboard proxy — we can't see
  actual ranks), multiply W_PREY by 0.3 and THREAT_IGNORE_DIST by 1.5:
  farm quietly, take zero fights.
- Tune ENDGAME_ROUNDS (100/150/250) if the first A/B wins.

## §2 Virus shielding when small (half a day)

Engine facts: viruses are static; any blob with mass > 1.8 pops on contact.
When our largest blob's mass ≤ 1.8 we are immune — a virus is a wall that
kills pursuers.

Sketch — add to `compute_forces`, only when
`mass(my_largest) < VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]` and a
threat is within THREAT_IGNORE_DIST:

```python
# steer so the nearest virus sits between us and the nearest threat:
# attract toward the point on the far side of the virus from the threat
vx_, vy_ = nearest_virus.pos
tx_, ty_ = nearest_threat_predicted_pos
ux, uy, _ = unit(vx_ - tx_, vy_ - ty_)          # threat -> virus direction
goal = (vx_ + ux * 2.0, vy_ + uy * 2.0)          # 2 units behind the virus
# add W_VIRUS_SHIELD (try 30) attraction toward goal, capped by distance
```

Careful: don't let this fight the direct flee force — test W_VIRUS_SHIELD
low first. A/B vs an aggressive reconstruction (02 §5), not a mirror; mirror
baselines rarely chase small bots long enough to trigger it.

## §3 Deliberate virus eating when alone (2 hours, speculative)

Consuming a virus grants +1.5 mass (≈ 67 food pellets) but fragments the
blob into up to 16 pieces (18-tick merge cooldown, pieces are tiny and
edible). Rule sketch: if no enemy blob is visible at all, our largest blob
has mass in [2.5, 6], and a virus is nearby — steer onto it instead of
avoiding. The existing virus-repulsion branch already has the geometry;
add an `elif` for the eat case. Risky: reject unless it clearly wins.

## §4 Velocity smoothing (intercept.py lost — this is the prerequisite)

- Velocity smoothing: tracker velocities are single-frame deltas (noisy).
  Keep an EMA: `v = 0.7*v_prev + 0.3*delta`. One-line change in
  `Tracker.update`. Test EMA **on the baseline first** (it feeds the
  LEAD_TICKS extrapolation); only if that wins, retry intercept on top.
- Flee-direction intercept: when cornered (wall within WALL_MARGIN and
  threat behind), flee *perpendicular* to the threat's velocity rather than
  directly away — buys distance because the pursuer must turn.

## §5 Per-blob forces — CLOSED, do not rebuild

perblob (mass-weighted votes) lost 19–11; perblob2 (equal votes) lost 22–8.
The family is a dead end for this engine — one shared direction for all
blobs means per-blob nuance mostly cancels. Don't sink more days into it.

## §6 Fast-clock screening rig — OBSOLETE since engine 2026.1.8

As of 2026.1.8 headless matches no longer sleep between ticks (the engine
only throttles in `--realtime`/GUI mode), so every headless game already
runs at CPU speed (~5 s). No site-packages patching needed, no fast-vs-real
calibration needed. Historical procedure kept below in case they revert it:

Matches run wall-clock (0.1s × 1400 ≈ 2.3 min) regardless of CPU. The engine
reads `TURN_DURATION_SECONDS` from installed config. Patch the **WSL venv
copy only** (never the repo, never the submission):

```bash
wsl -d Ubuntu-24.04 -- bash -c \
  "sed -i 's/^TURN_DURATION_SECONDS = .*/TURN_DURATION_SECONDS = 0.03/' \
   ~/agario-venv/lib/python3.12/site-packages/lib/config/arena.py"
# revert: same command with 0.1
```

~3× faster experiments. Two cautions:
1. At fast clocks, bot compute time per tick matters more — a variant that
   wins at 0.03 must be **confirmed at 0.1** before merging (one 30-game run).
2. Calibrate once: re-run a known-decisive result (e.g. baseline vs
   ignore9.py, expected ~24/6) at 0.03s. If the fast clock reproduces it,
   trust the rig for screening; if not, abandon fast-clock screening.

## §7 Candidate variables from the opening-ceremony plan (sketches)

Ladder each behind a single weight (0 = disabled). Statuses in README.

- **Risk appetite ∝ (mass − floor)**: scale SAFETY_RATIO and
  THREAT_IGNORE_DIST by how much we'd actually lose. Near the 0.81 floor
  death costs ~nothing (respawn in 30 rounds with similar mass) — dare more.
  Sketch: `risk = clamp((total_mass - 0.81) / 4.0, 0, 1)`; interpolate
  W_THREAT between W_THREAT*0.5 (risk=0) and W_THREAT (risk=1).
- **Soft intercept feasibility**: the hard-abandon version lost 26–4. Retry
  as a *weight*: multiply prey force by `1/(1 + t_intercept/HORIZON)` instead
  of dropping the chase — uncatchable prey fades rather than vanishes.
  Requires the intercept_time() helper from bots/variants/intercept.py.
- **Late-game gamble-when-small**: the other half of endgame logic — if in
  the final ~200 rounds our mass is clearly bottom-half of visible blobs,
  raise risk (drop W_THREAT 30%, raise W_PREY 50%): a 6th place and an 8th
  place score nearly the same, a stolen 3rd doesn't.
- **Food memory**: keep a decaying grid (e.g. 12×12 cells) of last-seen food
  density; when nothing is visible, steer to the best-remembered cell instead
  of arena centre. State lives across ticks like Tracker does.
- **Threat velocity**: a bigger blob moving *away* is not a threat — scale
  threat force by `max(0, cos(angle between their velocity and us))`, floor
  0.3 (never fully trust it; they can turn).
- **Crowding penalty**: repulsion from regions where ≥3 enemy blobs sit
  within a 6-unit radius, regardless of sizes — third parties turn won fights
  into losses.

## §8 Ideas considered and rejected — do not rebuild

- **Pushing/feeding viruses onto rivals**: impossible; viruses are static
  and no mass-eject move exists (engine source, state_mutator.py).
- **Waiting at the mass floor to ambush**: mass decays to ~0.81 (starting
  mass) and speed advantage at small size is capped; the drafted scoring
  punishes low ranks accumulated while waiting.
- **Reading the leaderboard from inside a match**: impossible; only visible
  blobs are exposed. Endgame logic (§1) must use visible sizes as the proxy.
