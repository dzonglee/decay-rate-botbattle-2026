# PREY-SEEDED EVOLUTION (field-realistic ecology)

Corpus finding: the live field's victims are GOOD FORAGERS WITH NO SURVIVAL
INSTINCT (median death mass 2.87, established players eaten mid-graze). The
apex team's entire ~19-mass opening edge is harvesting them. Our gyms never
contained such prey, so evolution never learned the harvest. These seats fix that.

## The graded incompetence band
- bots/oblivious.py  — nearest-pellet forager, never evades (the median victim)
- bots/sluggish.py   — same forager, flees only inside 3u (too late vs committed)
- bots/hungry_shy.py — retreat radius 7 (top of the band, hard to catch)

Calibration (verified vs corpus): oblivious reaches ~2.6-3.3 peak and dies
established (r384 @ 2.63) or spawn-band under pressure — matching the live
victim mix (44% spawn-band / 56% established). A champion in the same lobby
harvested to 34 mass: the food chain works.

## Launch (laptop relaunch — replaces the opening-race run)
```bash
cd ~/Developer/competition/botbattle && source .venv/bin/activate
pip show agario-kit | grep Version    # GATE: exactly 2026.1.9
cp bots/gen51_organs_off.py bots/my_bot.py
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league --reset \
  --archetypes bots/champion_gen134.py \
  --prey bots/oblivious.py,bots/sluggish.py,bots/hungry_shy.py \
  --pop 20 --gens 999 --games 12 --parallel 12 > evolution_run.log 2>&1 &
sleep 120; pgrep -f simulation | wc -l; ls evolution/variants | head -3
```
Seats per match: 5 genomes + 1 competent anchor (gen134) + 2 rotating prey.
Identity line: `[LAPTOP / prey-ecology / base=gen51_organs_off / arch=champ134 / prey=3-band / gen=NN / ANALYST]`

## Milestones — every 30 gens, BOTH lobbies, evolution running
1. FIELD lobby (standard yardstick): 2:elite 2:gen51_organs_off 2:mimic_p4
   1:hungry_shy 1:template — n=20. Flag if elite > gen51 by 4.0.
2. HARD lobby (finals rehearsal): 2:elite 2:gen51_organs_off
   2:champion_gen134 2:mimic_p4 — n=20. A candidate promotes ONLY if field-lobby
   gains come without hard-lobby regression (we rent from the weak without
   depending on them).
Winner's-curse rule applies: the flagging run is excluded; confirmations decide.
