# ALGORITHM.md — Decay Rate (Team 35)
### SYNCS x Susquehanna Bot Battle 2026 — Best Algorithm Submission
**Solo entrant: Chris Li (DzongNru).** Written July 8, day 3 of live competition, while ranked **#1** on the 24-hour-window leaderboard (~18.2 avg final weight; nearest rival ~16.2).

This document describes the bot, but more importantly the **system that builds the bot** — because the bot changed five times in three days and the system is what made each change correct.

---

## 1. The bot on the board: `gen51_feast`

A potential-field agent: every visible object contributes a weighted force
(attraction or repulsion), forces sum, the bot moves along the resultant.
~55 tunable constants ("genes") govern the weights, falloffs, and thresholds.
On top of the field sit a small number of discrete decision layers, each
earned the hard way (see §4):

- **Threat/prey election** with size-ratio gating (engine eat ratio 1.2x),
  panic multipliers, and lead-prediction using opponents' *broadcast intent*
  (the engine leaks every player's direction + split flag via `move_player`;
  we read it for exact heading prediction and split-lunge early warning).
- **Feast posture** (the championship layer): viruses switch from hazard to
  food when `total_mass >= 11` OR `blob_count >= 12`, and no hunter is inside
  the clearance bubble. This compiles three lines of engine source: consume
  gate `mass > 2.7`, grant `+2.25`, shatter `piece_count = 16 - blobs + 1`.
  Below the threshold a shatter is fatal confetti; above it, the tax is a
  business expense that the +2.25/virus income dominates.
- **De-flinched avoidance**: `VIRUS_AVOID_DIST = 1.5` (evolution's ancestors
  used 5.47). On current physics, flinching from viruses costs more expected
  mass than the occasional pop. One gene; +9.32 certified.
- **Bank protection**: split-lunges capped by total mass; when the bot is the
  snowball, it never fragments the snowball for a snack.
- **Fresh-spawn survival mode**, tangential wall-escape, and split-zone
  prophylaxis scaled by bank size.

Live profile (24h window, day 3): **~25 mass/game average, best 97.8,
win rate in own lobbies ~70% of non-bust games.** The doctrine beats both
decoded rivals: the previous #1's safety-first farming (we out-throughput
them 27 vs 17 consumptions/game) and the #4's reckless small-mass feasting
(they pay confetti tax we gate away).

## 2. The core idea: three information sources, one pipeline

Nothing in this campaign came from cleverness alone. Every certified gain
came from one of three measurement loops, welded into a pipeline:

**(a) Engine source-reading.** The engine is open. Reading it yielded the
eat ratio, the speed formula `1.1 - 0.08*radius`, decay 0.2%/tick, split
reach and cooldown, the virus economy, the shatter formula, and the intent
leak. The feast doctrine is not a strategy guess — it is *arithmetic
compiled into an if-statement*. Rule learned: hand-written structure wins
when it encodes verified world-mechanics, and loses when it encodes human
strategy intuition (0-for-6 on intuition organs; 1-for-1 on arithmetic).

**(b) Evolution as instrument, not factory.** Eleven evolution runs shipped
zero bodies after the genome matured — every wholesale elite carried
gym-overfitting (fear deleted, safety ratios floored) and lost to the
champion at the yardstick. But the runs' *gene drift* is a sensitivity
instrument: populations voted "stop flinching" before we built noavoid,
widened hunter-clearance before we hand-set it, and deleted the feast gate
through a bounds loophole — each drift became a purified one-gene candidate
tested on the champion's disciplined genome. Evolution proposes; the
yardstick disposes.

**(c) Corpus decoding.** We download every replay of every match we play
(the API serves our own lobbies) and run automated digests: per-match mass,
placement, consumption timing, mass-and-blob-count at each consumption,
pieces lost within 30 rounds of consuming, killer attribution on busts.
This found the wounds gyms cannot see: the watched-feasting shatter tax
(417 pieces lost in one era), the collapse-after-peak bust anatomy, and the
frame-level decode of the then-#1 team's slot-saturation farming (split to
16 blobs, consume at piece_count=1). We tested their signature move on our
genome: it *lost* by 6.17 — their safety trade pays more in foregone
throughput than it saves in shatter. We kept our doctrine on evidence.

## 3. The verification law (why our numbers are real)

Agar-style outcomes are heavy-tailed; per-match sd ≈ 10 mass. The graveyard
of this competition is teams tuning on noise. Our promotion law:

1. **Yardstick**: every candidate plays the *current champion* in a
   prey-seeded "giant gym" (2:candidate, 2:champion, 1:old-champion,
   3 prey bots) — a lobby ecology matched to the live field, where prey
   conveyors produce the 40-70 mass giants that real lobbies contain.
   All-competent gyms convicted our best doctrine and acquitted paranoia;
   ecology validity is a precondition for verdict validity.
2. **Batteries**: 3 x n=20 minimum, per-run win-checksums, mass (not rank)
   as the currency, any parse failure voids the entire run.
3. **The winner's curse clause**: a flagging run's numbers are *discarded*;
   only fresh confirmation batteries count. Ten flags died this way —
   +9.00 shrank to −2.49, +9 to +1.58 — and two survived to ship. Every
   number in this document is a confirmation number, not a flag number.
4. **Provenance**: results exist only if a disk log backs them. (This law
   was purchased at price: one agent session fabricated a complete,
   plausible, checksum-passing trial report for a battery that never ran.
   Recompute-from-files caught it before it buried a real champion.)
5. **Pre-registered verdicts**: ship thresholds are committed before the
   battery runs. Tonight's final act was *shelving* a +1.58 candidate at
   n=100 because the line was +2.5 — while leading, the burden of proof
   sits on challengers.

## 4. Champion lineage (every link certified)

| Generation | Change | Evidence |
|---|---|---|
| v1 | hand-written potential-field skeleton | — |
| gen134 → gen51 | evolution tunes 50+ genes across 3 runs | league fitness + yardstick |
| organs_off | amputate 5 hand-designed "clever" organs | +certified; intuition organs were dead weight |
| **noavoid** | one gene: VIRUS_AVOID_DIST 5.47→1.5 | source-read + pool-drift; **+9.32, n=60** |
| **feast** | posture if-statement (11 / 12 / 12) | source arithmetic; **+9.33, n=60**, prey-seeded gym |
| (10 challengers) | guarded x2, prep, nogate, early, elites... | all ≤ +2.2 confirmed; champion holds |

The bot on the board is one genome, two source-derived edits, and ten
successful title defenses.

## 5. Findings we contributed back

- **Virus consumption units bug** (engine used `virus.radius` where mass
  belonged; documented threshold 2.7 vs effective 1.8) — reported, fixed
  in engine 2026.1.9.
- **Leaderboard formula verification**: proved the displayed average was
  all-time mean pre-deploy, then independently verified the 24h sliding
  window went live (decreasing match counts; displayed ≈ trailing-24h
  within 0.3), closing the loop with maintainers.
- **Matchmaking starvation evidence**: quantified scheduling asymmetry
  (one rival +42 matches in a window where we received 7).

## 6. Operations (how a solo entrant runs this)

Two AI agents on remote machines execute the loops: an evolution operator
(Mac Studio: runs, batteries, milestone crons with peak-archiving every 5
generations) and a corpus operator (replay pulls, digests, rival tripwires
that alert on co-lobby appearances or consumption-profile era-jumps).
Process laws exist for them too — one owner per machine, detached scripts
over foreground waits, cold-start briefs that trust only the disk — each
law the residue of a specific failure. The human's jobs: audit everything,
read the source, decide the ships, and keep the queue fed, because under a
24h window the crown is re-earned daily.

*The bot is arithmetic. The edge is epistemology.*
