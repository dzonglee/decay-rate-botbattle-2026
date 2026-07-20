# HYBRID TRIALS — geometry organs vs the champion (laptop runbook)

The hybrid = champion_gen134_vfix + two grafted organs, each behind a boolean gene:
- **VETO_ENABLED** — constitutional veto: directions entering any kill envelope
  (contact / closing-speed chase / cooldown-gated 8.9u lunge disc) cannot win
  the per-tick election; the bot takes the closest legal direction instead.
- **LOCK_ENABLED** — commitment latch: one interceptable prey is locked and
  pulled toward (W_LOCK) until eaten, infeasible, timed out, or a threat closes.

My container's preliminary 6-game read: hybrid 5.0 mass vs vfix 14.1 —
**losing with my default organ genes.** Same pattern as every hand-set
mechanism this week: structure plausible, numbers wrong. Your laptop's job is
the real verdict at proper sample size, organ by organ.

## Setup
```bash
cd ~/Developer/competition/botbattle   # deploy this zip first (AGENT.md step 1)
source .venv/bin/activate
```

## Trial 1 — both organs, defaults (n=20, ~15 min)
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/hybrid.py 2:bots/champion_gen134_vfix.py \
  2:bots/mimic_p4.py 1:bots/hungry_shy.py 1:bots/template_bot.py
```

## Trial 2 — ablation: latch only (edit hybrid.py CONFIG: VETO_ENABLED False)
## Trial 3 — ablation: veto only  (LOCK_ENABLED False, VETO_ENABLED True)
Make each edit with sed so it's reversible:
```bash
sed -i '' 's/"VETO_ENABLED": True/"VETO_ENABLED": False/' bots/hybrid.py   # macOS sed
# run Trial 1's command again; then flip back and flip the other flag
```

## Reading the results (mean mass, hybrid vs champion, n=20 → noise ±~2.5)
- Hybrid wins by >2.5 in any configuration → send Chris the table: promotion trial.
- One organ helps, the other hurts → keep the winner's flag on, ship that.
- Both lose in all configs → organs' *genes* go to the evolution: run
  `evolve.py --league --reset` with hybrid.py as base
  (`cp bots/hybrid.py bots/my_bot.py` first) and archetypes
  `bots/mimic_p4.py,bots/champion_gen134_vfix.py` — let the league find the
  organ constants my hand-guessing missed. Structure by trial, numbers by breeding.

## Organ genes worth watching if evolution takes over
VETO_MARGIN, VETO_HORIZON, VETO_SOFT_MASS, LOCK_MIN_VALUE, LOCK_TICKS_MAX,
LOCK_ABANDON_T, W_LOCK, LOCK_THREAT_BREAK — all evolvable; booleans are frozen.
