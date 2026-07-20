# Leaderboard Forensics — SYNCS Bot Battle 2026 (compiled 2026-07-13)

Evidence base: 6,440 match-metadata records (matches 10800–17859, Jul 11 05:03 → Jul 13 05:37 UTC)
via authenticated `/matches/{id}`; ~3,300 locally archived replays (actual masses); direct HTTP
status probes of every missing match ID (all sealed IDs individually verified **403 Forbidden**;
normal matches are world-readable 200).

## Headline finding (REVISED after witnessed-outcome analysis — laundering NOT supported)
Initial analysis suspected "team" (frozen #1, 52.86) of loss-laundering via deliberate
timeouts. **Witnessed-outcome data overturns this**: of sealed matches we participated in,
team was the banned party in ZERO during both their peak and tuned eras (the banned parties
were BK All Day, Pie Guy, QwQ, CheeseQuacks, Bots for Life, Bot1234). The Jul-11 seal
"explosion" decomposes into a server outage (SystemError storms; server-wide throughput
collapsed 214->1 match/hour that afternoon) plus routine weak-bot timeout bans. team's
"suspension holes" were the outage — shared by everyone.

**What actually happened to team:** their final-night submissions were buggy (timing out),
each got CumulativeTimeout-banned (the 4 sealed matches track their re-uploads), and after
sub 1404's ban at 00:37 no human re-uploaded — leaving them permanently unscheduled and
frozen at a 26-game froth score. Their sub 1194's anomalous consistency (54% wins, 1.7%
last-place vs honest controls at 9.1%) remains a genuine outlier, but with zero witnessed
ban events there is no laundering mechanism — the surviving explanation is a legitimately
elite defensive-consistency bot (small 67.8-mass wins, almost never bottom).
**The frozen 52.86 is still an artifact** (26-game sample on a dead sub) and arguably should
be purged from the board — but on the evidence, not fraud.

---

## T1. Loss profile per era — team vs two honest controls (same rooms, same hours)

**Jul 11, sub-1194 era — 1,538 matches**

| team | n | win% | bottom-3% | last% |
|---|---|---|---|---|
| **team** | 287 | **54.4** | **9.1** | **1.7** |
| Decay Rate | 318 | 34.3 | 24.5 | **9.1** |
| Washed CS | 320 | 44.4 | 24.7 | **9.1** |

*The two controls agree to the decimal (9.1% last-place each); team is at 1.7% — one fifth.*

**Jul 12, tuned-down era (sub 1264) — 3,156 matches**

| team | n | win% | bottom-3% | last% |
|---|---|---|---|---|
| **team** | 616 | 43.5 | **17.4** | 5.7 |
| Decay Rate | 721 | 39.5 | 23.4 | 7.2 |
| Washed CS | 620 | 46.0 | 23.7 | 8.7 |

**Jul 12/13 night, pre-ban (subs 1390/1401/1404) — 520 matches**

| team | n | win% | bottom-3% | last% |
|---|---|---|---|---|
| **team** | 108 | 42.6 | **13.9** | 4.6 |
| Decay Rate | 98 | 33.7 | 27.6 | 8.2 |
| Washed CS | 115 | 47.0 | 29.6 | 8.7 |

**Jul 13, after team's ban — 1,031 matches**

| team | n | win% | bottom-3% | last% |
|---|---|---|---|---|
| team | 0 | — | — | — |
| Decay Rate | 183 | 45.4 | 17.5 | 5.5 |
| Washed CS | 190 | 53.7 | 23.2 | 5.8 |

*team's loss profile is a persistent outlier vs two mutually-agreeing controls. With zero
witnessed ban events for their strong subs, the surviving explanation is design (an extreme
defensive-consistency doctrine), not laundering.*

---

## T2. team's ACTUAL masses across the three eras (replay-covered games)

| era | wins n | avg win mass | bottom-3 n | avg b3 mass |
|---|---|---|---|---|
| 1194 era | 7 | **67.8** | 4 | 1.17 |
| 1264 era | 51 | **82.5** | 25 | 0.66 |
| Pre-ban (1390/1401/1404) | 3 | **85.9** | 5 | 0.46 |

*Sub 1194 won small (67.8, barely above our 64.2) but constantly (54%) and almost never
finished bottom — a consistency machine. The later bots traded consistency for bigger wins
(82–86). Note 1194's leaderboard-era average derived from rate x consistency, not harvest size.*

---

## T3. Sealed-match rate and adjacency, era by era

| era | sealed matches | team adj. | us adj. | Washed adj. |
|---|---|---|---|---|
| Before sub 1194 existed | **0** | — | — | — |
| Peak (1194) | **194 in 1,538 (12.6%)** | 1.05× | 0.80× | 0.79× |
| Tuned (1264) | 57 in 3,156 (1.8%) | **1.80×** | **1.00×** | 1.34× |
| Pre-ban | 4 in ~520 | (n too small for ratios) | | |
| After team's ban | **0 in 1,031+** | — | — | — |

*(REVISED: witnessed outcomes decompose the peak-era seals into a server outage (SystemError
storms, server throughput fell to 1-4 matches/hour that afternoon) + weak-bot timeout bans
(BK All Day, Pie Guy, QwQ...). team was the banned party in ZERO witnessed sealed matches in
both eras. The density/era correlation was coincidence; adjacency ratios at these densities
are not attribution.)*

---

## T4. The Jul-11 afternoon holes — RESOLVED as a server outage

team's gaps of **22 → 49 → 55 → 179 → 61 → 61 minutes** (12:34 → 19:37) initially looked like
suspensions. Server-wide throughput for the same hours: 214 → 95 → 22 → 17 → **1 → 2 → 4 → 3**
→ 82 → 215 matches/hour — the whole competition stalled, and our own history logs SystemError
storms at the same timestamps. The holes were everyone's.

---

## T5. Final-night cascade: seal → re-upload, four times, then ban

| time (Jul 12/13 UTC) | event |
|---|---|
| 21:59 | sub **1390** uploaded |
| 22:38 | **SEALED match 16439** |
| 23:13 | **SEALED match 16554** |
| 23:52 | sub **1401** uploaded (lives 7 minutes, 13 games) |
| 00:00:47 | **SEALED match 16707** |
| 00:07 | sub **1404** uploaded |
| 00:37:37 | **SEALED match 16829** |
| 00:37+ | **permanent freeze — zero matches scheduled since** (1,031+ matches and counting) |

*Reading (revised): their final-night bots were buggy — each upload accrued timeout bans
(sealed matches), was replaced, and after 1404's ban nobody re-uploaded. Dead sub + absent
operator = frozen at a 26-game froth score. Same mechanism as CheeseQuacks' morning freeze,
never repaired.*

---

## T6. team's games/hour — the freeze (Jul 12 22h → Jul 13 03h)

| hour | 19 | 20 | 21 | 22 | 23 | 00 | 01 | 02 | 03 |
|---|---|---|---|---|---|---|---|---|---|
| team | 42 | 43 | 45 | 44 | 35 | 26 | **0** | **0** | **0** |
| (all other teams) | 32–51 | 39–51 | 35–46 | 35–49 | 32–44 | 36–41 | 43–53 | 34–46 | 33–52 |

---

## T7. Exonerations

**CheeseQuacks' peak (sub 1379, Jul 12 18:33 → Jul 13 02:57) vs controls — same 1,703 matches:**

| team | n | win% | last% | bottom-2% | bottom-3% |
|---|---|---|---|---|---|
| CheeseQuacks (peak) | 353 | 37.1 | **5.7** | 13.0 | 20.1 |
| Decay Rate | 328 | 39.6 | **5.2** | 14.0 | 23.5 |
| Washed CS | 334 | 49.4 | 8.4 | 17.1 | 24.6 |

*CQ's peak last-place rate is statistically identical to the honest control's; zero seals in
their peak window. Their #2 was EARNED — via the field's best harvest engine:*

| team (same era) | wins replayed | avg win mass | bottom-3 replayed | avg b3 mass |
|---|---|---|---|---|
| CheeseQuacks (1379) | 18 | **99.6** | 16 | 0.75 |
| Washed CS | 26 | 74.0 | 18 | 0.56 |
| Decay Rate | 125 | 64.2 | 77 | 0.66 |

*Their collapse was self-inflicted: 15 uploads in 2 days; at 03:01 they replaced the 99.6-per-win
bot with an old 8%-win prototype and never reverted (99+ games later: rank 27, avg 5.86).*

**Banana:** earlier suspicion withdrawn — whole-window seal adjacency was an artifact of the
seal-dense 1194 era; era-split shows nothing anomalous. Their low bottom-3 (8–16% across 15
subs) is a genuine bust-avoidant bot at modest win size (~64).

**Decay Rate (us):** clean control in every era (adjacency 0.80–1.00×), win rate elite
(45.4% on Jul 13, best current form in the field), win size 62–64 — the improvement target.

---

## Strategic implications
- Live race is effectively Washed (37.1) vs us (35.4); the frozen 52.86 above both is a corpse.
- Everyone's bottom-3 mass ≈ 0.5–1.2 (dead is dead): leaderboard averages are made ENTIRELY of
  win-rate × win-size. Our win rate matches anyone; our win size (62–64) trails Washed (74–94)
  and CQ-peak (99.6). CQ's peak is the existence proof: ~100-mass wins at a normal 5.7%
  last-place rate are achievable — the feast-gene campaign targets exactly this.
- Ship discipline stays: +2.5 over the live-ship anchor at n≥100 or hold. The board is a
  graveyard of teams that died by upload.
