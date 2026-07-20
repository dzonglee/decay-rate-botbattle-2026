# Troubleshooting

## A tournament prints `[warn] match ... hung >600s; skipping game`

One-off: harmless (the harness drops that game and continues). Many in a
row: WSL is resource-starved — you exceeded ~10 concurrent matches on
Windows. Kill everything and restart smaller:

```bash
wsl -d Ubuntu-24.04 -- bash -c "pkill -9 -f agario-venv"
```

## `could not parse outcome; skipping game`

The match crashed before printing a result line. Look at the engine log in
that game's workspace (Linux side): `~/.agario_tourney/<tag>_ws<N>/app1.log`
and each `submission<N>/io/submission.log`. Usual causes: a bot file with a
syntax error (run `python -m py_compile bots/...` first — always), or the
engine version changed under you mid-run.

## The bot suddenly plays like a zombie (drifts to centre, never hunts)

That's the crash guard eating an exception every tick. Find it:

```bash
grep -A5 Traceback ~/.agario_tourney/*/submission*/io/submission.log | head -40
```

Fix the bug; the traceback is preserved because the guard prints to stderr.
This is the price of ban-proofing — check for tracebacks after ANY change
(the checklist in 06 does).

## Windows: `simulation` fails with SIGKILL / mkfifo errors

You ran the engine natively on Windows — it can't (needs Unix FIFOs).
Always go through WSL; `tools/tournament.py` does it automatically.
For a single manual match:

```bash
wsl -d Ubuntu-24.04 -- bash -c "cd /mnt/c/Users/zenbook/Documents/botbattle && \
  ~/agario-venv/bin/simulation --headless --workspace ~/manual 4:bots/template_bot.py 4:bots/my_bot.py"
```

The workspace must be on the Linux filesystem (`~/...`), never `/mnt/c/...`
(mkfifo fails on the Windows mount).

## WSL itself is dead / commands hang

```powershell
wsl --shutdown        # then retry; state is disposable (venv survives)
```

If the venv is corrupted: `wsl -d Ubuntu-24.04 -- bash -c "rm -rf ~/agario-venv && python3 -m venv ~/agario-venv && ~/agario-venv/bin/pip install agario-kit"`

## Tournament results look impossible (baseline loses to everything, etc.)

1. Check both bot files compile.
2. Check you didn't edit `bots/my_bot.py` while the run was in flight —
   matches launched after the edit used the new file. Re-run clean.
3. Check the engine version didn't change (`~/agario-venv/bin/pip show agario-kit`).

## The visualiser (watching a game) 

`interactive 7:bots/my_bot.py` needs a GUI and runs the engine locally —
on Windows it has the same FIFO problem. Options: run it on the MacBook
(native), or use WSLg (`wsl -d Ubuntu-24.04 -- ~/agario-venv/bin/interactive ...`
— works if WSLg is enabled, which it is by default on Win11). Watching
games is for building intuition only — decisions still come from
tournaments (rule 1).

## Disk filling up

Workspaces accumulate: `wsl -d Ubuntu-24.04 -- rm -rf "~/.agario_tourney"`
is always safe between runs (quote it or the ~ may expand on the Windows side).
