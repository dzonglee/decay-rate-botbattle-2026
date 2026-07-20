# ENGINE 2026.1.11 — FEAST PROTOCOL (urgent, update-day)

Source-verified mechanics (engine/state/state_mutator.py):
- gate unchanged: blob.mass > 2.7
- grant: +2.25 total mass per consumption (economy RESURRECTED)
- shatter: piece_count = 16 - current_blob_count + 1
  -> big blob (>= ~11 mass): pieces above the 0.81 floor, re-merge, COMPOUND
  -> slot-saturated player (15-16 blobs): near-zero shatter (hidden mechanic)
  -> small single blob: 16-piece confetti suicide (the .9 risk remains)
Live smoke test: an avoider bot accidentally compounded 22 consumptions into
55.75 final mass — the new economy's ceiling is enormous.

## STEP 1 — engine sync (BOTH machines + resubmit env)
```bash
cd ~/Developer/competition/botbattle && source .venv/bin/activate
pip install --upgrade agario-kit && pip show agario-kit | grep Version   # must be 2026.1.11
```
ALL version gates everywhere are now: exactly 2026.1.11.

## STEP 2 — build the feast candidate (laptop)
```bash
python3 tools/feast_patch.py bots/gen51_organs_off.py bots/gen51_feast.py
timeout 200 simulation --headless --workspace /tmp/fcheck 4:bots/gen51_feast.py 4:bots/champion_gen134.py
ls -la /tmp/fcheck/output/*.err | head -2      # 0-byte
python3 -c "import json;d=json.load(open('/tmp/fcheck/output/game.json'));print('consumptions:',sum(1 for e in d if e['event_type']=='event_virus_consumed'))"
```

## STEP 3 — trial (n=20, mixed lobby, .11 physics)
```bash
python3 tools/tournament.py --games 20 --parallel 8 \
  2:bots/gen51_feast.py 2:bots/gen51_organs_off.py \
  1:bots/mimic_p4.py 1:bots/oblivious.py 1:bots/hungry_shy.py 1:bots/champion_gen134.py
```
Flag law unchanged: >4 flags, flagged run excluded, one confirmation at n=20
promotes (update-day: run the confirmation IMMEDIATELY, no waiting).
Report Sigma-wins and the consumption counts per side if extractable.

## STEP 4 — Studio: relaunch v2 pools on the NEW evolve.py
Same HANDICAP_FROZEN.md launch, but with this zip's tools/ (feast genes LIVE:
W_VIRUS_FOOD, VIRUS_FEAST_CLEAR evolvable; VIRUS_AVOID_DIST bounds now (0.3,8)).
Base: bots/gen51_feast.py if Step 3 promotes, else bots/gen51_organs_off.py.

## NOTES
- Certifications from tonight's mining (g90, gen094_i07) were earned on .9-era
  physics; the finals vault is provisionally stale pending .11 re-checks.
- Rate limit: max 10 submissions per 10 min — the re-upload ritual is fine.
- The in-game leaderboard + match download button may restore corpus access —
  check whether other teams' matches are downloadable again.

## FEAST_PREP addendum (ENGORGIO doctrine, reverse-engineered match 791)
Build: `python3 tools/prep_patch.py bots/gen51_feast.py bots/gen51_prep.py`
Mechanism (live-verified): in feast posture, no hunter within VIRUS_FEAST_CLEAR,
virus within PREP_VIRUS_DIST, blobs < FEAST_SLOT_SAT -> split moves until slot
saturation, then farm at piece_count ~1 (engine: 16 - blobs + 1). New genes:
PREP_MIN_MASS 7.0, PREP_VIRUS_DIST 14.0 (both should join BOUNDS: (4,20) and
(6,30)). Trial: giant gym, 3 x n=20, 2:prep 2:feast 1:champ134 1:obl 1:slug
1:shy. Ship law: >+4 pooled -> ritual -> OneDrive. Twin -> shelf (safety
without income gain isn't worth a seat swap mid-climb).
