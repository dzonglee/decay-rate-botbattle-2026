# Daily workflow

## Morning (10 min)

```bash
# 1. engine bump? (do 04-ENGINE-WATCH.md immediately if yes)
pip index versions agario-kit          # compare against pin in README

# 2. check Discord for rule/scoring announcements

# 3. pull results if the MacBook (or another machine) pushed overnight
cd botbattle && git pull
```

## Running experiments

**Windows (this machine)** — matches run inside WSL automatically:

```powershell
cd C:\Users\zenbook\Documents\botbattle
python tools/make_variant.py bots/my_bot.py -o bots/variants/<name>.py KEY=VALUE
python tools/tournament.py --games 30 --parallel 5 --tag <name> `
    4:bots/my_bot.py 4:bots/variants/<name>.py
```

**macOS** — see `MACBOOK.md` (venv + `AGARIO_SIM` env var, then the same
tournament command with `python3`).

Concurrency limits (learned the hard way):
- Windows/WSL (15 GB): max **10 concurrent matches total** across all
  tournaments — e.g. two runs at `--parallel 5`, or one at 8 plus smoke tests.
  Beyond that WSL freezes and matches hit the 600s timeout (harness skips
  them now, but the games are wasted).
- MacBook: `--parallel 6–8` is safe.

## After every experiment

1. Add a row to `TUNING.md` (date, variant, mean ranks, wins, verdict —
   copy the table format that's there). If the experiment revealed an
   *insight* — an engine fact, a methodology lesson, anything that would
   change a future decision — also write a dated entry in `JOURNAL.md`
   (results go in TUNING.md, understanding goes in JOURNAL.md).
2. If the variant won a 30-game screen, send it to the **ladder** for the
   promotion test (07): ≥50 games, same lineup, mean-rank margin > 0.55
   (≈2×SE). Only ladder winners get merged into `bots/my_bot.py` (for CONFIG
   values just edit the number; for structural variants replace the changed
   functions). Then **re-run one confirmation match vs the template** and
   check for tracebacks:

```bash
wsl -d Ubuntu-24.04 -- bash -c "cd /mnt/c/Users/zenbook/Documents/botbattle && \
  ~/agario-venv/bin/simulation --headless --workspace ~/confirm \
  4:bots/template_bot.py 4:bots/my_bot.py 2>&1 | grep ranking; \
  grep -c Traceback ~/confirm/submission*/io/submission.log | grep -v ':0' ; echo done"
```

3. Commit + push:

```bash
git add -A && git commit -m "merge <name>: <ranks A/B>, <wins> (30 games)" && git push
```

## Interpreting a result table

```
bot                mean rank    sd   mean mass  wins
bots/my_bot.py          3.17  1.83        2.46    24   <- lower rank = better
variants/x.py           5.83  1.91        2.51     6
```

- Gap > 2.0 mean rank: decisive (all July-6 experiments looked like this).
- Gap 0.5–2.0: real but modest — merge if it's a simple CONFIG change,
  re-run at 50 games first if it's structural.
- Gap < 0.5: tie — keep baseline (simpler is better), log it, move on.
- Ignore `mean mass` in mirror A/Bs (both sides suppress it); it only means
  something vs the template.
- `wins` and `mean rank` disagreeing = high variance → re-run at 50 games.

## Submitting

Follow `06-SUBMISSION-CHECKLIST.md` every time — the leaderboard bans bots
that error repeatedly, so never skip the traceback check.
