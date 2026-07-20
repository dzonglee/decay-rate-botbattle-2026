# Algorithm — SYNCS Bot Battle 2026 entry (champion: v0)

A reactive potential-field agent with velocity-prediction interception,
hard-gated split attacks, and weights tuned empirically by automated
parallel self-play tournaments — and defended by them: eleven consecutive
A/Bs (30–50 games) rejected every proposed change, including two of our
own "obvious improvements" (§6).

Version history:
- **v0** (2026-07-06): handover baseline + virus-threshold fix (engine
  uses virus radius as its mass — read from source) + crash guard.
  Eleven mirror A/Bs (30-50 games each) defended without a loss.
- **v0.1** (2026-07-06): endgame rank protection + EMA velocity smoothing.
  **Rejected in validation 27–3**; component isolation convicted both
  halves individually (§6). Champion remains v0.

## 1. Potential fields (the core)

Every visible object contributes a force vector on the bot; the move
direction each tick is simply the weighted sum. This turns "strategy" into a
small set of continuous, individually-tunable weights instead of brittle
if/else state machines, and degrades gracefully in situations we never
anticipated — there is always a defined direction.

| Source | Direction | Magnitude |
|---|---|---|
| Food pellet | attract | `W_FOOD / d^1.0` — shallow falloff makes *clusters* outweigh the single nearest pellet |
| Edible enemy blob | attract | `W_PREY · mass / d^1.5` — bigger meals pull harder |
| Dangerous enemy blob | repel | `W_THREAT · mass / d^2.0` — steep falloff: close threats dominate everything |
| Virus (when we'd pop) | repel | `W_VIRUS / d^2` inside 3.5 units |
| Arena wall | repel | linear ramp inside a 4-unit margin (walls kill by cornering) |
| Own centroid (when split & threatened) | attract | regroup so fragments aren't picked off |

Three shaping rules encode the game's physics:

- **Threat panic zone** — inside 4 units the threat force is multiplied 4×:
  escaping a nearby larger blob outranks any feeding opportunity.
- **Threat ignore distance** — beyond ~7 units, larger blobs are *ignored
  entirely*. Speed falls with radius (`1.1/(1+0.08r)`, verified in engine
  source), so bigger hunters close distance slowly enough to keep farming.
  Without this the bot flees visible giants forever and starves at the mass
  floor — fear and greed are the two failure modes, and every weight trades
  between them. A/Bs confirmed 7.0 beats both 5.5 and 9.0.
- **Eat/threat classification is per-blob, with a safety margin** — the engine
  requires 1.2× radius to eat; we treat anything within 12% of edible as a
  threat too (`SAFETY_RATIO 1.12`), because both blobs are moving and mass
  decays.

## 2. Velocity-prediction interception

A per-enemy-blob tracker differences positions between consecutive ticks to
estimate velocity, keyed by `(player_id, blob_id)` and dropped when a blob
leaves vision (so respawns don't inherit stale velocity). All attraction and
repulsion is computed against the enemy's position extrapolated `LEAD_TICKS`
ahead — we chase where prey *will be* and flee where a hunter *will be*,
which matters when speeds differ by a factor of 4 between sizes.

Notably, the velocity estimate is a raw single-frame delta *on purpose*:
EMA smoothing (α=0.3) was tried and lost 27–3 — at 0.1s ticks in a
contact-heavy arena, response latency costs more than estimation noise.
Reactivity is the signal, not the noise (§6).

## 3. Split-safety gating

Splitting is the highest-risk action in the game: it halves our eat
threshold and creates 18 ticks of vulnerability. The split lunge (~8.9 units
of reach from eject speed 1.6 with drag 0.82) fires only when *all* of:

1. predicted prey position within `SPLIT_MAX_RANGE` (6 units);
2. each post-split half ≥ 1.35× the prey's radius — a deliberate buffer over
   the engine's 1.2× so the lunge still eats after decay and prey growth;
3. no threat within 9 units;
4. we'd stay ≤ 4 blobs (fragmentation is death in an 8-player arena);
5. the current net force already points at the prey (dot > 0.7) — we never
   turn *and* split in the same decision.

## 4. Empirical weight tuning

Every constant above lives in a single CONFIG dict. Changes are never judged
by eye: a variant generator (`tools/make_variant.py`) produces a bot file
differing in exactly one CONFIG value, and a parallel headless tournament
harness (`tools/tournament.py`) plays ≥30 mixed 4v4 matches per comparison,
reporting mean rank, rank variance, mean final mass, and wins. Weights are
hill-climbed one axis at a time against the current best. The engine itself
was read (agario-public source) to pin exact mechanics rather than guessing —
e.g. the virus pop threshold is `blob.mass > 1.8` because the engine uses the
virus *radius* (1.5) as its mass, and viruses are static so shield play is
possible but push play is not.

## 5. Robustness

Repeated runtime errors get a bot banned from the leaderboard, so the
decision path is wrapped: any exception logs a traceback to stderr (captured
in per-slot submission logs) and falls back to a legal drift toward the
arena centre — the bot can lose a tick of cleverness, never the match.

## 6. Negative results (the method working as intended)

Eleven A/Bs (30-50 games), eleven rejections — each one bought information:

| Rejected idea | Score | Lesson encoded |
|---|---|---|
| More fear / more greed (THREAT_IGNORE_DIST ±) | 24–6, 22–8 | the fear/greed weight is a sharp optimum |
| Longer split lunges | 24–6 | reach ≠ profit; overextension dies |
| Per-blob force computation (2 weightings) | 19–11, 22–8 | one shared movement direction cancels per-blob nuance |
| True intercept geometry + chase abandon | 26–4 | hard cutoffs discard too much; steady simple leads win |
| EMA velocity smoothing | 27–3 | reactivity beats noise-filtering at 0.1s ticks |
| Endgame passivity while leading | 24–6 | in-match rank is a mass race to the buzzer; passivity never protects a lead |
| Hunt harder / fear less (W_PREY↑, W_THREAT↓) | 39–11, 40–10 (50 games) | the greed side of both core weights is also closed |

The champion's weights are not assumed good — they are the survivors of
every alternative we could construct, and the rejects are archived
(`bots/variants/`, TUNING.md) so no idea gets rebuilt twice.
