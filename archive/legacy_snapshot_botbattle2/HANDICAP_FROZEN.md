# FROZEN-GENE HANDICAP — PROTECTED POOLS (v2, Chris's design)

v1 post-mortem: open elite competition let free genomes extinguish handicapped
lineages by gen ~30 — a guaranteed outcome (more knobs wins the sprint), which
answered nothing. v2 implements the design as specified: two PROTECTED pools
breeding separately in shared lobbies. The question it answers: what does the
best constrained genome look like, and does its robustness transfer (hard
lobby) where the free genome's overfitting doesn't?

## Mechanics
- Population = 10 free + 10 handicapped. Handicapped share 2 lineage-wide
  frozen sets (5 genes each, anchored at gen51 base) so crossover stays coherent.
- Same lobbies for everyone (handicapped face full pressure, incl. the free).
- Selection is PER POOL: top free breed free, top handicapped breed handicapped.
  Neither pool can extinguish the other. Generation tables tag handicapped
  rows with `H`; each generation prints `pool bests: free=X handicapped=Y gap=Z`.
- PRIMARY READOUT: the gap trajectory across generations, and at milestones the
  best-H vs best-free yardstick comparison (esp. hard lobby).

## Launch
```bash
cd ~/Developer/competition/botbattle && source .venv/bin/activate
pip show agario-kit | grep Version                    # exactly 2026.1.11
grep -c "pool bests" tools/evolve.py                  # MUST be >= 1 (v2 deployed)
cp bots/gen51_organs_off.py bots/my_bot.py
rm -rf evolution evolution_run.log
nohup caffeinate -is python3 tools/evolve.py --league --reset \
  --archetypes bots/champion_gen134.py,bots/gen51_organs_off.py \
  --handicap-frac 0.5 --handicap-n 5 --handicap-lineages 2 \
  --pop 20 --gens 999 --games 12 --parallel 12 > evolution_run.log 2>&1 &
sleep 120; pgrep -f simulation | wc -l
grep -A3 "handicap pools" evolution_run.log          # echo lineage gene sets
```
Identity: `[STUDIO / frozen-pools / base=gen51_organs_off / arch=champ134+gen51 / pools=10F+10H(2x5) / gen=NN / ANALYST]`

## Milestones — every 30 gens
1. `grep "pool bests" evolution_run.log | tail -12`  (the gap trajectory)
2. Top free elite AND top handicapped elite each -> n=20 in the HARD lobby
   (2:elite 2:gen51 2:champ134 2:mimic) and n=20 field lobby.
3. Report: both tables, the gap trajectory, both lineages' frozen gene lists,
   and which lineage the best-H belongs to.
Flag law unchanged: >4 over gen51, curse rule, confirmations.
If a frozen set proves costless (best-H ~ best-free), those genes are
simplification candidates — report that explicitly.
