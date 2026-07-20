
## 2026-07-16 — Sub 1810 (BUNDLE v3) first-look vs sub 1776: composition, not bot
Chris worried new sub's avg is low; old sub ended on a ~7-8 win streak.
Meta analysis thru 30699: sub 1776 (702 games) win 35% rank 2.44 facing
0E14/1E40/2E34/3E+11% (avg oppE 1.44). Sub 1810 (25 games, 13 MINUTES ⚠)
win 28% but MEAN RANK 2.00 — better — while facing 4/24/48/24% (avg oppE
1.92, hardest mix we've seen). Conditional cells (tiny n ⚠): 1E 50%v41%,
3E 33%v17% favor new bot; 2E 8%(1/12)v26% = noise. Streak of 7-8 at p=0.35
over 702 games is expected-by-chance; it was a soft-stretch highlight.
Low avg mass = elite-dense rooms depress all masses + per-sub leaderboard avg
over a tiny window. VERDICT: composition shift (field refilling), no bot
defect signal. Re-judge at n>=150; pull submission.log for [mode] tick lines
(production switch confirmation + sighting-latency data) when available.

## 2026-07-16 — Why 1776's final slice banked more wins (follow-up)
(1) Swap-point selection: sub replaced right after the hot streak -> successor
compared against a peak (regression to the mean). (2) Binomial noise: P(<=11
wins in 37 at true 40%) ~ 10%. (3) Slightly harder deal for 1810: 2.11 elite
encounters/game vs 1.91, 3E+ 32% vs 27%. (4) NOT bans: 0 non-successful games
both subs. Head-to-head placement holds (SUNMO 77%, Banana 64%, QwQ 57%,
spaghetti 50%); soft cell = Bot Battle 29%@14 vs 48% (noise-range, recheck).
WATCH ITEM at n>=150: 2E-cell win% (overlay genes e3r10-j09, gym-trained) vs
1E-cell tracking 1776 — the discriminating test for a gym->live domain gap in
the 2E/3E models.

## 2026-07-16 — Live mode-dwell telemetry (submission.log pull via Hermes)
Chris found the per-match file endpoint (matches/teams/35/matches/{id}/files/
submission.log); pulled our last 80 logs (subs 1810 + 1834, 0 fetch fails),
saved to Studio /tmp/mode_logs/. Sub 1834 (survivor-gate ids): final modes
0E 15% / 1E 38% / 2E 28% / 3E 20%; tick-share 15/42/26/16 (58% of playtime in
overlays — every model earning its seat). 0E commit fired 13/40 (7 of 13 later
escalated out on late elite contact — escape hatch verified live). FIRST ELITE
SIGHTING: median tick 39, p25 16, p75 107, max 599 -> tick-150 commit
threshold VALIDATED (p75 well inside, tail handled by escalate-out); no change
recommended. vs sub 1810 (old ids incl. farmers): 2E-final share dropped
42%->28% and 0E time doubled — survivor-gate ids reclaim farm posture vs
SUNMO/spaghetti, consistent with live avg jump to 33.2. Caveat: dwell assumes
1400-tick games (death not logged) — shares are ceilings.

## 2026-07-16 — Paper-tiger census (soft vs hard rooms, full cache, n=740-2700/cell)
Method: per team, SOFT cell (<=1 elite opp AND >=4 garbage opps) vs HARD cell
(>=2 elite opps), all successful games, tiers by current leaderboard (>22).
PAPER TIGERS: spaghetti (25pp drop, biggest in field; hard 24%/2.88 — the #1
aura is farm-built), SUNMO (21pp -> 18%/3.21), chimken_wingz (23pp ->
18%/2.66). QwQ: weak everywhere (soft 26%, hard 15%/3.40) — not a tiger, just
fodder-economy avg. REAL FIGHTERS by hard-room record: Banana 32%/2.07@1739
(quiet apex), Washed 32%/2.90, us 28%/2.69, BotBattle 27%/2.21, team
26%/2.51, Ninja 22%/2.55 with only an 8pp drop (most composition-proof bot in
the game). IMPLICATIONS: finals threat list = Banana/Washed/BotBattle/team/
Ninja + us; spaghetti+SUNMO likely occupy finals seats as PREY -> validates
FINALS-MIX world design (elites + farmer stand-ins). Revisit QwQ+chimken pins
at Jul-18 build (tallying non-threats costs farm posture). Caveat: aggregates
span submissions/eras (buys sample size); current-sub form can differ.

## 2026-07-16 — EXPERIMENT: #1003 re-uploaded as same-era control vs mode bundles
Chris's read after watching bundles live: mode switching worked mechanically
but did NOT outperform 1003 at 2E/3E cells — elite counts "didn't do
anything". Re-uploaded SHIP_v3_laf1003 (single genome, LA v1m1a1h3, no modes,
NO CUTOVER) to A/B in the current hard meta. Hypotheses for overlay parity:
(1) gym->live domain gap (2E/3E models certified vs BEST_POOL stand-ins, not
real elites); (2) depth asymmetry (base n227+ vs 3E n105 from a 1h world);
machinery itself exonerated (bit-faithful, cheap) — models, not mechanism.
PLAN: at n>=150 run meta_report same-era cells (1003 vs 1834 vs 1810) +
elite head-to-head. If 1003 >= bundle per-cell: Jul-18 final = best base with
EMPTY 0/2/3 overlays + 7E cutover only ("modes only where proven").
WARNING (standing): 1003 has no time gate — MUST be replaced by a
cutover-armed build before Jul 19 14:00Z regardless of verdict.

## 2026-07-16 — CORRECTION: "1E 17%, field-worst" retracted (Chris's challenge)
Chris challenged the 1E cell reading; re-derivation with FIXED elite ids
(bundle fighter set, drift-immune) and full samples: v4 1E = 24%@34, rev4/5
29%@42, and CRUCIALLY #1003's rerun = 29%@14 in the same era vs its own
39%@394 yesterday. The 17%@18 was tier-drift + empty-cell noise (CI 4-41%).
VERDICT: no bot-specific 1E defect — the ERA repriced 1E rooms (contested
returnees replaced pure fodder; whole field's 1E economics degraded). The
"base seat field-worst" framing is overturned; base ≈ 1003 in every
measurable cell. Yesterday's board #2 was era-priced, not lost form. Lesson
reinforced: never compare cells across pulls (tier drift) — fixed-id cells
for cross-era claims; and n=18 cells make no claims at all.

## 2026-07-16 — Fixed-def field cells: 2E fine (3rd), 1E weak-relative, 3E+ = finals alarm
Fixed fighter-set cells (gate ids + us; drift-immune), since 31800, all
current subs: 2E — us 26%@54 = 3rd of 9 (h1-cfeast healthy). 1E — us 23%@52
vs team 59/Washed 46/Banana 40: real RELATIVE gap (consistent 23-29% across
v4/rev4/#1003 -> base-family trait, not v4 defect; earlier 17% artifact
retraction stands, but the over-correction is itself corrected). 3E+ — us
13%@30, 8th of 9 (Ninja 28, team 26): the drift-table "we're best at 3E+"
flipped because fixed-def counts REAL fighters — we beat paper-elite crowds,
lose real-fighter crowds. 3E+ cell = closest live proxy for the finals room
-> strongest evidence for finals-model priority; TRAIN-FINALv2 4-fighter
rooms rehearse exactly this cell. Jul-18 acceptance test for the finals
champion: must project above ~20-25% in fixed-def 3E+ terms vs stand-ins.
