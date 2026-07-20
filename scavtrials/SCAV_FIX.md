# SCAV_FIX — close the fragment-scavenger blind spot (+ GYM_V3)

## The wound (decoded, era I2)
T1 = fragment scavenger. 54 kills across matches 1294/1318/1319: 89%
land >20 rounds after our last virus consumption, against 9–15-blob
confetti of ~0.7-mass pieces, at T1 mass 1.4–7. It waits out the
shatter and eats the re-merge, split-growing mid-engagement (1→6
blobs). Leaderboard avg 7.0 — built to farm shatterers, not to win.

## The blind spot (source-read)
Threat classification tests `b.radius >= my_smallest * SAFETY_RATIO`.
Correct AFTER the shatter; but the FEAST DECISION runs before it, when
my_smallest is the big blob. Clearance is judged against a body the bot
is about to trade away. Temporal, not spatial.

## The fix (compiled arithmetic — one condition)
piece_count = 16 − blobs + 1 (engine source), so post-shatter piece
radius is known pre-consumption: sqrt(total_mass / pieces). Any enemy
blob within SCAV_CLEAR whose radius ≥ piece_radius × EAT_RATIO ×
SCAV_MARGIN sets hunter_near → feast suppressed, virus handled by the
pre-existing hazard branch. New genes: SCAV_CLEAR 9.0 (≈ lunge reach),
SCAV_MARGIN 1.0. Both evolvable; the fix is vetoable by bounds.

Arithmetic validation (against observed T1 masses):
- 10-mass shatter vs T1 at 3.0 or 1.4 mass → VETO (the I2 kill pattern)
- 40-mass shatter vs T1 at 3.0 → FEAST (big pieces outclass T1;
  healthy feast economy untouched)
- 40-mass shatter vs 8-mass scavenger → VETO (correctly paranoid)

## Bodies built (both syntax-checked, smoke-run clean on 2026.1.11)
- bots/gen51_scav.py   c5e1c0eb…  (feast + SCAV_FIX — the trial lead)
- bots/gen099_scav.py  4a1fb01e…  (i19 + SCAV_FIX — bench candidate)
- tools/scav_patch.py  (applies to any feast-family bot)

## mimic_t1 (2e5489c0…) — the predator the gym never had
Compiled from the kill anatomy: flees only close larger blobs, scores
targets by closeness × owner's blob count (confetti outranks lone
blobs), split-grows into fragments once established, never feasts.
Smoke (1 match, 8-bot lobby): runs clean, survives, 3 kills, 0 virus
consumptions (correct — scavenger, not feaster). HONEST CAVEAT: its
fragment-preference did not express at n=1 because the lobby's
scav-patched champions barely produced small shatters near it; verify
doctrine expression in the acceptance battery vs UNPATCHED i19, which
shatters small constantly.

## GYM_V3 yardstick (supersedes GYM_V2)
```
python3 tools/tournament.py --games 20 --parallel 4 \
  2:bots/<candidate>.py 2:bots/<champion>.py \
  1:bots/mimic_t59.py 1:bots/mimic_t1.py \
  1:bots/sluggish.py 1:bots/hungry_shy.py
```
champ134's seat goes to mimic_t1: both live predator classes (virus
competitor + fragment scavenger) are now priced into every verdict.
evolve_v2 launch flag: --archetypes bots/mimic_t59.py,bots/mimic_t1.py

## Trials (Studio, in order, pre-registered)
1. GYM_V3 self-validation: 1×n=20, 2:gen099_i19 (UNPATCHED)
   2:gen51_feast + V3 seats. EXPECT: mimic_t1 kills concentrate on i19;
   i19's gym numbers degrade toward its live 12.4-class form. If the
   gym cannot reproduce the live wound, it may not certify the cure.
2. Scav trial: 3×n=20 GYM_V3, 2:gen51_scav vs 2:gen51_feast. Ship law
   unchanged: flag >+4 → confirm; ship ≥+2.5. A twin (±1) ALSO ships
   here as pure insurance: the patch only fires when a scavenger is
   present, costs nothing in scavenger-free lobbies, and the live field
   contains T1 in most of our lobbies.
3. Bench: 3×n=20 GYM_V3, 2:gen099_scav vs 2:gen51_scav — does patched
   i19 reclaim its edge once its shatters stop being donations?

## Engine status (checked against PyPI, this session)
INSTALLED 2026.1.11 = LATEST published. NO engine update required for
evolve_v2 or anything above. Keep the exact-version gate at 2026.1.11;
re-check on any Discord engine announcement, per standing law.

## Provenance
Patch inputs hash-verified champions (fb9fbc78… / 2db51deb…). All
smoke evidence generated on a fresh pip install of 2026.1.11 at
speed 0.01.

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
