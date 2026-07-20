# Decay Rate — SYNCS x Susquehanna Bot Battle 2026

**Team:** Decay Rate (team 35) · Cheng LI (SID 560186806)

**Final bot:** [`bot.py`](bot.py) — the exact file submitted to the competition server.
sha256: `7b7eeb1c6f6ba246f7775b4c12927c53f479c664a3c2831293868975a416beef`

---

## Architecture

`bot.py` is a single self-contained file, but internally it is a **multi-mode agent**: one
evolved "chassis" plus a planning organ, wrapped in a runtime mode-switcher that swaps whole
gene-configurations depending on who is in the room.

### 1. Reactive core — an evolved sensor-mixer

The per-tick decision starts as a weighted sum of hand-designed force fields whose ~300
parameters ("genes", the `CONFIG` dict) were set by evolution, not by hand:

- **Threat/prey/food fields** with evolved falloffs, panic distances and size gates.
- **Virus economy**: virus-feast targeting, split-cycle farming, virus shields, and
  hunter-avoidance when carrying a large bank.
- **Wall/corner handling** with a sticky corner-veto.
- **A 16-node evolved mixing graph** (`ARCH_N*` genes, CGP-style): each node reads game
  sensors (rank, threat pressure, merge-cooldown vulnerability, kill-pulse activity …) and
  multiplies/gates the base steering forces. Evolution rewires the graph structure as well
  as its weights, so strategy composition itself is evolved.
- **Split gating**: candidate splits are checked by an engine-faithful **lookahead veto**
  (`LA_*`) that simulates the split a few ticks forward and vetoes commits that lead to a
  death, a virus hit, or a whiffed attack.

### 2. PL3 — a budgeted rollout planner ("organ")

When a threat is inside range and our mass is below a gene-set ceiling, a small planner
evaluates ~4 candidate headings (continue / flee / two perpendicular escapes) by rolling each
forward under **three adversarial opponent scenarios** (opponent continues, pursues, or
executes a split-strike) on an **engine-exact world model** — a bit-for-bit reimplementation
of the game's transition function (movement, split momentum, merge/attraction physics,
virus explosions, eating order) that was differentially verified against the real engine.
A candidate replaces the reactive heading only if it dominates on worst-case *and*
lower-confidence-bound outcome — the planner is a safety override, not the driver.

Because the competition server bills wall-clock compute and bans bots that exceed a
cumulative cap, every organ is wrapped in a **self-measuring governor**: per-fire deadlines,
a hard cumulative budget, and a graduated throttle that spreads the budget across the whole
match. The bot degrades gracefully to its reactive core rather than ever risking a timeout.

### 3. Multi-mode play — the right genome for the room

The bundle carries several complete gene-configurations and switches between them at runtime:

- At boot it watches the public event feed and **counts distinct elite team ids** (a baked-in
  list of the strongest teams on the leaderboard).
- **0–1 elites sighted** → base genome (evolved in a matching soft-room world).
- **2–3 elites** → a farming chassis evolved for contested rooms: leaderboard rooms with
  several elites are still *feast economies* (fodder and viruses to farm), so the right
  policy is aggressive farming, not survival play.
- **4+ elites** → a champion evolved in an all-elite "finals world" with PL3 enabled.
- **True finals detection** is deliberately separated from room difficulty: the dedicated
  finals genome engages only on unambiguous signals — the bot's own team id changing
  (bracket play) or a hard-coded cutover time — never on room composition alone.

Mode switches apply gene *overlays* (diffs against the base config), so the whole system
ships as one file with no runtime dependencies.

### 4. How it was built (methodology, briefly)

- **Evolution**: a steady-state ladder of 40 persistent genomes playing curated opponent
  rooms shaped to mirror the live meta (measured by a census of real server matches), with
  windowed fitness (mean of last 300 games), periodic cull-and-breed, family-block
  crossover, and hand-seeded "injection" candidates for hypothesis testing (every candidate
  organ was validated by ON-vs-OFF twins on identical chassis before being trusted).
- **Validation**: the engine-exact simulator was proven bit-identical on 7,200 replayed
  states; planner changes were graded on counterfactual replays of real server matches
  before ever shipping; every uploaded artifact passed a gate battery (compile, fold
  equivalence, mode-ladder witnesses, live smoke matches) and its sha256 was logged.
- **Live telemetry**: the bot logs its mode switches and planner statistics to the server
  submission log, which drove several mid-competition fixes (budget retuning for the
  server's ~5x slower CPUs, and the escalation redesign in §3).
