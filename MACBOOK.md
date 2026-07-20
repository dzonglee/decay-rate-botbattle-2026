# Running the tuning batch on the MacBook Pro

The engine runs natively on macOS (it needs Unix FIFOs, which Macs have —
no WSL required). One-time setup:

```bash
git clone https://github.com/dzonglee/botbattle.git
cd botbattle
python3 -m venv ~/agario-venv
~/agario-venv/bin/pip install agario-kit
export AGARIO_SIM=~/agario-venv/bin/simulation   # or: source ~/agario-venv/bin/activate
```

Sanity check (one match, ~2.3 min, should print a `ranking=[...]` line):

```bash
$AGARIO_SIM --headless --workspace /tmp/agario-smoke 4:bots/template_bot.py 4:bots/my_bot.py | grep ranking
```

Run the batch (~2 h at defaults; every experiment is baseline-vs-variant,
30 games, 4v4 mirror):

```bash
./tools/run_batch1.sh                  # defaults: 30 games, 6 parallel
GAMES=50 PAR=8 ./tools/run_batch1.sh   # since engine 2026.1.8 headless is
                                       # unthrottled: whole batch ≈ minutes
```

When batch 1 is done (or overnight), batch 2 has ~23 more experiments
(second-tier CONFIG axes + endgame/velocity-smoothing features + mixed-field
benchmarks vs opponent archetypes), highest-value first, ~4.5 h at defaults:

```bash
./tools/run_batch2.sh                  # same GAMES/PAR knobs, same resume rules
```

## Beyond the batches: workloads that don't just re-confirm the mirror optimum

**Population league** — the local proxy for the leaderboard. Bots are scored
by mean rank across a *diverse* pool (random 8-slot lineups each game), so
generalists win, not mirror specialists. Runs indefinitely; more games =
finer discrimination:

```bash
python3 tools/random_search.py bots/my_bot.py -n 12 --seed 1   # 12 diagonal perturbations
python3 tools/league.py --games 200 --parallel 8 --anchor bots/my_bot.py \
    bots/variants/search/*.py bots/meta/*.py bots/template_bot.py \
  | tee -a results/league.log
```

Anything that beats the anchored champion's mean rank over 100+ shared games
goes to a 50-game head-to-head ladder rung (promotion rule in
instructions/07). Repeat with a new `--seed` and fresh `random_search` crop;
retire variants that rank below the template.

**Vs-archetype exploitation** — tune specifically against each archetype
(`4:champ 4:meta/aggressive` etc.) to find opponent-conditional weaknesses
worth a feature.

Notes:

- The script **resumes**: re-running skips experiments already in
  `results/batch1_results.txt`. To redo one, delete its block from that file.
- Since 2026.1.8 headless matches are CPU-bound (~5 s each) — parallel 8 ≈
  8 busy cores. Still use `caffeinate -i` for long league runs.
- Engine version matters: results are only comparable on the same agario-kit
  version (currently **2026.1.8** — `pip install -U agario-kit` first,
  `pip show agario-kit` to confirm).

## Reporting back

```bash
git add results && git commit -m "batch1 results from macbook" && git push
```

(or just paste the contents of `results/batch1_results.txt` into the chat).

## How to read a result table

```
bot                                       mean rank     sd  mean mass  wins
bots/my_bot.py                                 3.17   1.83       2.46    24
bots/variants/batch1/xyz.py                    5.83   1.91       2.51     6
```

Lower mean rank wins the experiment. Mirror matches suppress mean mass for
both sides — judge by rank and wins. From 30-game runs, treat anything
within ~0.5 mean-rank as a tie; the six experiments run so far were all
decisive (gaps > 2).
