# COMPETENCE PROFILER — build & ablation trial

Mechanism (from four corpus decompositions): the apex team's ~4-point edge is
relentless pursuit of prey that never evades; our force election rationally
declines those chases. Winning behaviour = CONDITIONAL PERSISTENCE — commit
against the oblivious, stay cowardly against the competent. The profiler reads
every opponent's broadcast intent and scores a per-player flee-ratio
(competence 0..1, prior 0.5); low-competence prey gets magnetism
(W_NAIVE_HUNT) and a persistence lock (W_NAIVE_LOCK). Both weights reach 0 —
the mechanism can be vetoed honestly by evolution or ablation.

Classifier ground truth (container, PROF_DEBUG=1): champions read 0.80-0.88
(competent), oblivious reads 0.25, observations accumulate fastest exactly when
we approach a target (we ARE its nearby threat) — the profile is freshest at
the moment of decision.

## STEP 1 — build (on the machine holding gen51_organs_off)
```bash
cd ~/Developer/competition/botbattle && source .venv/bin/activate
python3 tools/add_profiler.py bots/gen51_organs_off.py bots/profiler.py
python3 - <<'PY'
from pathlib import Path
s = Path('bots/profiler.py').read_text()
s = s.replace('"W_NAIVE_HUNT": 2.5', '"W_NAIVE_HUNT": 0.0')
s = s.replace('"W_NAIVE_LOCK": 20.0', '"W_NAIVE_LOCK": 0.0')
Path('bots/profiler_off.py').write_text(s); print("ablation twin ready")
PY
timeout 200 simulation --headless --workspace /tmp/profcheck 4:bots/profiler.py 4:bots/champion_gen134.py
ls -la /tmp/profcheck/output/*.err | head -2   # expect 0-byte errors
```
If the patcher raises AssertionError (anchor missing), STOP and send the error.

## STEP 2 — the ablation trial (mixed-competence lobby; n=20 each)
The lobby MUST contain both prey and competents — discrimination only shows
where there is something to discriminate:
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/profiler.py 2:bots/gen51_organs_off.py \
  1:bots/oblivious.py 1:bots/sluggish.py 1:bots/mimic_p4.py 1:bots/champion_gen134.py
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/profiler_off.py 2:bots/gen51_organs_off.py \
  1:bots/oblivious.py 1:bots/sluggish.py 1:bots/mimic_p4.py 1:bots/champion_gen134.py
```
Report both tables. The comparison is profiler vs profiler_off (same genome,
mechanism on/off) AND each vs gen51 in-lobby.

## STEP 3 — hard-lobby no-regression (n=20)
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/profiler.py 2:bots/gen51_organs_off.py 2:bots/champion_gen134.py 2:bots/mimic_p4.py
```
The profiler must NOT regress vs gen51 here (all-competent room: the naive
machinery should correctly go silent — that is the test).

## Verdict law (pre-committed)
- profiler beats profiler_off by >4 AND no hard-lobby regression -> flag;
  winner's-curse confirmations; then Chris decides on live audition.
- Parity everywhere -> mechanism convicted at hand-set genes; genes join the
  genome for the NEXT evolution reset (all weights evolvable, 0 reachable) and
  the population gets the final vote.
- profiler_off wins -> mechanism convicted outright; archive.
