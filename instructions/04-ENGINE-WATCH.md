# Engine watch — what to do when agario-kit updates

Rules may change mid-competition (they changed 1.6→1.7). An unnoticed
mechanics change can silently invalidate the bot's baked-in constants.

## Detect

```bash
pip index versions agario-kit        # newest version vs the pin in README
```

Also watch the SYNCS Discord and the agario-public GitHub repo's commits.

## On every bump — the 20-minute procedure

1. **Diff the source.** The local clone at
   `C:\Users\zenbook\Documents\agario-public` is the engine's repo:

```bash
cd C:\Users\zenbook\Documents\agario-public
git pull
git log --oneline -10                  # find the version-bump commits
git diff <old-version-commit> HEAD -- src/ docs/
```

2. **Check the constants** against the README engine-facts table:
   `src/lib/config/*.py` — ARENA_SIZE, EAT_SIZE_RATIO, speed constants,
   MASS_DECAY_RATE, SPLIT_*, VIRUS_*, MAX_ROUNDS, vision.
3. **Check the mechanics** in `src/engine/state/state_mutator.py`:
   - `_movement_speed` (currently `1.1/(1+0.08r)`, floor 0.25)
   - `_can_consume_virus` (currently `blob.mass > virus.radius * 1.2` —
     note: radius as mass, the famous 1.8 threshold)
   - `_apply_split` (currently splits EVERY blob ≥ mass 2.0, no cooldown)
   - `_resolve_player_eating` (currently radius ratio 1.2 + centre inside)
4. **Update both machines:**

```bash
wsl -d Ubuntu-24.04 -- ~/agario-venv/bin/pip install -U agario-kit   # Windows
~/agario-venv/bin/pip install -U agario-kit                          # MacBook
```

   If you patched TURN_DURATION_SECONDS (03 §6), the upgrade reverts it —
   re-apply if wanted.
5. **Update the docs**: README engine-facts table + the constants block in
   `bots/my_bot.py`'s docstring, and bump the version pin mentioned in
   MACBOOK.md. Commit.
6. **Re-run the sanity baseline** (results only comparable within a version):

```powershell
python tools/tournament.py --games 20 --parallel 5 --tag sanity 4:bots/template_bot.py 4:bots/my_bot.py
```

   Expect ~20/20 wins. A regression here = the update changed something
   the bot depends on; diff harder.

## Red flags that need bot changes, not just doc updates

- EAT_SIZE_RATIO or the eating-geometry change → CONFIG["EAT_RATIO"],
  SAFETY_RATIO, SPLIT_SAFETY_RATIO all need revisiting.
- Speed formula change → THREAT_IGNORE_DIST rationale breaks; rerun that axis.
- Virus consume rule change → VIRUS_MASS constant in my_bot.py.
- New moves (e.g. a mass-eject) → several "impossible" tactics in 03 §7
  become possible; read the new interface models under `src/lib/interface/`.
- Scoring finalised → re-weigh consistency vs aggression (02 §6).
