# HYBRID EVOLUTION — launch instructions (Claude Code)

Breed the hybrid architecture (force-field income engine + veto organ + commitment
latch) against the live champion. Goal: find the organ-gene constants that the
hand-set defaults missed. The hybrid's organs are proven to work only *together*
(ablation: latch-only −6, veto-only ~0, both +1.8 mass vs champion at n=60), so
both stay ON — evolution tunes their genes, never their existence.

## Identity line (open every report with this)
`[LAPTOP / hybrid-evo / base=hybrid.py / archetypes=mimic_p4+champion_gen134_vfix / gen=NN]`

## Setup
```bash
cd ~/Developer/competition
rm -rf hybrid-evo && mkdir hybrid-evo && cd hybrid-evo
unzip <path-to-new botbattle.zip>
cd botbattle
python3.12 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip -q && pip install agario-kit -q
python3 -c "from importlib.metadata import version; print('agario-kit', version('agario-kit'))"
```
Report the version. If above 2026.1.11, STOP and report (engine changed).

## Calibrate parallelism (once)
```bash
python3 tools/tournament.py --games 4 --parallel 8 4:bots/template_bot.py 4:bots/hybrid.py
```
If any bot shows "NO PARSED GAMES" or it errors, halve parallel and retry. Use the
working value (call it P, expect 8–15) below.

## Launch
```bash
cp bots/hybrid.py bots/my_bot.py          # evolve.py reads CONFIG from my_bot.py
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league --reset \
  --archetypes bots/mimic_p4.py,bots/champion_gen134_vfix.py \
  --pop 20 --gens 999 --games 12 --parallel P \
  > evolution_run.log 2>&1 &
```
Verify alive after 2 min: `pgrep -f simulation | wc -l` (should be ~P, not 0).
Confirm gen 0 prints within ~20 min: `grep -A22 "generation 0" evolution_run.log`.
The genome has 37 live genes (vs ~30 for non-hybrid runs) — includes W_LOCK,
VETO_MARGIN, VETO_HORIZON, VETO_SOFT_MASS, LOCK_MIN_VALUE, LOCK_TICKS_MAX,
LOCK_ABANDON_T, LOCK_THREAT_BREAK. Booleans VETO_ENABLED/LOCK_ENABLED are frozen ON.

## Milestone tournament — every 30 generations, WITHOUT stopping evolution
Use the COMMON yardstick lobby (identical to the other machine's, for comparability):
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:evolution/variants/genXXX_iYY.py 2:bots/champion_gen134.py \
  2:bots/mimic_p4.py 1:bots/hungry_shy.py 1:bots/template_bot.py
```
(Substitute the current top elite's filename from the latest generation table.)
Send Chris the full table. **Flag only if the elite's mean mass beats
champion_gen134.py by more than 4.0** — smaller gaps are parity (report, no headline).

## Watch and report each milestone
- Top elite's mean_mass vs champion_gen134 (the promotion metric).
- Organ-gene trajectory: `grep -E '"W_LOCK"|"VETO_MARGIN"|"VETO_SOFT_MASS"|"LOCK_ABANDON_T"' evolution/variants/genXXX_iYY.py`
  If W_LOCK trends toward 0 across milestones, evolution is neutralising the organs
  (architecture adds nothing in this lobby). If it stays load-bearing while mass
  climbs, the organs are earning their place. This trajectory IS the architecture
  verdict — report it every milestone.

## Rules
- Change nothing in any .py except via the documented steps.
- Do not stop the evolution to run tournaments — they coexist.
- Any error in a tournament: reduce --parallel, retry once, else report.
