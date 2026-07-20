# Submission checklist — run all of it, every time

The leaderboard bans bots that error repeatedly. Ten minutes of checks
protects two weeks of work.

## 1. The file

- [ ] Submitting `bots/my_bot.py` — single self-contained file, no imports
      beyond the engine's `helper.*` / `lib.*` and the stdlib.
- [ ] `python -m py_compile bots/my_bot.py` passes.
- [ ] The crash guard (try/except around the decision path in `main`) is
      still present — look for `traceback.print_exc` in `choose_move`.
- [ ] No leftover debug prints to stdout (stdout is the engine protocol
      channel on some harnesses; stderr is safe).
- [ ] git status clean; the exact submitted content is committed and pushed.

## 2. Behaviour (on the pinned engine version, REAL clock speed)

- [ ] If you ever fast-clocked the venv (03 §6): confirm
      `grep TURN_DURATION ~/agario-venv/.../lib/config/arena.py` says `0.1`.
- [ ] Full match vs templates completes with a ranking and **zero
      tracebacks** in every submission log:

```bash
wsl -d Ubuntu-24.04 -- bash -c "cd /mnt/c/Users/zenbook/Documents/botbattle && \
  ~/agario-venv/bin/simulation --headless --workspace ~/precheck \
  4:bots/template_bot.py 4:bots/my_bot.py 2>&1 | grep ranking; \
  grep -c Traceback ~/precheck/submission*/io/submission.log; echo checked"
```

      (all counts must be 0)
- [ ] Same check in an 8-way mirror (`8:bots/my_bot.py`) — self-interactions
      (regroup, merge, own-blob logic) exercise different code paths.
- [ ] 20-game sanity tournament vs template still shows dominance
      (~expect every win; July-6 baseline was 20/20, mass 20.8 vs 2.8).

## 3. Version hygiene

- [ ] `~/agario-venv/bin/pip show agario-kit` matches the newest published
      version (04) — a bot tested on an older engine may break on theirs.
- [ ] README engine-facts table matches that version.

## 4. After submitting

- [ ] Note submission datetime + commit hash in TUNING.md.
- [ ] Watch your first few leaderboard games for errors/bans.
- [ ] Tag it: `git tag sub-YYYYMMDD && git push --tags` — instant rollback
      target if a later "improvement" regresses.

## Best Algorithm prize (submit near the deadline)

- [ ] ALGORITHM.md is current: does it still describe the actual bot?
      Update after any merged feature (endgame, virus shield, intercept...).
- [ ] It cites the empirical process (TUNING.md row count is evidence —
      "N tournaments, M games" is a strong differentiator).
