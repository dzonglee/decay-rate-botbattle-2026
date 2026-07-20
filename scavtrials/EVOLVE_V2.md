# EVOLVE_V2 — champion-seeded evolution under GYM_V2 ecology

## What changed vs tools/evolve.py (minimal audited diff)
1. `--base` flag (default `bots/gen099_i19.py`): the genome source is a
   parameter, not a hardcoded my_bot.py. 44 evolvable genes parsed from
   the live champion.
2. GYM_V2 league defaults: every match seats champion_gen134 +
   mimic_t59 (contested-virus pressure) + 2 rotating prey
   (sluggish, hungry_shy). Populations can no longer evolve empty-room
   feast doctrines that the repaired yardstick will kill.
3. Feast-gene bounds added: FEAST_MIN_MASS (2.7, 60), FEAST_SLOT_SAT
   (0.3, 16), W_VIRUS_FEAST (0, 30). The i19 gate-deletion
   (SLOT_SAT ~0.4) stays reachable — it is champion doctrine now — but
   drift stays bounded and interpretable.
4. State isolated to `evolution_v2/` — never clobbers a v1 tree.
5. **BUG FIX (critical — applies to v1 too).** write_variant's regex
   `-?[0-9.]+` cannot parse scientific notation. Seeding on any
   MATERIALISED genome containing e-notation (gen099_i19 has
   `W_REGROUP: 6.92114e-05`) produced `6.92114e-05e-05` → SyntaxError
   in EVERY variant → every fitness reading collapsed to the rank-9
   sentinel. Fixed: `-?[0-9.]+(?:[eE][+-]?[0-9]+)?`.
   Caught live here: first smoke generation scored every individual
   0.00 mass / 9.000 rank; after the fix, 30.45 / 2.0 best.

## STUDIO ACTION REQUIRED — feastgym-2 audit
`gen51_feast.py` contains NO e-notation literals (checked: 0), so
feastgym-2's variants are probably valid — BUT any gene that drifts
tiny is WRITTEN back in e-notation by `{val:.6g}`, and anything later
re-materialised from such a variant hits the same bug. Audit:
compile-check `evolution/variants/*.py` and scan failures.log for
SyntaxError bursts or rank-9 sentinel generations. Port the one-line
regex fix to the Studio's evolve.py regardless.

## Verified here (engine 2026.1.11, exact-version gated, speed 0.01)
- read_base_config on gen099_i19: 44 evolvable genes ✓
- 1 full league generation, pop 4, GYM_V2 lobby: all variants compile,
  matches parse, fitness spread 0.84–30.45, state.json checkpointed ✓

## Launch (Studio, one owner, detached)
```bash
python3 tools/speed_patch.py set 0.01
nohup python3 tools/evolve_v2.py --pop 16 --gens 30 --games 20 \
  --parallel <calibrated> --league --reset > mining/evov2.log 2>&1 &
```
Milestone crons every 30 gens vs gen099_i19 in GYM_V2; Δ = MASS not
rank; the stopping rule stands: if the top-3 drifted genes all confirm
below flag threshold, evolution retires for the campaign.

## Provenance
Seed bodies hash-verified against the promotion-forensic record:
- gen099_i19.py  fb9fbc78694ae38185286f7094a4831264b3df412ff0f417a562614edb903528
- gen51_feast.py 2db51deb30d7f7ec7675f36a49b942ceb34639b2cba826e30f47ad02dce01ee6
Both exact matches. mimic_t59.py 31a3c6e8… (GYM_V2 kit).

---

## HARNESS LAWS (permanent — added 2026-07-09 after the slot-0 artifact voided Trial 1)

Diagnosis: in headless `tournament.py`, player slot 0 is the visualiser-delegate
slot. It plays full-length (uniform move counts) but starts after the countdown,
missing the opening food rush — a STRUCTURAL, load-independent mass handicap.
Clone probe (8x identical gen51_feast, n=10): slot-0 mass deficit +1.04 sd @p4,
-0.12 sd @p2, +0.88 sd @p1 (non-monotonic => noise-dominated at n=10; NOT a CPU
contention effect). Any single-arrangement battery is confounded: the bot seated
at slot 0 is silently penalised.

LAW 1 — MIRRORED BATTERIES. Every battery is 2x(n/2). In half A the candidate
sits at slots 0-1 and the champion at 2-3; in half B they swap. Archetype/prey
seats stay fixed. Slot bias cancels by construction. Report per-mirror-half AND
pooled tables; a per-half asymmetry that survives the mirror is real signal, not
harness bias.

LAW 2 — BAN-VOID. Any game whose results.json is not a clean SUCCESS with a
`ranking` (i.e. PLAYER_BANNED, non-SUCCESS result_type, or missing/malformed
ranking) is VOIDED from that run's table. Report ban/void counts alongside the
Sigma-wins checksum for every run.
