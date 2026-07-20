# CORNER_FIX — stop the decay-siege on uncatchable cornered prey

Observed live by Chris: our big blob camps a corner-tucked prey it is
geometrically too large to reach (walls pin our edge; our center stops
one radius from each wall) and burns 0.2%/tick decay on the whole bank
until it has SHRUNK enough to make contact. Dieting its way to the kill.

Fix (one condition in the prey loop): a prey within CORNER_TUCK of two
walls contributes zero prey force when even blob-overlap is impossible
at our size: closest-approach = hypot(my_r - wdx, my_r - wdy); skip if
closest > my_r + prey_r (minus CORNER_MARGIN conservatism, default 0.5
so we only skip clearly-impossible chases). Validated cases:
  50-mass vs r=1 prey at (0.5,0.5): SKIP (the observed siege)
   4-mass vs same prey:             CHASE (overlap possible - catchable)
  any mass vs wall-but-not-corner:  CHASE (unchanged behavior)

## Step 0 — diagnostic (sizes the wound before/after)
Scan recent replays for the siege signature: our largest blob within
~1.5u of a corner for 200+ consecutive rounds while total mass strictly
decays. Report: incidents, rounds wasted, mass burned per incident.

## Step 1 — build
```bash
python3 tools/corner_patch.py bots/gen51_feast.py bots/gen51_corner.py
```
Expect "55 CONFIG keys"; grep-confirm CORNER_TUCK 1.6, CORNER_MARGIN 0.5.
Add BOUNDS to tools/evolve.py: "CORNER_TUCK": (0.5, 4.0), "CORNER_MARGIN": (-1.0, 3.0)

## Step 2 — trial (FULL ISOLATION: kill sims, never SIGSTOP near tournaments)
3 x n=20 giant gym, tee'd to mining/corner_run<k>.log, Σwins per table:
```bash
python3 tools/tournament.py --games 20 --parallel 6 \
  2:bots/gen51_corner.py 2:bots/gen51_feast.py \
  1:bots/champion_gen134.py 1:bots/oblivious.py 1:bots/sluggish.py 1:bots/hungry_shy.py
```
Any parse failure voids the whole run - rerun it. Report tables + pooled.

## Verdict law (pre-committed)
>+4 pooled -> flag -> 3-run confirmation battery -> ritual -> OneDrive.
+1..+4 -> likely real but gym under-prices it (gym lobbies rarely produce
  the 50-mass-vs-cornered-snack standoff): weigh Step 0's live wound size.
  If live incidents burn 5+ mass/match, ship on corpus evidence.
twin/negative -> shelf; the gym says the condition never fires there,
  and only live A/B could price it. NO SHIP mid-crossover regardless -
  seat changes wait until the #1 pass completes.
