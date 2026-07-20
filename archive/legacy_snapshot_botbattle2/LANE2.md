# LANE 2 — OPENING-RACE EVOLUTION (launch runbook)

Goal: breed for the live field's actual win condition. Corpus analysis of all
leaderboard replays shows matches are winner-take-all snowballs decided in the
first ~400 rounds: the apex team (42% conversion) reaches mass 3 by ~r383,
makes its first kill by ~r334, and averages 34.7 kills/match; we (16%
conversion) run ~100 rounds behind at every stage. This run adds opening-race
genes to our best genome and prices the race directly in the fitness function.

Identity line for all reports:
`[MACHINE / opening-race / base=gen51_organs_off+opening / archetypes=mimic_p4+champion_gen134 / gen=NN / ANALYST]`

## STEP 0 — retire the old run on this machine (if any)
```bash
cd ~/Developer/competition/botbattle
pkill -f evolve.py; sleep 3; pkill -f simulation
mkdir -p archive && cp evolution/state.json archive/$(date +%m%d)_state.json 2>/dev/null; cp evolution_run.log archive/$(date +%m%d)_run.log 2>/dev/null
```

## STEP 1 — deploy the new zip (tools changed: evolve.py, add_opening_genes.py, gym_funnel.py)
Copy `tools/` and any missing `bots/` files from the new botbattle.zip over the
current directory. Keep the existing .venv and the existing bots/gen51_organs_off.py.
```bash
source .venv/bin/activate
python3 -c "from importlib.metadata import version; print('agario-kit', version('agario-kit'))"
```
If the version is above 2026.1.11, STOP and report.

## STEP 2 — gym-realism audit (10 min, run BEFORE launching)
```bash
python3 tools/gym_funnel.py bots/gen51_organs_off.py 8
```
Send Chris the output. (This measures whether the gym reproduces the live
opening race; the run launches regardless, but this number tells us how much
to trust in-league fitness.)

## STEP 3 — build the opening-race base bot
```bash
python3 tools/add_opening_genes.py bots/gen51_organs_off.py bots/opener.py
python3 -c "import ast; ast.parse(open('bots/opener.py').read()); print('opener syntax OK')"
timeout 200 simulation --headless --workspace /tmp/opener_check 4:bots/opener.py 4:bots/champion_gen134.py
ls -la /tmp/opener_check/output/*.err | head -2
```
EXPECT: "opening genes injected", syntax OK, match completes, error logs 0 bytes.
If the patcher raises an AssertionError (anchor missing), STOP and send Chris
the full error — the local gen51 file differs from expected structure.

## STEP 4 — launch
```bash
cp bots/opener.py bots/my_bot.py
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league --reset \
  --archetypes bots/mimic_p4.py,bots/champion_gen134.py \
  --early-weight 0.5 \
  --pop 20 --gens 999 --games 12 --parallel 12 \
  > evolution_run.log 2>&1 &
```
Fitness = final mass + 0.5 x mass at round 400. The five opening genes
(OPEN_ROUNDS, OPEN_GREED, OPEN_FEAR, EDGE_HUNT_RATIO, W_EDGE_HUNT) are
evolvable with physical clamps; organ booleans stay False.

## STEP 5 — verify (2 min wait)
```bash
sleep 120; pgrep -f simulation | wc -l; ls evolution/variants | head -3
```
EXPECT: process count > 0, gen000 variant files present. Gen 0 table prints in
~20 min; send it to Chris.

## STEP 6 — milestones (every 30 gens, do not stop the evolution)
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:evolution/variants/genXXX_iYY.py 2:bots/gen51_organs_off.py \
  2:bots/mimic_p4.py 1:bots/hungry_shy.py 1:bots/template_bot.py
```
Yardstick is now gen51_organs_off (our strongest). Report the full table plus
the elite's five opening-gene values. Flag ONLY if the elite beats
gen51_organs_off by >4.0 — and remember the first flagged run is excluded from
any pooled estimate (winner's-curse rule); confirmations decide.
