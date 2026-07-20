# GYM_V2 — contested-virus giant gym (ecology repair)

## Why
The prey-seeded giant gym certified gen099_i19 at +6.12 (n=200, clean,
recomputed from disk) — and the live corpus convicted it in 68 games
(matches 1165–1284): 22.4 vs feast's 25.0 baseline, bust 45.6%,
consumptions collapsed 27→13.3. Mechanism identified: T59 was present in
ALL 68 live lobbies eating 7.1 viruses/match; the gym contained zero
rival virus-competitors. Patient-feast doctrines price out under
contested-virus economics, and the old gym never charged that price.
Ecology validity precedes verdict validity — same law that overturned
the FEAST_11 wrongful conviction, opposite sign.

## The new sparring partner: bots/mimic_t59.py
Crude early-feaster modelled on the decoded SUNMO profile: feasts from
~3 mass (just above the 2.7 gate), no clearance check, no slot
discipline, never split-lunges, minimal flight. Dumb on purpose —
do not tune it to be good; tune it to be T59.

Smoke-tested on engine 2026.1.11 (fresh pip install, exact-version
gated), speed patch 0.01, one headless 8-bot match:
- runs clean; the only stderr across all 8 slots is the identical
  end-of-match "Engine closed the pipe" EOF (benign teardown, present
  on known-good bots too). output/ err files: zero-byte. ✓
- consumed 13 viruses across its 2 copies ≈ 6.5/copy — matches T59's
  live 7.1/match. ✓
- did not win the lobby (champ134 did, with 19 consumptions) — correct;
  it is pressure, not a contender. ✓
- one API fix during build: BlobModel exposes radius only; mass is
  computed as radius**2 (line 42-43). The first draft used b.mass and
  crashed — fixed and re-verified.

## GYM_V2 yardstick spec (replaces prey-seeded giant gym)
```
python3 tools/tournament.py --games 20 --parallel 4 \
  2:bots/<candidate>.py 2:bots/<champion>.py \
  1:bots/champion_gen134.py 1:bots/mimic_t59.py \
  1:bots/sluggish.py 1:bots/hungry_shy.py
```
Change: mimic_t59 replaces oblivious (the most passive prey slot).
Everything else — 3×n=20 batteries, flag >+4, confirm, ship ≥+2.5,
parse-fail voids run, mass not rank, pre-registered verdicts — unchanged.

## Acceptance test (run BEFORE any candidate verdict in GYM_V2)
The repaired gym must reproduce the live ordering it previously missed:
3×n=20, 2:gen51_feast 2:gen099_i19 1:champ134 1:mimic_t59 1:sluggish
1:hungry_shy. Pre-registered expectation: i19's edge shrinks or inverts
vs its old +6.12. If GYM_V2 still shows i19 >> feast, the gym does NOT
model the live field and needs a second density step (e.g. 2:mimic_t59)
before it may issue verdicts. Requires gen51_feast.py and
gen099_i19.py — both still MISSING from the kit; restore from the
Studio before running.

## evolve.py note
If GYM_V2 becomes the evolution reference pool, add mimic_t59 to the
archetype/pool spec so populations evolve under contested-virus pressure
— otherwise evolution keeps proposing empty-room doctrines the yardstick
will now correctly kill (wasted generations, not wrong verdicts).

## Files
- bots/mimic_t59.py   (the sparring partner)
- GYM_V2.md           (this runbook)
Engine gate: exactly 2026.1.11 everywhere, as before.
