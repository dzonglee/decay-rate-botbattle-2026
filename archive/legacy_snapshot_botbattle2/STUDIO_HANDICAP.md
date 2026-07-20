# STUDIO — HANDICAPPED OPENING-RACE EVOLUTION

The regularizer bet: populations bred WITH the organ tax (veto + latch enabled)
develop more robust income reflexes; amputating the organs at harvest releases
the compensation as free strength. This produced gen30 (+1.35) and gen51
(+3.31, confirmations-only) by accident; this run does it on purpose, on top
of the opening-race genes and fitness.

Identity line for all reports:
`[STUDIO / handicap-opening / base=opener+organsON / archetypes=mimic_p4+champion_gen134 / gen=NN / ANALYST]`

## STEP 0 — deploy
Copy tools/ and bots/ from the new botbattle.zip over the project directory
(keep .venv and local bots like gen51_organs_off.py).
```bash
cd ~/Developer/competition/botbattle && source .venv/bin/activate
pip show agario-kit | grep Version
```
GATE: must be EXACTLY 2026.1.11. Anything else: STOP and report.

## STEP 1 — build the taxed opening base
```bash
python3 tools/add_opening_genes.py bots/gen51_organs_off.py bots/opener_taxed.py
python3 - <<'EOF'
from pathlib import Path
p = Path('bots/opener_taxed.py'); s = p.read_text()
s = s.replace('"VETO_ENABLED": False', '"VETO_ENABLED": True')
s = s.replace('"LOCK_ENABLED": False', '"LOCK_ENABLED": True')
assert '"VETO_ENABLED": True' in s and '"LOCK_ENABLED": True' in s
p.write_text(s); import ast; ast.parse(s); print("taxed base ready: organs ON")
EOF
timeout 200 simulation --headless --workspace /tmp/taxcheck 4:bots/opener_taxed.py 4:bots/champion_gen134.py
ls -la /tmp/taxcheck/output/*.err | head -2
```
EXPECT: "taxed base ready", match completes, 0-byte error logs.

## STEP 2 — launch
```bash
cp bots/opener_taxed.py bots/my_bot.py
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league --reset \
  --archetypes bots/mimic_p4.py,bots/champion_gen134.py \
  --early-weight 0.5 \
  --pop 20 --gens 999 --games 12 --parallel 12 \
  > evolution_run.log 2>&1 &
sleep 120; pgrep -f simulation | wc -l; ls evolution/variants | head -3
```
EXPECT: sims > 0, gen000 variants present. Organ booleans are FROZEN at True —
every genome trains under the tax. Send Chris the gen 0 table when it prints.

## STEP 3 — milestones (every 30 gens): AMPUTATE, THEN TEST
The tax is for training only. At each milestone:
```bash
cp evolution/variants/genXXX_iYY.py bots/mile_on.py
python3 - <<'EOF'
from pathlib import Path
p = Path('bots/mile_off.py')
s = Path('bots/mile_on.py').read_text()
s = s.replace('"VETO_ENABLED": True', '"VETO_ENABLED": False')
s = s.replace('"LOCK_ENABLED": True', '"LOCK_ENABLED": False')
p.write_text(s); print("amputated copy ready")
EOF
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/mile_off.py 2:bots/gen51_organs_off.py \
  2:bots/mimic_p4.py 1:bots/hungry_shy.py 1:bots/template_bot.py
```
Report the full table + the elite's five opening-gene values + its W_LOCK /
VETO_MARGIN / VETO_SOFT_MASS (the tax-pressure telemetry). Flag ONLY if
mile_off beats gen51_organs_off by >4.0; the flagged run is excluded from any
pooled estimate (winner's-curse rule) — confirmations decide.

## Comparison discipline
The laptop runs the identical experiment WITHOUT the tax. Milestone tables from
both machines meet the same gen51_organs_off yardstick — never compare
in-league masses across machines; only yardstick tables are common currency.
