# AGENT RUNBOOK — Bot Battle (7 July, afternoon)

You are operating Chris's Mac. Follow steps IN ORDER. After each step, compare
the output to "EXPECT". If it does not match, STOP and send Chris the full
terminal output. Do not improvise. Do not skip verification steps.

Everything you need is in the file `botbattle.zip` Chris sent with this note.
Put it in ~/Downloads first.

## STEP 0 — stop any old runs (safe even if none exist)
```bash
pkill -f evolve.py ; pkill -f simulation ; sleep 3
pgrep -f "evolve.py|simulation" | wc -l
```
EXPECT: `0`

## STEP 1 — fresh deployment
```bash
mkdir -p ~/Developer/competition
cd ~/Developer/competition
mv botbattle botbattle_old_$(date +%H%M) 2>/dev/null
unzip -o ~/Downloads/botbattle.zip
cd botbattle
ls bots tools
```
EXPECT: bots shows `champion_v1.py hungry_shy.py mimic_p4.py my_bot.py predator.py predator_greedy.py template_bot.py`; tools shows `autopsy.py evolve.py speed_patch.py tournament.py`.

## STEP 2 — python environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install agario-kit -q
python3 -c "from importlib.metadata import version; print(version('agario-kit'))"
```
EXPECT: `2026.1.9` or higher. Include the exact number in your report.

## STEP 3 — sanity check (~4 minutes)
```bash
python3 tools/tournament.py --games 2 --parallel 2 4:bots/template_bot.py 4:bots/my_bot.py
```
EXPECT (engine 2026.1.9 economy): `bots/my_bot.py` mean mass ABOVE `template_bot.py`. Absolute numbers are small now (3-10 is normal). Only STOP if my_bot is BELOW template.

## STEP 4 — launch the league evolution (the main job)
```bash
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league \
  --archetypes bots/mimic_p4.py,bots/hungry_shy.py \
  --pop 20 --gens 999 --games 12 --parallel 12 \
  > evolution_run.log 2>&1 &
echo launched
```
EXPECT: `launched`

## STEP 5 — verify it is alive (wait 2 minutes first)
```bash
sleep 120
pgrep -f simulation | wc -l
ls evolution/variants | head -3
```
EXPECT: first number BETWEEN 5 AND 12 (not 0). Second shows files like
`gen000_i00.py`. If the number is 0, run `tail -30 evolution_run.log`, STOP,
and send Chris that output.

## STEP 6 — first generation check (wait ~15 minutes, then run)
```bash
grep -A 22 "generation 0" evolution_run.log | head -24
```
EXPECT: a table of lines like `* i03  mean_mass=  61.65  mean_rank=1.500`.
Numbers will differ; what matters is the table EXISTS and mean_mass values
are not all 0.00. If all are 0.00, STOP and send `cat evolution/failures.log`.

## STEP 7 — report to Chris
Send him:
1. The version number from STEP 2
2. The table from STEP 3
3. The generation-0 table from STEP 6
4. The output of: `pgrep -f simulation | wc -l`

## STANDING RULES
- Leave the machine plugged in. Do not close the Terminal window's session
  owner account; the run survives window-close (nohup) but not logout/shutdown.
- Do NOT run `pip install --upgrade` on anything after setup.
- Do NOT edit any .py file.
- If ANYTHING asks for a password or confirmation you weren't told about, STOP.
- To stop everything later (only if Chris says so):
  `pkill -f evolve.py && pkill -f simulation`
