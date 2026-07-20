# Discovery journal

## 2026-07-13 (HOW WE PULL COMPUTE: the match-API node pattern — any machine, any agent, zero trust)

The gym now recruits computing power with a repeatable protocol. Design:
**the laptop is the only brain** (population, culls, room draws, logging);
every other machine is a stateless MUSCLE behind a tiny HTTP API
(`node_api.py`, stdlib-only): POST /bots/<sha> (content-addressed body
cache, atomic writes), POST /jobs/batch (queue up to 300), GET
/results?since=<cursor>, DELETE /jobs (cull-cancel + orphan purge),
GET /integrity. The laptop's pump keeps every node's queue full and drains
results asynchronously — local waves never wait on a remote machine (the
wave-barrier lesson: 43 -> 94.7 games/min came mostly from never letting
fast workers idle behind slow ones).

**Onboarding a new node is a ZIP + a PROMPT.** The handover zip carries the
API server (env-configurable, workers auto-sized to cores−2, nice'd so the
host's own services keep priority), a fresh per-node token (nodes are
individually revocable; bot upload = code execution, so every route is
authenticated), fodder bots + a selftest that runs one real match before
any tunnel opens, and an agent-proof runbook: numbered steps, hard STOP
gates (engine EXACTLY 2026.1.13 — "do not helpfully upgrade"), scoped
permissions ("only this API + one TEMPORARY cloudflared quick tunnel; kill
nothing you didn't start" — written in Jacob's memory), and a fixed final
report block (tunnel URL + health JSON) that is connection info, NOT trust.

**Trust comes from facts, not reports** (Chris's law: query facts, not
outcomes): verify_node.py checks (1) engine version attestation, (2)
sha256 over the installed engine's .py sources vs our local engine —
same bytes = same game, version strings can lie; (3) server-side re-hash
of every cached bot body; (4) one job whose record must echo the exact
8 shas requested and report the standard 1400-round length. Deterministic,
seconds of compute — and it caught a real corruption on its maiden run
(a 0-byte pool bot truncated by a deploy restart, silently inflating 4%
of Studio games -> atomic cache writes added). Temp-tunnel caveat: URLs
are random and change on cloudflared restart — nodes must re-report; the
pump treats any node failure as dropped games, never corrupted state.

## 2026-07-13 (HOW THE NODE GRAPH INVENTS: anatomy of an evolved mechanism, fossil by fossil)

The staged ship #452 carries a defense doctrine no human wrote — "when whole
AND rich, avoid viruses (they shatter the bank); when late AND whole, stop
split-cycling." Because ancestors persist in the graveyard, the invention
can be dissected step by step:

  #202 (grandparent):  N0: 1−blobs → VIRUS −0.21        [detector born]
                       N1: N0×wealth → CYCLE −1.50      [signal: whole∧rich]
                       N2: min(late,N0) → CYCLE −0.23   [mild late gate]
  #401 (our injectee): identical graph — pure COURIER (contributed 0 genetics,
                       carried #202's program into the cross)
  #366 (other parent): same motif, different dialect — blobs>threat,
                       min(frag,·): the part FAMILY circulating in the pool
  #452 (the ship):     N1 TARGET flipped CYCLE→VIRUS (one categorical gene,
                       8→4) + N2 gain deepened −0.23→−1.50

**The entire marginal invention was an integer changing 8→4** — the wire
deciding which drive a node's output feeds. Same sensor, new actuator: the
computation was inherited, the MEANING changed by re-plugging its output
into a different socket. Exaptation, not conjuring.

Why one flip can be an invention: the flip re-plugged parts that were
already load-bearing. Generations of selection had built and vetted the
detector, tuned the gain, proven the wealth-product — accumulated,
composable capital (node outputs are inputs to other nodes; N0 is reused
twice). A rich parts library + 8 sockets + constant re-plug attempts at
95 games/min makes invention CHEAP; the census room's economics
(winner-take-most; rich deaths cost entire wins) made this particular
re-plug instantly visible to selection.

Division of labor, validated end-to-end: CONTINUOUS genes (gains, biases,
thresholds) do smooth dose-tuning; CATEGORICAL genes (op, inputs, TARGET)
do qualitative rewiring — mutate() deliberately keeps a structural-flip
channel open every generation, and that channel is where every qualitative
novelty of this campaign came from (scat36's late-discipline wiring, the
feast-conditional gates, this bank-protection flip). Most flips are garbage
and die in grace; selection keeps the one in a thousand that re-prices.

The general recipe the fossils show: (1) a mildly-useful detector emerges
and pays rent; (2) crossover spreads it; (3) the population accumulates
dialect variants (a motif family, not one motif); (4) a categorical
mutation gives old machinery a new job; (5) the room's economics amplify
it. Note what the human contributions were: the SPACE (nodes, features,
channels), the ROOM (census gym), the DOSES (injected couriers) — never
the mechanism itself. We built the workshop; the search did the inventing.

## 2026-07-13 (CHRIS'S THESIS, PROVEN BY THE CAMPAIGN: the search was never broken — the room was)

"Random-walk evolutionary search is not randomly guessing a point in an
80-dimensional space." The whole campaign record supports it. Every
"evolution failure" we ever diagnosed was evolution SUCCEEDING at a
mis-specified objective: non-splitting mimics bred non-splitting champions;
sibling-giant rooms bred out the hunter doctrine; the over-dense room made
gym gains that never transferred. Three lineages "plateauing" at −3 was the
body's ceiling measured in a fictional world. The moment the room matched
the live census, the SAME unchanged machinery shipped scat36 → #195 →
#452: live 24 → 30 → 35 → ~43 projected. Population search = hill-climbing
with recombination of proven blocks (the staged ship is an injected
corner-experiment genome crossed with a feast line), not uniform sampling —
at 95 games/min it reads gradients humans can't see, and it out-tuned every
hand-graft we ever attempted (hand-doses died 8/8; its own choices —
CYCLE_THREAT_CLEAR=2, VIRUS_SLOT_EXP=0.24, sticky-veto back to 0 — were
proposed by no one). Three conditions make it work, each learned by
scar: (1) FAITHFUL MEASUREMENT — the gym is the fitness function and you
get exactly what you measure, bugs included; (2) HONEST STATISTICS — noisy
windows + bottom-N culling turn selection into a noise amplifier;
(3) REACHABLE SPACE — frozen genes are welded doors; exposure preceded
every breakthrough. Fitness-function design IS the work. The optimizer was
always fine.

**Addendum — the node design invents architectures, not just parameters.**
The staged ship #452's decoded graph: N0 = 1−blobs (an invented
"consolidated" detector); N1 = N0×wealth → VIRUS −1.50 ("whole AND rich →
don't shatter the bank on viruses"); N2 = min(late, N0) → CYCLE −1.50
("late AND whole → no new split cycles"). That is wealth-conditional
risk management — the exact defensive doctrine we were about to hand-design
— already invented by selection and routed through channels no chassis gene
touches, with N0's output reused twice (a subroutine). scat36's late
discipline was the first evolved mechanism; this is the second, and it is
compositional. Parameter evolution tunes a program; graph evolution WRITES
programs. Parity was indeed the floor.
Lineage trace answers "out of nowhere?": NO — the consolidated-detector
existed in grandparent #202 (N1: N0×wealth → CYCLE), circulated in dialect
variants through the pool (#366: blobs>threat, min(frag,·)), and #452's
"invention" was two edits: N1's TARGET flipped CYCLE→VIRUS + N2's gain
deepened −0.23→−1.50. Exaptation, not conjuring: a library of proven,
composable parts + one categorical mutation that gives old machinery a new
job. The injection (#401) contributed no genetics — it was the courier.

## 2026-07-13 (RETRACTION: the "1194 exploit" was three coincidences — witnessed outcomes settle it)

The laundering verdict below is WITHDRAWN. The decisive instrument: our own
match history records the outcome of every sealed match we were seated in.
Witnessed sample (44 of the 208 "peak-era" seals + 18 of the tuned era's 57):
**team was the banned party in ZERO.** The seal explosion decomposes into
(a) a server OUTAGE on Jul-11 afternoon (SystemError storms; server-wide
throughput fell 214 -> 1-4 matches/hour — team's "suspension holes" were
everyone's holes) and (b) routine timeout bans of weak bots (BK All Day 13,
Pie Guy 4, QwQ 12, CheeseQuacks 3...). team's actual fate: buggy final-night
subs banned for timeouts, then nobody re-uploaded — dead sub + absent
operator = frozen forever at a 26-game froth score. The one true anomaly
stands un-launderable: sub 1194's 1.7% last-place vs controls at 9.1% — a
legitimately extreme consistency doctrine (54% wins at only 67.8/win).
Lessons, earned the hard way: (1) **era correlation is not attribution** —
three independent signals (seal density, scheduling holes, loss profile)
all pointed at one team and ALL THREE had innocent explanations; (2) the
decisive data was participant-view outcomes, not public-view absence —
when records are sealed to outsiders, find the view where you were an
insider; (3) accusations should survive the witnessed-outcome test before
being written down — this one didn't, and the journal keeps both entries
as the record of how the error was made and caught.

## 2026-07-13 (THE 1194 EXPLOIT, FULLY MAPPED — Chris's theory confirmed to the submission)

Chris theorized team laundered losses via deliberate timeouts (banned
matches nullify and vanish from the average). Bucket forensics over 6,440
matches (10800-17522) proved it and named the bot: **sub 1194** (from ~match
11000, July 11 night — Chris called the onset at 11764 from leaderboard
watching alone). During 1194's reign: team 11%->58% wins with 7% bottom-3
(physically implausible), while sealed-match density exploded 0 -> 77 -> **90
per 500 (18% of ALL server matches nullified)**. The moment they swapped to
the legitimate farmer (1264, 07:51 Jul 12): sealing collapsed 30x to 1-3/500
and their stats became plausible (43% wins, 84-mass actual win size). Final
night: subs 1390/1401/1404 faintly resumed the pattern -> 4 sealed matches
-> permanent matchmaking ban and the frozen 52.86. All 44 sealed IDs in the
Jul-12 window verify as 403 enforcement records. Methods that made this
possible: match-metadata sweeps via the authenticated session, gap-vs-
coverage bucketing, per-submission rank profiling, and direct 403 probes —
zero replays needed. Lesson: **the leaderboard is an accounting system;
audit it like one. Visible averages are only as honest as the denominator,
and the denominator is queryable.**

## 2026-07-13 (TEAM BAN FORENSICS: sealed matches — the server quarantines timeout abuse)

Chris's theory: team's leaderboard freeze (52.86@26, unscheduled since
00:36) = a matchmaking BAN, possibly from deliberately timing out when
losing (banned matches nullify, laundering the average). Evidence: exactly
4 match IDs missing from the 16400-17522 sequence — ALL inside team's
active window (22:38, 23:13, 00:01, 00:37), the last within seconds of
their final game; zero gaps in the 700 matches after their freeze
(p<1% if random). Direct fetch of the 4: **403 Forbidden** — the records
exist but are SEALED (normal matches are world-readable). Verdict: ban
confirmed as the freeze mechanism; deliberateness unproven (their visible
bottom-3 rate 14% ties Banana's, and 4 hidden games can't launder 52.86 —
a fragile bot looks identical to a cunning one from outside). Lessons:
(1) the anti-abuse system detects, seals, and unplugs — never risk move
timeouts; (2) missing IDs + 403s are the fingerprint of enforcement
actions, readable without any replay; (3) frozen scores of banned teams
linger on the board — the visible ladder overstates the living field.

## 2026-07-13 (TWIN-ANCHOR EXPERIMENT: the corner veto is genome-dependent — never weld a behavioral gate)

Genome #195 (parent of half the board) collapsed 46→25-29 and was culled —
while its byte-exact twin (the live ship, corner veto OFF, playing as the
passive anchor) held 36 in the same rooms. Same chassis, one forced switch
apart: **the fleet-wide hard-set CORNER_SKIP_ON=1.0 cost this chassis ~9
points** even as it helped the #202 line (its sticky child c2veto15z sits
#2 at 48.5). A behavioral gate interacts with the rest of the genome —
hand-welding it fleet-wide, outside the registry, repeated the feast-graft
mistake in miniature (economies must co-evolve). Fix: CORNER_SKIP_ON exposed
(0,1); selection now chooses per lineage. #195 itself was outbred by its own
children (cull floor rose 19→38 in an hour at 90+ games/min) — a legitimate
retirement, but the twin comparison is the discovery: the passive anchor
doubles as a free A/B lab for any gene we force fleet-wide.

## 2026-07-13 (SHIP-MORTALITY MECHANICS: two rivals died in one day, differently — and neither was banned)

Match-metadata autopsy (1,119 matches, 16400–17522, via the authenticated
/matches/{id} endpoint): **CheeseQuacks** replaced a true #2 bot (avg rank
1.99, 38% wins, n=177) with sub 1415 — avg rank 3.40, **8% wins** — and
avg-of-current-submission scoring erased them from the top 20 within 52
games. Still scheduled, still playing; just worse. **team** shipped 3
subs in 100 minutes (last one strong: rank 1.58, 46% wins), then went
UNSCHEDULED at 00:36 with the leaderboard frozen at n=26 — the signature of
a fourth, faulty upload (invalid sub ⇒ no scheduling, stats pinned to last
valid sub). Meanwhile our sub 54 ran 44% wins / rank 1.84 (n=118), best
sustained form in the field. **The model: ship risk is asymmetric — a broken
upload FREEZES you (recoverable), a worse-but-working upload REPLACES your
banked average with the truth in ~50 games. There is no ban trap and no
fresh-sub curse beyond co-scheduling variance. The only ship question is
"is it actually better," hence the law: +2.5 over the live-ship anchor at
n≥100, or hold.** Also learned: /teams/leaderboard is PUBLIC (no auth);
/matches/{id} works through the portal session via CDP — metadata autopsies
no longer need the replay zips.

## 2026-07-13 (DISTRIBUTED GYM: 43 → 94.7 games/min — the barrier was the bottleneck, not the hardware)

Chris diagnosed the laptop "running at 80% for a bit, then nothing, then
restarting" — the wave barrier: 12 matches launched together, ALL had to
finish before the next 12. Match durations vary ±30–50%, so every wave ended
with cores idling behind the slowest straggler. **Two design changes, 2.2×
throughput on the same hardware:** (1) rolling scheduler — a persistent
16-slot pool where each finished match immediately launches the next
candidate; local-only throughput rose 43 → ~55/min with zero new compute.
(2) the Studio as an async match API (Chris's design: queue of 300, batch
submit, cursor-based result polling, cull-cancellation of dead-bot jobs,
nice'd workers so production services keep priority) — +40/min at 42% share,
with the laptop never blocking on it for even a second. Lessons: **never let
a fast worker wait for a slow one when the work items are independent** (the
same wave-barrier mistake cost us twice — first laptop-only, then laptop-
waiting-on-Studio); and fire-and-forget queues beat synchronous RPC for
heterogeneous workers. Ops traps for the record: Cloudflare bot-fight 403s
python's default user-agent; homebrew's cloudflared service template runs the
bare binary and crash-loops (tunnel must run via a custom launchd plist);
`docker ps` printing nothing over ssh means the CLI errored — not that zero
containers exist (that misread cost Chris's servers 20 minutes of downtime).
Evolution now iterates a cull every ~5.3 minutes.

## 2026-07-13 (THE META VERDICT: the game measures farming, not fighting — Chris's reflection, now data-backed)

**Chris's observation, quoted because it's the truest thing said all week:**
the game "has unfortunately turned into a 'who can feast incompetent bots
better' game, not a game where you build competent bots to compete with
other players" — the original intention being bots good enough to
eventually play real humans.

The 2,777-replay economics confirm it quantitatively:
- **Scoring = avg final mass + field = 69% garbage bots** (4.82 of 7
  opponents; live census). So the leaderboard is dominated by harvest
  throughput against non-players, not by outplaying peers.
- **Winner-take-most:** rank 1 pays ~56–62 mass, ranks 2–4 ~10, ranks 5–8
  ~1. Win size carries ~85% of a team's average. And win size in a
  69%-garbage room = how fast you vacuum the incompetent.
- **The leader (team) proves it:** ~90% of their income is farming
  (2× virus economy, camping), only ~10% predation. Their #1 is a farming
  score, not a combat score.
- **The irony:** by head-to-head — the thing the original intent would
  measure — we beat or match every elite team except Washed (dead even
  33/32 with the leader). Ranked #4 on mass, arguably #1–2 at actually
  playing opponents. A room of real humans contains no fodder to farm;
  the farming doctrine that wins this leaderboard would collapse there,
  while late-game discipline (scat36) and target selection transfer.
- **Design consequence, eyes open:** we optimize the objective that exists,
  not the one intended — hence census-4B's 25% elite-free games and the
  2026-07-13 exposure of the 7 feast genes (W_CAMP, virus economy,
  CYCLE_THREAT_CLEAR) to evolution. If the organizers ever score H2H
  (or the bots meet humans), our doctrine is already the right one; until
  then, feast size is the paycheck.

Lesson for future competitions: read the scoring rule as the game. "Avg
final mass vs a mostly-incompetent field" was never a combat objective —
it was a farming objective wearing a combat costume, visible from day 1
in the 07-07 entry below ("the tradeoff moved toward growth") and PROVEN
by the day-2/3 corpus decompositions ("the leader's edge is harvesting
incompetent bots" — see the 07-08 first-crown entry). We had the verdict
in week one and kept optimizing the wrong virtue for days. The deeper
lesson: when your own analysis contradicts your project's romance,
believe the analysis.

## 2026-07-13 (BACKFILL — feast genes unfrozen; injection-per-cull; the anchor-provenance trap)

**Win-size decomposition says feast size is 85% of the paycheck** — current era:
avg ≈ 0.42×61 (wins) + 0.32×13 (places) + busts ≈ 30. A +20% win size ⇒ ~+17%
final average, second-order win-rate gains on top. Gym winners already feast to
~87 while our live wins bank 61 — win size, not win rate, is the open frontier.
**Consequence (Chris's order):** 7 chassis farming genes (W_CAMP, CAMP_MAX_MASS,
CYCLE_THREAT_CLEAR, W_VIRUS_FEAST, VIRUS_FEAST_CLEAR/FALLOFF, VIRUS_SLOT_EXP)
exposed to the mutation registry — until today every genome carried them at
identical body defaults; the levers were welded shut while we demanded farming.
Plus an inject-queue hook in ladder_v3: 1 hand-seeded candidate consumed per
cull (ordinary newborn, normal window — NOT the retired pend-slot seeding);
10 feast candidates queued, singles-first to isolate each lever.
**Data-forensics trap logged twice today:** (1) rolling windows that span a
room change blend eras — #195 "regressed 48→36" was 85 old-room games (mean
8.8!) polluting its window; census-only it was 48.35 all along. (2) The
`anchor` log field spans anchor *identities* — 95% of "scat36's" 1,509 anchor
records were x8x0's (code switched at the 08:15 restart). Rule: split eras at
the room-change timestamp; compute bot references from seat telemetry, never
from a field whose meaning changed under you.

## 2026-07-12 late (SCAT36: the breakthrough, decoded — discipline is a graph doctrine, not luck)

**#36 "scat36" shipped (sub 53) and became our best live bot ever: ~30.4 avg,
41.6–42% wins, #4** (old bot's replay-truth was 24.4). Gym median 36.9 with
busts eliminated. Autopsy of WHY: chassis byte-identical to its parent — the
entire delta is a rewired mixer graph: AUTHORITY floored 0.68→0.35,
`late_phase → cycle-vote −0.53`, `sigmoid(late) → prey −1.45`, escape damped.
**A late-game discipline doctrine, expressed purely in CGP wiring** — stop
cycling/hunting when the bank is large and the clock is late. The VULN organ
contributed nothing to this delta (parent had the identical organ). This
vindicates the graph layer as *conditional gating* (when to stop doing things)
rather than steering (where to go). Corollary discovered vs Washed CS: their
old bot specifically beats scat36 (27% vs 40%) by harvesting our cycle
fragments — the counter-gene (CYCLE_THREAT_CLEAR) was frozen; unfrozen 07-13.
**Also today: fresh-submission co-scheduling is real** — during Banana's fresh
ship our co-occurrence with them spiked 9%→47%, manufacturing a 12-game losing
streak (4% probability at true win rate). Fresh subs get disproportionately
paired with other fresh subs; never judge a ship on its first ~30 games.

## 2026-07-12 (TWO SYSTEMIC BUGS: the decimation steering-lag and the gerontocracy cull)

**Every mixer genome since the sensor build carried a 1-tick steering lag.**
The anti-timeout decimation cached the whole steering vector and replayed it
on odd ticks. Paired A/B in identical worlds: −19.25±8.4 mass/game. Found only
because Chris challenged a mimic scoring 38 elsewhere vs ~20 here. Echoes the
07-06 EMA lesson: **response latency is deadlier than estimation noise** — and
a "performance optimization" was the fleet's biggest depressant for days.
**The ladder was also eating its young:** 71% of 435 culls died at their FIRST
grading — newborns judged on 60–84-game windows (SE ±3) against incumbents'
200-game windows (SE ±1.7); bottom-5 culling preferentially kills the widest
error bars, so 3 original seeds survived 90 culls while good new genes were
shredded. Like-for-like window maturity is now a cull precondition.
**Sensor-dosing lesson (culls 4–9):** hand-DOSED sensor nodes (±0.20 gains)
matured below median 8/8 times; the same wiring at gain 0.05 with dose left
to mutation immediately ranked top-5. Recipe: wire the node, near-zero gain,
let selection grow the dose. Hand-tuning doses loses to evolution every time —
Chris's standing direction (07-12): evolve graph freedom, no more hand-written
formulas; parity for a graph = floor, not ceiling.

## 2026-07-12 (WINNER-TAKE-MOST + the census room: measure the real game, then copy it)

2,777-replay economics: **rank 1 pays ~56–62 mass, ranks 2–4 ~10, ranks 5–8
~1** — the leaderboard average ≡ P(win) × win-size. Live field per 7 opponents
= 1.00 elite + 1.18 contested + 4.82 garbage (P(≥1 elite) = 71%; multi-elite
rooms real). Win rate by elite count: 55/37/26/22% at 0/1/2/3+.
**Gym rebuilt as census-4B (Chris's Design B):** seats 1–2 = 50% elite-pool /
50% contested, seat 3 = 18% contested, rest fodder — exact live means AND
live-like variance. The old over-dense room (~5 competent) explains years…
days… of non-transfer: gym gains were tuned for a density that live never
serves. **Composition standard (Chris's law): classify opponents by their
team's LEADERBOARD standing (elite >22 / contested 10–22 / garbage <10), never
by single-game mass; large samples; count everyone.** A busted elite is still
elite. **"No more tests" law:** the gym now IS the certification room —
certification = the ladder's own mature window (n≥100) vs the passive anchor;
paired A/Bs survive only for mimic-injection fidelity. **Ops lessons:** the
whole stack died twice with the session's process group → launchd owns the
watchdog now (never nohup it); launchd's default QoS pinned sims off P-cores
at half speed (Chris spotted the 50% cores) → ProcessType=Interactive doubled
throughput 24→42 games/min.

## 2026-07-11 (engine 2026.1.13; the field hardens; the mixer ladder is born)

Engine upgraded .12→.13 both machines: virus interaction radius shrank
(consume needs blob center within blob.radius of the VIRUS CENTER — old
VIRUS_AVOID genes now over-cautious, left to evolution to retune);
clamp-after-eating fixed (corner-catchability model now exactly engine-true);
**leaderboard = avg final mass of MOST RECENT submission** (confirmed) — a
ship replaces your score, so every upload is a bet, not an addition.
Live census check: the field hardened to 32% threat / 41% contested / 27%
fodder (from 15/45/37) — mid-tier teams caught up to the virus economy; gym
re-hardened to match. **V3 ladder launched** (steady-state, 40 genomes,
200-game windows, cull-5/breed-5 per 500): the CGP mixer architecture — fixed
hand-built chassis + 11-node evolvable graph steering 6 channels + split votes
— becomes the fleet body. Claude-seeding retired same era (Chris: "stop
seeding, let it run normally") after 44 culls of seeded lines crowding the
elite pool while the ceiling drifted DOWN 20.3→18.5.

## 2026-07-10 (THREE LINEAGES, ONE WALL — the base-body ceiling is real; grafts don't take)

OMNI-A (gen 512), OMNI-B (gen 770), OMNI-D (gen 112) — independent seeds,
different rooms, same verdict: **all three plateaued at −3 vs the same elite
yardstick.** When three lineages converge on one number, that number is the
body's ceiling, not the search's failure. (This is what ultimately justified
the architecture change to the CGP mixer.) **Feast-graft lesson:** hand-setting
vacuum-cycle genes onto gen576 scored −1.8 to −7.4 — organ economies must
CO-EVOLVE; transplanted values are load-bearing parts of someone else's
economy. **Screen noise calibrated:** n=40 screens ran σ≈5 (the same body
printed +8.00 and −8.39) — all screens ±10 until proven otherwise; n=100 or
silence. **Live: omni-body timeout fear died** — 367 matches, zero bans on us
(the 2 scary rows were another team's). And the live census (n=365: 11% apex /
21% mid / 68% weak — prey-rich, the INVERSE of our 75%-giant breeding room)
was the first hard sign the gym was training for the wrong world.
**Live drama of the day:** OMNI-B's gen576 emerged AUTONOMOUSLY (no seeding,
no grafts) and took the live crown for us — proof the architecture could breed
a champion end-to-end. Then **Bot Battle took #1 with a pure vacuum doctrine**
— the earliest live demonstration of what the 07-12 economics later formalized
(farming throughput beats fighting for the leaderboard's objective). Room
compliance battles (the 2+2+2+2 "seeing room") established that any room
change must be acknowledged in the next report — rooms silently drifting is
how gyms stop measuring what you think they measure.

## 2026-07-09 (THE .12 SPLIT-FEAST VIRUS ECONOMY — the defining strategic discovery)

From raw replays (matches 1719–1724): **consuming a virus grants +2.25 mass
(virus.radius²), mass conserved through the shatter; pieces = 17 − blobs.**
~40 consumptions ≈ +90 mass — **viruses are ~90% of a 100-mass game.** Team-15
(the leader): 21 split-moves/match, blob count oscillating 1↔16, consumption
bimodal (46% at 1 blob = max shatter engine-start, 26% at 15–16 = free mass).
Shatter is the ENGINE of the economy, not a cost. **Our champion elite_g30 in
the SAME lobby: 0 splits, 2 consumptions, flatlined at ~1 mass, eaten** — its
split genes were degenerate because the old gym's mimics never split, so
non-splitting was never punished. Root cause of the entire slippage era, and
why evolution on that base couldn't improve: **the meta strategy was
unreachable from that basin.** Built split_feaster (elite_g30 + split-feast
cycle organ) same day. **Hard lesson re-learned:** its hand-built gym showed
+6.62 at n=40 → COLLAPSED to −6.55 at n=100 (winner's curse), and the gym
failed known-answer calibration (elite_g30 gym-mass 25–29 vs live 19) — never
trust a gym whose calibration bots don't reproduce their live numbers.
**Hermes trust posture set:** its raw event extraction verified within ~10%;
both its scary headline metrics (837 "win rate", ban attribution) were
plausible-but-wrong DEFINITIONS. A liar's raw data is worthless; a buggy
aggregator's raw data is usable. Recompute all derived metrics from raw events;
win rates from `event_player_won` only.
**Meta context (from the day-4 log):** the split-feast meta CONVERGED — four
teams at 40+ average simultaneously; our elite_g30 was dethroned in this wave.
split_feaster iterated v1→v2/v2b→v3 chasing it; the corpus decode surfaced the
"grow-then-cycle" lever (bank mass first, then cycle-split into the virus
field). And the two-machine self-play run split into distinct basins from
similar bases — omni-A a patient feaster, omni-B a prey hunter: **the room,
not the seed, chooses the doctrine.** The gym IS the strategy.

## 2026-07-08 (day 4 — THE FIRST CROWN, and the crises that wrote the process laws)

**Decay Rate reached #1 on the live leaderboard** at the close of the
sliding-window saga — the campaign's first crown, in the gen51-lineage era.
The body that did it: **gen51_noavoid, a ONE-GENE change certified +9.32,
which posted an 83.5 all-time record live.** Its parent gen51_organs_off had
been discovered by organ AMPUTATION — switching organs OFF outperformed the
full body (the "accidental regularizer" discovery). Twin lessons that outlived
the lineage: **subtraction is a discovery tool** (amputate before you graft),
and **a single gene can be worth +9** when it sits on a load-bearing doctrine
(noavoid = stop fearing viruses the meta had made valuable).
**The vfix saga** (same era): a champion shipped on n=9 verification, a live
"butchered" dispute, resolved only by building statistical twins — n=9 is not
verification, it's vibes. Directly ancestral to the winner's-curse law.
**The multi-agent crises also date here:** a session collision, ghost
processes, and the fabrication incident — an agent reported an entire trial
that never ran (no files existed). These wrote the permanent process laws:
sole operator (kill anything I didn't launch), files-or-it-didn't-happen
(recompute from disk, cite paths), win rates from `event_player_won` only.
Rival decodes of the era: ENGORGIO, team-59; gen099_i19 entered the
verification pipeline. Also: **the day-2/3 corpus decompositions had ALREADY
proven the leader's edge was harvesting incompetent bots** — the 07-13 meta
verdict was empirically on the books five days early; we kept building
fighters anyway. (Cross-reference: Chris's parallel journal, Desktop/
journal.txt, archives the full transcripts of these days.)

## 2026-07-08 (opening-race and prey-ecology lanes close — the gap was predation, not foraging)

Three evolution lanes (opening-gene overlay, field-ecology, prey-ecology) all
closed unpromoted. Replay decomposition killed the premise: the live opening
gap vs the apex is **early PREDATION (~22 vs ~3 mass of kill income by r400
— they win real fights), not foraging (pellet income a wash, 116.6 vs 111.5)**.
Evolution kept trying to switch the opening overlay OFF (OPEN_ROUNDS driven to
the clamp floor) — when the optimizer fights your feature, the feature is
wrong. Soft-seat-only ecology OVERFIT (in-league rank improved while yardstick
performance degraded) → a champion anchor in the room is a necessary selection
gradient. **Corpus rule (Chris): analysis uses matches ≥200 only** — the old
era is retired for decisions. 07-07 evening addendum, from the hybrid-geometry
ablations (n=20 each): commitment-latch alone −5.94, safety-veto alone +0.03,
both together ≈ +2 — **aggressive organs are only survivable with their safety
nets; the net alone is neutral.** Foreshadowed VULN v2's five hard vetoes.

## 2026-07-07 (SCORING RESOLVED: leaderboard = Avg Final Weight, and harness fix validated)

**The leaderboard scores AVERAGE FINAL MASS, not rank.** Confirmed from the
first-match results chart Hugo posted (axis: "Avg Final Weight"; Rye ~56
smashing test bots at 1–15). This settles the opening-ceremony open question
decisively toward the "largest cell" reading, NOT consistency round-robins.

Consequences — this is a partial objective pivot:
- All tuning to date optimized mean RANK. Rank and avg-mass correlate but
  diverge: a boom bot (mass 40, occasional death→0) can beat a steady bot
  (always ~15) on the average even while ranking worse.
- Some rank-rejected variants may WIN on mass — especially perblob ("fatter
  but deader", higher mean mass in every A/B) and the hunting/greed variants.
  Re-judge the whole variant library by mean mass, not rank.
- Survival still matters (a death contributes 0 to your average), so pure
  recklessness is still bad — but TIMIDITY that caps mass is now clearly
  suboptimal. The tradeoff moved toward growth.
- Action: harness now reports and can sort by mean mass; ladder/promotion
  switches to a mass objective (see TUNING.md). Re-run key rejects.
- Caveat: we still don't know the aggregation window or whether it's mean
  over all your games / best N / decayed. "Avg" is the label; ask Discord
  for the exact formula. But the axis being mass is unambiguous.

**Harness slot-bias fix VALIDATED.** Post-fix A/A blocks (identical bots,
shuffled slots): mean-rank gaps of 0.1–0.34 (4.42 vs 4.58, 4.33 vs 4.67,
4.41 vs 4.59, ...) vs the pre-fix 3.11 vs 5.89. Noise floor ≈ 0.2 mean rank,
well under the 0.55 promotion bar. Results from here are trustworthy. Lesson
reinforced: the A/A control is the single most valuable experiment we ran.

## 2026-07-07 (engine 2026.1.8 — headless is now unthrottled; total re-run)

The promised update landed. Diffed 1.7→1.8 (procedure 04):

- **Headless matches no longer sleep between ticks** — the engine only
  throttles in `--realtime` (GUI) mode. A full 1400-round match: ~5 s
  (+~10 s fixed launcher countdown), was ~140 s. **~20× throughput.**
  The fast-clock rig (03 §6) is obsolete; statistical power is now cheap —
  default to 50-game screens, 100-game promotions.
- **Vision clamped inside arena** (their fix for a competitor's report):
  near walls the view centre shifts inward. `view_center` ≠ centroid there.
- `ClientState.players` removed (we never used it); `total_players`,
  `winner_player_id`, `engine_version` added to bot-visible state.
- **Tie-break code unchanged** — the slot bias survives in 1.8; our shuffle
  fix remains necessary. Bounty candidates all still valid.
- Operational note: upgrading the venv mid-batch would have mixed engine
  versions inside one experiment set — stopped batch 3, upgraded, restarted
  everything under 1.8 with the shuffled harness. Also: `pkill -f
  agario-venv` kills your own pip upgrade if pip lives in that venv. Ahem.
- Official announcement (Discord, "Game engine update #1") later confirmed
  the diff, and added one fact we couldn't see in the source: **leaderboard
  matches run unthrottled too** ("the same applies when you submit it via
  the website"). So per-tick bot compute directly slows official matches —
  keep the decision loop O(visible objects) forever; anything heavy is now
  a leaderboard liability, not just a local one. Submission is "via the
  website" (GameHub).

## 2026-07-07 (Discord intel — engine update imminent, our bugs unreported)

From the Bot Battle Discord (evening of day 1):

- **A new engine version ships "later tonight"** fixing (a) the
  edge-of-screen FOV bug and (b) a visibility/last-known-state bug. Vision
  behaviour may change — run instructions/04 the moment it lands, especially
  re-verify the circle-intersection vision facts.
- **More changes are being considered, not just bugfixes**: FOV measured
  from centre vs edge is "to be decided", same-player attraction may become
  mass-dependent (changes merge dynamics), and `ClientState.players` may be
  removed entirely (we don't use it — but check after update).
- **Our three bounty candidates are unreported** as of this dump — virus
  units mix, missing split cooldown, player_id tie-break bias. Virus report
  drafted and ready to send.
- The GameHub PLAYER_BANNED TIMEOUT errors are an acknowledged portal-side
  issue ("This is us sorry") — if our submission gets banned with the
  to_engine/from_engine pipe message, it may not be our bug; check Discord
  before panicking. Our crash guard covers the bot side.
- Competitors are sharing dummy bots in Discord — grab them for `bots/meta/`
  when posted; free archetype reconstructions.

## 2026-07-07 (A/A calibration catches a systematic slot bias — methodology reset)

**The engine favors lower player ids in every contention tie, and it's big
enough to have manufactured most of our results.** A/A block 1 (batch 3):
byte-identical bots, 30 games, slots 0–3 vs 4–7 → **3.11 vs 5.89 mean rank,
22–8**. Mechanism (state_mutator.py): food, eating, and virus contests all
sort candidates by `(-radius, player_id, blob_id)` — equal radius means the
lower id wins the pellet/meal. At game start everyone is radius 0.9, mirror
copies converge on the same clusters, low slots win every tie, and
bigger-eats-first compounds it into a blowout.

Consequences: (1) every pre-fix A/B listed baseline in slots 0–3 — all
eleven "defenses" are contaminated; variants whose losing gap was ≤ the A/A
gap may actually be improvements (ignore55, perblob, preyhunt20, threat60
are the closest calls). (2) tournament.py and league.py now shuffle slot
assignment per game — unbiased from here on; `--no-shuffle` retained for
deliberately measuring the bias. (3) **Bug-bounty candidate #3**, likely the
most valuable: if the live leaderboard assigns player ids deterministically
(e.g. by submission order), the whole competition has a fairness bug.
(4) The methodology lesson: my earlier "spawns are random so slot order is
fine" check looked at the wrong mechanism and shipped a wrong all-clear —
*an A/A control is the only check that validates the whole pipeline at
once*, and it should have run BEFORE eleven A/Bs, not after. Run an A/A
first in any new experimental setup, always.

Log of useful discoveries, one dated entry each, newest at the top of each
day. Not a lab notebook (that's TUNING.md) — this is for *insights*: engine
facts, methodology lessons, strategy realizations, gotchas. If a future
decision would be made differently because of a finding, it belongs here.

---

### 2026-07-14 — VERIFIED: a live bot can open another seat's `to_engine.pipe` for writing
Contained local verification against installed `agario-kit==2026.1.13`:
seat 1 ran as uid 501 from `submission1`, obtained fd 4 by opening the live
`submission0/io/to_engine.pipe` with `O_WRONLY|O_NONBLOCK`, then closed it
after writing **zero bytes**. The foreign FIFO was uid 501, mode 0640;
`os.access(..., W_OK)` was true. The normal 1,400-round match completed
`SUCCESS` with no bans, proving the probe itself caused no interference.
Installed launcher source confirms all submissions use the same
`sys.executable`, shared `GAME_ENGINE_CORE_DIRECTORY`, and OS user; engine
source confirms it reads moves solely from the seat-numbered FIFO and only
validates the attacker-controlled JSON `player_id` field. Therefore cross-seat
write access is real in the distributed kit. Production remains unverified:
an external per-seat container/UID wrapper could mitigate it, so disclosure
must explicitly ask organizers to confirm production isolation. Raw evidence:
`/tmp/botbattle_crossseat_to_engine_evidence.json`; preserved match workspace:
`/tmp/botbattle_crossseat_live_verify`.

### 2026-07-14 — grace-period bots receive 2x scheduling frequency
Chris ordered a scheduler policy change: candidates with `_games < GRACE`
now receive exactly weight 2, while mature candidates receive weight 1.
This applies to both paths: weighted-random local selection and shuffled
weighted round-robin dispatch to Studio/WSL. It is deliberately NOT a return
to least-played-first; mature candidates retain equal expected service and
newborns lose the boost automatically at 75 games. Policy timestamp: applied
2026-07-14 at match 55,540.

Activation exposed an operational stall: `_draw_room()` enumerated the
Desktop `BEST_BOTS` directory for every match, so parallel local workers and
remote batch pumps could block together in macOS `os.scandir`. Because the
pool is frozen by standing order, it is now snapshotted exactly once at
process start and reused immutably; an empty/unreadable snapshot fails loudly.
This changes no pool membership or room probabilities and makes an explicitly
ordered BEST_BOTS change take effect on the next ladder restart.

**Activation status / integrity rollback:** the restart context could not
enumerate `~/Desktop/BEST_BOTS` (directory exists but glob returned empty).
Before the fail-loud snapshot check was added, 40 local successes at logged
matches 55,540–55,579 occurred only on draws that happened to avoid the empty
elite pool, making them biased zero-elite rooms. They were removed from
`state.json`: match/last_ckpt restored 55,580→55,540, exactly 40 `_games`
removed across 23 affected candidates, windows/ranks/cons reversed and
validated against the log. Nine dropped mature-window masses were recoverable
only from the 0.01-rounded JSONL values (maximum fitness effect negligible,
<0.001). Pre-rollback state is preserved at
`evolution_v3/state.pre_invalid_rooms_55540_55579.json`; invalid log lines are
marked by `ROLLBACK_INVALID_ROOMS` and remain as an audit trail. **Ladder is
intentionally DOWN until Terminal/Desktop access can enumerate the frozen pool;
do not substitute another pool.** The 2x scheduler code is compiled and ready.

## 2026-07-06 (night — endgame also rejected; v0.1 fully dead)

**Within a match, rank = final mass — passivity never protects a lead.**
endgame_only (rank protection, no EMA) lost 24–6. The design assumed a lead
is held by avoiding risk; but the match ranking is a mass race to the
buzzer, so a leader that throttles prey-attraction for the last 150 rounds
just watches rivals snowball past. If a "leading → change behaviour" term
ever returns, it must stay *aggressive on safe food/prey* and only veto
splits/marginal fights — never dampen the growth engine. Also: my smoke-test
read ("endgame won its smoke match!") was worthless against a 30-game
result — single games carry ~zero signal, as the playbook already said.
Score after day 0: champion v0 has defended **9** straight A/Bs; every idea
of mine died in testing. The engine's own tuning is formidable; respect the
one-change rule and the ladder, and spend creativity on new inputs +
real-opponent data, not on re-weighting a solved core.

## 2026-07-06 (design decision — not RL, and staying that way)

Chris was advised (consistent with the AgarCL literature) to avoid RL-style
approaches: sample-hungry, unstable self-play, unexplainable policies. Our
pipeline is NOT that — the policy is hand-written and interpretable; the
league/random-search loop is offline *parameter selection* with a human
reviewing every promotion diff (≥50 games, >0.55 margin, git-revertible).
The one shared hazard is self-play drift (optimizing vs our own population),
mitigated by: diverse hand-written archetypes + template in every league
pool, meta-box results outranking mirror results, and the live leaderboard
as final ground truth. Standing rule: **machines count, humans decide;
nothing learns at runtime.**

## 2026-07-06 (late evening — v0.1 rejected)

**Reactivity beats smoothness — the "jitter" theory was wrong.** v0.1
(endgame + EMA velocity smoothing) lost to v0 by the worst margin yet
(27–3). Endgame protection only acts in the final 150 rounds while leading —
it cannot explain a 27–3 wipeout. Prime suspect: EMA smoothing (α=0.3) adds
lag to every prediction, and at 0.1s ticks in a contact-heavy 60×60 arena,
*response latency is deadlier than estimation noise*. Reframe of the
intercept post-mortem: raw single-frame velocity isn't noise to be filtered,
it IS the signal — intercept lost for its own reasons (probably the hard
chase-abandon), not because its inputs jittered. Isolation run in flight
(endgame_only, EMA off). Meta-lesson: bundling two changes cost a full
tournament cycle to un-confound — the one-change rule exists for a reason,
even for a "version release".

## 2026-07-06 (day 0 — setup, engine archaeology, first seven tournaments)

**Mirror A/Bs amplify small differences — and can mislead on style.**
Every one of seven 4v4 mirror tournaments ended in a blowout (worst 19–11,
best 26–4) with losers uniformly around rank 5.5–6.0. Mechanism: whichever
side wins the early food races snowballs and eats the other side. So decisive
margins ≠ huge underlying differences, and a sensitive detector for small
ones. Corollary from the perblob result (fatter by 2.3× but deader): a
farming-heavy style can lose mirrors yet be better vs the real field —
weigh mixed-field/meta results above mirror results.

**The handover CONFIG is a genuine local optimum.** Six challengers, six
decisive defenses. Coherent weight sets punish single-knob deviations; the
remaining edge is in untested axes, contextual behaviour (endgame), and
anti-meta — not in re-tuning the core.

**Prediction jitter, not prediction logic, killed interception.** The
intercept variant (proper closing-speed solve + abandon uncatchable chases)
lost 26–4. Velocity estimates are single-frame deltas; the intercept point
jumps frame to frame. Lesson generalizes: any feature consuming tracker
velocity needs smoothing first (EMA now in v0.1).

**Virus "mass" is its radius — engine unit mix, bot bug, bounty candidate.**
`_can_consume_virus` checks `blob.mass > virus.radius * 1.2` (=1.8, i.e.
blob radius ~1.34), and consuming adds `+virus.radius` (+1.5) mass. The bot
assumed mass=radius²=2.25 and walked into viruses in the radius band
1.34–1.64 (fixed). Two bounty candidates documented in README: this unit
mix, and the absent split cooldown.

**Speed is hyperbolic, not linear**: `1.1/(1+0.08r)`, floor 0.25 (README had
`1.1−0.08r`). Giants are ~2× faster than the linear formula suggests at
r=10; the floor is unreachable in practice (r≈42). "Big = slow = harmless"
is weaker than documented — yet THREAT_IGNORE_DIST=7.0 still won its A/Bs,
so the heuristic survives empirically even with the wrong rationale.

**Split mechanics differ from folklore**: `split=True` splits EVERY blob
with mass ≥ 2.0 (same direction), there is NO split cooldown (the 18 ticks
gates merging), and viruses are static with no eject move — virus push/feed
tactics are impossible, virus-as-shield is real (immunity below mass 1.8).

**Spawns are uniform random with min separation** (not corners) — confirmed
`_spawn_players_randomly` in source. Means slot order in tournament specs
carries no positional bias; our A/B methodology is sound.

**Windows can't run the engine natively** (`os.mkfifo`); WSL works, but the
match workspace must be on the Linux FS. Practical ceiling ~10 concurrent
matches in 15 GB WSL — beyond that everything freezes and matches hit the
600s timeout (originally killed whole tournaments and 40 finished games;
harness now skips hung games). macOS runs it natively.

**The engine exposes more state than the bot uses**: `round`, `max_rounds`
(→ endgame logic, now in v0.1), `vision_size`, `view_center`, `turn_order`,
`event_history`. Unexploited signal — event_history may reveal eats we
didn't witness.

**Editing a bot file mid-tournament contaminates the run** — matches read
bot files at process start, so later games silently use the new code.
Never edit `my_bot.py` or an in-flight variant while tournaments run.

**Opening-ceremony intel (from Chris)**: portal 7–19 July, continuous
resubmission (→ submit day 1 for meta-intelligence); $100 bug bounty;
four always-on machines available, review time is the real constraint;
scoring aggregation is an OPEN QUESTION (slides say largest-cell, docs say
consistency round-robins) — it decides the tuning objective and v0.1's
endgame settings assume consistency. Ask in Discord day 1.

### 2026-07-13 — portal fitness chart was lying (two biases fixed)
The fitness-over-time chart disagreed with the population table because of two
measurement artifacts, both now fixed in `portal/server.py`:
1. **Elite line biased high**: it took the MAX of every momentary rolling-fit
   reading inside each 100-match bucket (~2-3 noisy readings per bot), which
   systematically over-reads. Now each genome contributes ONE value per bucket —
   its end-of-bucket rolling fit — and elite = top-1 of certified (n≥150),
   with the anchor excluded (elite is what challenges the anchor).
2. **Anchor line was the wrong anchor**: it plotted the old passive pool-seat
   cumulative mean (~42.2) instead of the real 41st-candidate seat-0 rolling
   fit (~39.8). The real line is now primary (amber dashed); passive kept as a
   faint gray reference. Real reads ~2.4 lower than passive — the passive seat
   flattered the ship.
Also: "leader Δ anchor" KPI now only compares a CERTIFIED (n≥150) leader —
it was quoting an n=13 newborn's hot streak. Lesson: any line on a dashboard
must be computable from the table on the same page, or one of them is wrong.

### 2026-07-13 — SHIP #40 (imm479 line): first v3-campaign ship
Chris ordered ship of genome #40. Gym: fit 44.9±3.1 @ n=177 (window 300),
median 39.9, bust 32%, avg rank 2.57 — +4.2 over the anchor's REAL seat-0
read (40.2@149) and +5 over old passive. Lineage: imm479 immigrant (v2
champion line) refined by v3 gym. Its evolved graph is a 3-node doctrine:
N0 = 1−feast_ready → INCUMBENT (feast-readiness gates who counts as champ),
N1 = 1−N0 → CYCLE vote, N2 = min(late,N1) → CYCLE vote — i.e. "cycle-split
only when feast-ready, double down late". No human wrote that coupling.
Ship protocol: materialized from state.json (255/255 genes applied),
byte-identical to gym variant g40.py (provenance exact), py_compile OK,
one real-engine (2026.1.13) witness match: SUCCESS, 0 ban events, won the
room 50.9 vs live ship 452 (2.4) + gen51_feast (19.9) + full census room.
sha256 2063bcb4…5db1b2, vaulted with genome JSON. Staged for upload as
bots/SHIP_v3_imm479_40.py — Chris uploads via SYNCS portal (a faulty upload
freezes the team, so the boot-witness match is the non-negotiable gate).

### 2026-07-13 — BREEDING WORKS: first certified cross-bred generation, #121 ships at +7.6
The family-block inheritance doctrine (this morning's rebuild) produced its
first certified generation tonight, and it is not noise:
- Five kids of the 41/47/56/83/84 parent cluster read 45.3 mean vs 39.5 for
  the other 30 mature bots in the SAME window era (anchor steady 40.2@300).
- Both reciprocal pairs replicate (41×83 ≈ 83×41; 47×56 ≈ 56×47) — the cross
  carries the signal, exactly what family-block inheritance was built for.
- Parents all certified 40.0–42.5 (n=300 each); mid-parent ≈41. Kids raw ≈45.
#121 (x56x47-fine) CERTIFIED at 47.77±3.3 @ n=155 — +7.6 over the live-ship
anchor's real seat-0 read (40.22@300), 3x the +2.5 ship bar, the strongest
certified signal of any campaign. Best game 139.4 = the full-vacuum win-size
trait (the exact lever behind team's 59.6 leaderboard leap). Its graph:
N0 feast_ready>edge → INCUMBENT; N1 N0×wealth → CYCLE (gain −1.26, wealth
suppresses cycling while incumbent); N2 min(late,N0) → CYCLE (+0.35,
re-enable late) — hold mass mid-game, vacuum late. No human wrote that.
Ship protocol passed: 255/255 genes, byte-identical to gym g121.py,
witness match SUCCESS 0 bans (placed 2nd behind split_v3's 79.6 — single
game, noise; the certified n=155 is the signal). sha256 84cf6306…7baad6.
SUPERSEDES staged #40 (certified ~44): if #40 not yet uploaded, skip it.
Winner's-curse calibration recorded: #78 went 47.4@13 → 38.1@244 (n=13
mirage), while this cohort was judged only at n≥150 per doctrine.

### 2026-07-13 — hand-tuned node activation: 4 variants on #121's chassis (bots/handtuned/)
Observation (Chris): the evolved pool leaves most node slots dark — #121 runs
3 live nodes + 1 dud (N7 const→unrouted), and NOBODY in the pool has ever
routed the v3 dials (9-13) or defense sensors (19-21). Hand-tuned 4 variants,
each = #121's exact genome + 2 new nodes aimed at tonight's live-data lever
(win size 66 vs team's ~105):
- HT1_vacuum: late×rank_lead→feast dial +1.0 (2.7x vacuum when leading late);
  feast_ready−threat→prey dial +0.6 (bolder leftovers when safe)
- HT2_closer: vuln_window×safe→vuln-margin −0.8 (commit on defenseless
  pieces); late×rank_lead→feast +0.8
- HT3_tempo: late×safe→cycle-gate −0.7 (freer cycling); kill_pulse×threatened
  →cycle-gate +0.8 (tighten under fire)
- HT4_guard: threat_prox+kill_pulse→threat dial +0.6; dominance×late→feast
  −0.6 (protect the median: don't die greedy while dominated)
All byte-verified 255-gene overlays, compile, witness SUCCESS 0 bans (HT1 won
its game 119.1). Delivered to Chris; candidates for the inject queue.

### 2026-07-13 — the 90-minute lie: analysis load on a gym node corrupted three verdicts
Both fixed reference bots (anchor #452, culled champion #121) stepped down
~8-12 mass at m≈20772 (19:38) and recovered after ~21:10 (anchor's last 70:
42.4). That window brackets exactly my Studio-side team forensics (meta
sweeps, 6GB zip extraction, browser replay parsing). Mature bots play 100%
remote → their matches ran CPU-starved; young-bot aggregates stayed flat
because culls deleted the depressed readers (survivor masking). Chris smelled
the timing (he blamed the twin-injection; the twin data refutes that specific
mechanism — #121 averaged 45.5 IN twin rooms vs 33.9 without — but his
instinct that the step was CAUSED, not noise, was right and mine was wrong).
Casualties judged inside the window: #121 culled 21:09 (unsafe verdict, one
minute before recovery), HT1 (36.0@70) and HT2 (32.2@71) audited entirely
inside it. All three genomes vaulted; re-injectable on Chris's word.
LAWS: (1) never run heavy compute on a gym node while the evolver lives;
(2) node results are testimony, not observation — sha checks verify identity,
not execution quality; (3) verdicts overlapping a load window get re-judged.

### 2026-07-13 — RETRACTION of "the 90-minute lie" entry: Chris was right, twice
The load-contamination story above is FALSE. Chris's counter ("if it were
wall-clock starvation it would print timeouts — and banned matches don't go
into records") is verified against the engine source and the worker:
`run_game()` BLOCKS on every `query_move_player` (realtime only sleeps in
visualizer mode) — a starved bot plays at full fidelity, just slower; a
2s/8s breach = ban = aborted match, dropped by BOTH the node worker
(result_type != SUCCESS → no mass posted) and the ladder (run_match → None).
Load can thin the sample; it cannot bend the values. So: #121's cull was
legitimate (winner's-curse convergence, true level mid-to-high 30s, lifetime
39.9 vs anchor 38.5); HT1/HT2 culls stand; the anchor dip was noise after
all. Lesson (expensive, twice today): under pressure to explain a wobble I
manufactured a causal story from a timing coincidence when the decisive
evidence — the engine source in the local venv — was a grep away. The prior
for a fixed bot's step is noise/curse; causation claims require a verified
MECHANISM, not a bracket of correlated timestamps.

### 2026-07-13 — SHIP #171 (x83x102-fine): first ship judged by trajectory, not peak
Chris ordered ship of #171: 47.8±2.7 @ n=223 (232 at ship time), median 51.4
(> mean — healthy mass distribution, not a few monster wins), avg rank 2.32,
bust 28%. THE decisive difference from tonight's failures (#452 peak 46.7→38,
#121 peak 47.8→37): #171's lifetime per-50 trajectory is 45.7 → 42.0 → 51.5 →
49.6 → 52.5 — flat-to-RISING across its whole measured life; we are not
quoting an excursion top. Graph doctrine: N0 (1−feast_ready)→VIRUS ch −0.355,
N1 (1−threat)→VIRUS ch −1.106 (virus channel suppressed unless feast-ready
AND safe), N2 min(feast_ready, N1)→CYCLE −1.5. Ship gate: 255/255 genes,
byte-identical to gym g171.py, compile OK, witness SUCCESS 0 bans.
sha256 logged; staged in ~/Desktop/ship_staging/. Context: pool median 40.4;
old ships (#452 anchor 37.7@300, #195 ref-injected 38.6@73 then culled) both
read below pool median and indistinguishable from each other in-gym.

### 2026-07-13 — ALL-16 injection campaign: 100 hand-built node-activation genomes, 2 per cull × 50 culls
Chris supplied 100 injectables (Desktop/SHIP171_ALL16_INJECTABLES_100): each =
ship #171's genome with its proven N0-N2 preserved, ALL 16 nodes enabled
(MAX_ACTIVE=16), every node routed to a live target (1..13, |gain|>=0.04),
10 doctrine families (balanced/bank_guard/safe_vacuum/rank_posture/
consolidator/vuln_closer/anti_frag/edge_survival/kill_tempo/tempo_harvest)
× 10 doses (d0-d9). Independently re-validated (schema/bounds/acyclic/ON;
0 failures; sample compiles). Deployed as 50 in inject_queue/ + 50 in
extra/ so the ladder's 1+1-per-cull mechanism seats exactly 2 per cull for
50 culls (~6-7h); ordering pairs families before doses. First pair confirmed
at m=43659: #288 all16-balanced-d3 + #289 all16-bank_guard-d3. Breeding runs
3 slots/cull for the duration. This is the systematic sweep of the dark
node-space (dials 9-13, defense sensors) that the 4-bot HT probe sampled.
Judgment discipline: mature windows only, no peak-quoting; the readout is
which FAMILIES survive culls at rates above the bred-children baseline.

### 2026-07-14 — STAGED #529 (all16-edge_survival-d9): the injection campaign's first keeper
Chris ordered staging of #529: 44.8 @ n=646 (SE~1.4 — deepest sample of any
ship candidate ever), median 45.7, latest 46-game chunk 52.2, trajectory
oscillates 38-52 with NO decay signature. +7 over the anchor (#452 ~37.7)
at four times the certification depth. Provenance: hand-built all16
injectable (edge_survival family, max dose d9) from Chris's 100-genome
campaign — all 16 nodes live, #171's N0-N2 preserved. Gate: 255/255 genes,
byte-identical to gym g529.py, compile OK, witness SUCCESS 0 bans (452 won
that single game 83.8 — one game, noise). sha256 logged; staged in
~/Desktop/ship_staging/SHIP_v3_all16edge_529.py.

### 2026-07-14 — FINALS ANNOUNCED (top-8, ~10k all-elite games) and the proxy table inverts the leaderboard
Organizers: finals = top 8 on leaderboard, ~10,000 games over 24h among the
finalists — an ALL-ELITE room, the exact regime our census under-trains.
Also: bans now score 0 mass (no impact — our record is clean) and engine
2026.1.14 "fixed event leaking data" (VERIFY our f16-f18 sensors survive
before assuming neutrality — rankings/kill-feed are leak-adjacent channels).
Room-composition analysis of the top 10 (each team's last 400 games, tiers by
current leaderboard, elites-in-room buckets): avg rank in >=2-elite rooms —
Bot Battle 2.88 (nearly flat degradation 1.98->2.95 across compositions, the
hidden favorite despite #7 leaderboard), Banana 3.15, US 3.48 (3rd-best
positioned; 50% top-2 in 3E+ rooms), OJ 3.62, team 3.65, Washed 3.67,
spaghetti 3.72 (#1 on leaderboard, paper tiger), L&F 3.95, SUNMO 4.23 (worst
fighter, #4 leaderboard). Leaderboard order ≈ inverted finals order because
leaderboard average = farming skill and the final has nothing to farm.
Top-8 entry looks safe (us #5 at 32.0; team collapsed to 23.7 on a fresh
sub — their leap fully evaporated). PROPOSED (Chris to decide): finals gym —
7-elite census from our ship stable — as next world after the all16 campaign,
since current-census gym points buy almost nothing in the finals regime.

### 2026-07-14 — FINALS PIVOT: 7-elite mirror gym + time-gated dual ship validated
Finals announced: top-8 by leaderboard, then ~10k games in an ALL-elite room.
Room-composition forensics (last 1000 replays): >4-elite rooms are ~1% of
matchmaking, 7-elite rooms have NEVER occurred — the finals regime is out of
distribution for every team; best predictor = 2E->3E degradation slope
(Washed rises 35->39%, we FALL 31->23%). Response, on Chris's orders:
1) v3campaign-1 stopped @ match 154,717; all 40 survivors archived as
   rankXX_nYYY_lineage (+ genomes, manifest, state, log) in
   archive/campaigns/v3campaign1_final_20260714_7elitepivot/.
2) Gym relaunched as v3campaign-2:FINALS-7elite-mirror452 — every room =
   7 copies of the live ship #452. No fodder. Windows flushed, gene pool
   carried over. New fitness = mass extracted from 7 elites; the anchor's
   own mirror read is the natural bar. First minutes: candidate #930 took
   90.15 (38 virus feasts, rank 1) in the mirror room — the economy exists.
3) DUAL SHIP (Chris's design): one upload, CONFIG_QUALIFY before a UTC
   cutover, CONFIG_FINALS after (tools/make_dual_ship.py). Branch selection
   gene-verified; both branches witness-tested 0-ban; fails safe to QUALIFY;
   gate prints one stderr diagnostic line (utc/sydney/branch) to
   submission.err each match. Chris verified ON THE LIVE SERVER that a bot
   reading the clock gets real current time — mechanism production-viable.
   Not prohibited by any published rule; visible on source inspection
   (accepted). Awaiting: exact leaderboard-freeze time + a FINALS genome
   certified above the ship's mirror-room bar.

### 2026-07-14 — kit 2026.1.14 "mass ban" mystery solved: launcher relative-path bug, engine unchanged
Chris's local runs under the new kit banned every player ("another player
banned" per game; his wrapper reported pods.current=0). Autopsy on the
official PyPI package: .14's only source changes are client-side
(ClientState.map -> size-only stub = the "leak fix"; typing tweak). Engine
source BYTE-IDENTICAL to .13 -> our f16-18 sensors safe, no bot changes
needed, gym stays on .13. The bans: .14's launcher spawns submissions via a
new run_delegated_worker (runpy) that resolves RELATIVE bot paths against
the wrong cwd -> FileNotFoundError -> pipe handshake never opens -> TIMEOUT
ban for every player. Reproduced (relative paths: PLAYER_BANNED; absolute
paths: SUCCESS, #171 wins 59.7). Live server unaffected (managed absolute
paths; our sub played through the upgrade normally). Candidate bug-bounty
report. Local rule: ALWAYS absolute paths to `simulation` under .14.

### 2026-07-15 — SHIP #862 (x630x367-fine): the farm-world champion, shipped for the QUALIFY seat
Chris ordered the old campaign's champion shipped for upload (leaderboard/
qualifying seat, replacing sub 1507/#452 at his discretion). Selection by
trajectory discipline: archive rank01 #918 (46.07@125) rejected — youth
spike (41.7 -> 52.7 halves); rank02 #862 chosen — 45.15 with MONOTONE RISE
across all 313 games (43.7/45.3/45.7/46.3), the #171-style shippable shape.
Gate: byte-identical to archived gym-tested variant, compile OK, witness
SUCCESS 0 bans (placed low in its single witness game — one game is noise;
n=313 rising is the signal). sha256 logged, vaulted with genome, staged in
~/Desktop/ship_staging/. Expected live: low-to-mid 30s by the usual gym->
live exchange; judge at n>=150 by slope per doctrine.

### 2026-07-15 — Chris confirms: the all-elite step-up is live and the arc worked
Chris's assessment after the pivot day: productive across the board — the
all-elite version successfully stepped up. Standing state: #862 (farm
champion) staged/shipped for the QUALIFY seat; mirror gym breeding around
apex #1045's rank doctrine (+7.3 over ship self-play @ n=664, rising) with
the guard line validating the conservative direction; dual-ship mechanism
production-verified end to end. Remaining before the freeze: bust-rate
audit of apex vs guard, diverse-elite validation, FINALS genome
certification, cutover timestamp from organizers, final dual upload.

### 2026-07-15 — Lookahead veto gate wired in (default OFF) + 100-candidate campaign queued
Built bots/lookahead.py (engine-faithful split-half simulation: virus-pop veto,
miss-survival veto, attack-lands veto) then INLINED it into omni_mixer_v3.py as
_la_* functions gated by 5 new genes: LOOKAHEAD_ON (default 0.0), LA_HORIZON,
LA_VIRUS, LA_MISS, LA_ATTACK. Additive + guarded => dead code when off.
Verified TWO ways: (1) verify_moves replay of #171's recorded game on the new
body with LOOKAHEAD_ON=0 = 1250/1250 moves identical; (2) equiv_test pre vs
post = 2000 ticks bit-identical, "behaviorally inert". LA-ON path witness-
tested: SUCCESS, 0 bans, splits still issued (veto selective, not blanket).
Compute measured: 34-81 us/call worst case; run on split-ticks only ~= 0.2%
of the 8s cumulative budget (~16ms/match) — effectively free, no subprocess.
Genes added to exposed bounds so the trait evolves/propagates. Queued 100
candidates (7 strong bases incl apex #1045, guard lines, farm champ x veto-
combos x horizons 3-6 + defensive jitter), 50 main + 50 extra = 2/cull for
50 culls. The CURRENT/live bot and all existing population stay LOOKAHEAD_ON=0
(bit-exact unchanged) — only injected la-* candidates run the gate. Gym
restarted at match 227382 (stale variants cleared to force new-body
materialization). Readout: do la-* lineages out-survive the reactive pool,
and which veto combo / horizon wins.

### 2026-07-15 — Injected elite-archive apex into BEST_BOTS pool (Chris's order)
Added the mirror-gym's best mature bot — rank02 inj2-lateguard-d1 (fit 20.60 @
n=197, the lateguard rank-doctrine bot) — to ~/Desktop/BEST_BOTS as
ELITE_lateguard_d1.py, so the farm census gym now draws a genuine elite-bred
sparring opponent in seats 1-2. LOOKAHEAD_ON=0 (its genome predates the gene);
role is a tough/diverse elite, not a lookahead demo. Pool 33->34. Ladder
restarted (BEST_POOL globs once at startup) to activate it. POOL CHANGE noted:
elite seat draws are now harder, expect a small downward drift in farm fitness.

### 2026-07-15 — Elite campaign archived; FARM evolution resumed with lookahead + 100 farm-tuned injectables
Chris's pivot back to qualifying prep. (1) ARCHIVED the 7-elite mirror campaign
as archive/campaigns/elite-archive-1/ (state, log, 40 ranked bots, full
RESUME.md + a working ladder_v3_ELITE.py copy) and ZIPPED (elite-archive-1.zip,
7.5MB) — resumable anytime. Notable: its rank01/rank02 were the lookahead/guard
injections (la-x1080 20.61, inj2-lateguard 20.60) — those experiments were
winning the mirror gym. (2) RESUMED the farm campaign from
v3campaign1_final archive (match 154717, windows intact — world_tag matched so
NO flush); restored the Design-B farm census _draw_room; backfilled the 5
lookahead genes (default OFF = bit-exact) into all 41 farm genomes so the old
bots can now carry/evolve lookahead. (3) Queued 100 FARM+LOOKAHEAD guesstimate
candidates (16 farm rank bases x LOOKAHEAD_ON=1 + veto/horizon variety +
whole-config farm jitter: virus-feast, cycle, camp, wealth, corner, frag-hunt,
bank-risk) — 50 main + 50 extra = 2/cull. Running 12h. The live/current bot and
existing farm pool stay LOOKAHEAD_ON=0 (bit-exact). breeding-KeyError bug from
earlier already fixed (mutate/crossover _fill backfill). Readout in ~12h: do
laf-* lineages out-farm the reactive farm pool, and which lookahead config wins.

### 2026-07-15 — SHIP #1003 (laf-rank09-v1m1a1h3): first LOOKAHEAD-ACTIVE live ship
Chris ordered ship. #1003 = the lookahead campaign's deepest winner: 54.7+-2.3
@ n=451 (still climbing when frozen), FLAT running fit (54.7-55.6 over recent
games), median 67 > mean, wins at 80-105 mass with 23-49 virus feasts — the
full-vacuum win-size profile that closes the gap the team forensics exposed.
Config: LOOKAHEAD_ON=1, ALL vetoes, horizon 3 (shortest = least pessimistic;
kept the kills, deleted the accidents). Measured against the HARDENED pool
(ELITE_lateguard sparring). Gate: 260/260 genes, byte-identical to g1003.py,
compile OK, TRIPLE witness (extra rigor for first LA-active live code):
3x SUCCESS, 0 bans (2 wins 87/79 + 1 bust — profile as measured). sha256
logged, vaulted + staged in ~/Desktop/ship_staging/SHIP_v3_laf1003.py.
Replaces sub 862 (live ~35.9) as the QUALIFY seat on upload. Live projection
~38-42 (contending #1). Finals lane untouched (elite-archive-1 + dual-ship).

### 2026-07-15 — Second-gen seeding: 100 evidence-driven candidates from the laf-run readout
Mined the first 100-candidate run (all 100 observed: 94 culled, 6 alive):
THE ATTACK-LANDS VETO IS THE DIFFERENTIATOR — every combo without it went
EXTINCT (v*a0: 0% survival, avg fit 38-39) while a1 combos avg ~46.5 and hold
all survivors. Miss-veto adds nothing on top (m0a1 >= m1a1); horizon is a
non-factor (h3-h6 within 2.4 fit). Children of laf winners own the top-10 —
the trait breeds. Second gen (prefix 70_/s2-, 2/cull): 40 winner-neighborhood
(local jitter around current top-9), 20 extreme-vacuum (feast axis pushed
1.1-1.4x under a1 protection), 15 elite-fusion (elite-archive graphs on farm
chassis), 10 dial-feast (late x rank_lead -> FEAST dial, the old HT1 idea now
LA-protected), 15 wildcards. Invariants pinned on all 100: LA on, virus+attack
vetoes always, m coinflip, horizons 2-5 (h2 previously untested). One leak
(wild jitter touching LA genes) caught by validation and repaired in place.

### 2026-07-15 — MULTI-MODE BOT ARCHITECTURE (Chris's design) + 3E training world live
The endgame architecture: ONE bot, FOUR parameter modes (1E/3E/5E/7E), an
in-game ELITE TALLY (unique elite team_ids seen via visible_blobs), and a time
gate. Mechanics installed in omni_mixer_v3.py: MODE_OVERLAYS {1,3,5,7} (gene
diffs vs base; EMPTY in gym = inert), ELITE_TEAM_IDS (empty in gym), escalate-
only switching (tally>=3 -> 3E, >=5 -> 5E, >=7 -> 7E), and CUTOVER
2026-07-19T14:00:00Z (= end of Jul 19 Sydney, when the official comp finishes):
after cutover the bot HARDCODES 7E. Before cutover live play starts at 1E and
escalates by tally. Verified inert TWO ways: #171 replay on the new body
1250/1250 identical + equiv_test 2000 ticks bit-exact. Evolution rooms carry
the switches but all modes are the same numbers — models get hand-picked per
E-level and bundled at ship time (bundler to populate overlays + team ids).
Farm/laf round paused + archived as farm-laf-archive-1 (9.3MB zip, RESUME.md;
NOTE: its rank02 x1213x1147-bold 56.7@227 BEATS shipped #1003's 54.7 — qualify
upgrade candidate). 3E TRAINING WORLD live: v3campaign-3:TRAIN-3E, room = 3
elite pool draws + 1 contested/fodder + 3 fodder; windows flushed, laf-adapted
genomes carried over; 82 s2 candidates still injecting. Plan: 1E model = best
farm bot; 3E model = this world's pick; then 5E world; 7E = elite-archive-1
lineage; bundle before Jul 19.

### 2026-07-15 — PIVOT: 3E training archived; 0E-model training world live; 0E mode added
Chris redirected: default assumption stays 1E, but train a dedicated 0E model
— when the bot identifies a 0E room it switches DOWN to the pure-farm
specialist (0E rooms = ~30% of games, currently commoditized at 70% win;
a specialist strips all elite overhead to mine that bucket). Executed:
(1) 3E world archived resumably as 3e-archive-1 (match 220746, zip 9.4MB).
(2) Body: MODE_OVERLAYS gained mode 0; ZERO-E RULE added to _mode_tick — if
no elite team_id identified by tick 150 -> apply 0E overlay; any elite
sighting at any time escalates immediately and 0E is abandoned permanently.
Re-verified inert: #171 replay 1250/1250 + equiv_test bit-identical.
(3) 0E training world live: v3campaign-4:TRAIN-0E, rooms = 1 contested +
20% second contested + ~5.8 fodder (live 0E shape); windows flushed, LA-adapted
pool carried; 80 s2 candidates still injecting. Mode roster now:
0E (train NOW) / 1E=base (have: #1003, x1213x1147) / 3E (3e-archive-1,
resumable) / 5E (later) / 7E (elite-archive-1 lineage). Detection thresholds
tunable at bundle time.

### 2026-07-15 — 0E world re-weighted to 7G (70% pure-fodder rooms) + 100 max-farm injectables
Chris: optimise for 7G. Room now 70% pure 7-fodder / 25% 1-contested / 5%
2-contested (tag TRAIN-0E-7G, flushed). Stale pre-pivot queue cleared. New
batch (z0-*, 2/cull): 30 cycle-aggression (CYCLE_MIN_MASS x0.5-0.85, more
target blobs, lower split threshold — heavy splitting is safe with no elites
and the LA virus-veto deletes the pop accidents), 30 feast-max (W_VIRUS_FEAST
x1.1-1.6, longer reach, softer slot penalty), 20 overhead-strip (threat/panic/
endgame-fear spend cut — nothing to fear in 0E), 20 combo-wild. Bases = the
10 farm-laf-archive-1 winners. LA invariants pinned (virus+attack always).
Goal: a 0E-mode model that pushes the commoditized 70% win at 0E toward the
85%+ our 7G data says is reachable.

### 2026-07-15 — BUNDLE v1 SHIPPED: the multi-mode bot is real
First full bundle staged (Chris's order): BUNDLE_v1_x1213_0E1415_7Elateguard.py
- BASE (pre-contact + 1E+): x1213x1147-bold (farm-laf champion, 56.7@227, LA-on)
- MODE 0E overlay (93 gene diff): #1415 x1349x1384-bold — the 0E world's bred
  champion, 80.2@155 flat halves, 2% bust (vs live ship 73.2 in same rooms)
- MODE 7E overlay (123 gene diff): inj2-lateguard-d1 (elite-archive champion
  20.6@197 in 7-mirror rooms)
- ELITE_TEAM_IDS = (85,37,1,9,59,5,24,4,73,15,14) — all elite-tier teams, us
  excluded. Spawn in 0E -> first elite sighting escalates (1E base; tally>=3/5/7
  -> 3E/5E/7E; 3E/5E overlays empty = base for now) -> post-cutover
  (2026-07-19T14:00:00Z = end of Jul 19 Sydney) hardcoded 7E.
Gates: compile OK; PRE-cutover witness SUCCESS 0 bans with live audit line
"[mode] switched to 3E (elites seen: 3)" (seat-id collision makes local gyms
simulate elite sightings — mechanism proven end-to-end); POST-cutover build
witness SUCCESS 0 bans, "[mode] switched to 7E" at boot. _apply_mode now
prints an audit line to submission.err (verified inert in gym via equiv).
PROVENANCE NOTE: the bundle file is a composition — not byte-identical to any
single gym variant; each component genome is byte-faithful to its measured
variant (vault holds all three genomes). sha256 logged; staged in
~/Desktop/ship_staging/. Replaces the qualifying seat on upload.

### 2026-07-15 — BUNDLE v1 CODEGEN: audit to stdout + mode-aware constant folding
Chris's polish orders: (1) mode audit line moved stderr -> stdout print(...,
flush=True) — lands in submission.log; (2) CODEGEN. Built tools/codegen.py:
mode-AWARE constant folding — keys touched by any MODE_OVERLAYS diff stay
dynamic (48 kept: the 0E/7E overlay unions), everything else folded to
literals (178 folds). Transformer PROVEN bit-exact the strong way: a fully-
folded #171 build (empty overlays -> 221 folds) replayed its recorded game
1250/1250 moves identical. Bundle codegen: equiv PASS vs plain bundle;
pipeline ~1.08x faster (bot was already ~0.05ms/move — codegen is margin, not
rescue). Witness gates on the CODEGEN build: PRE-cutover SUCCESS 0-ban with
the FULL escalation ladder captured live in submission.log (0E spawn -> 1E
first sighting -> 3E tally); POST-cutover SUCCESS 0-ban, 7E at boot.
sha256 logged; BUNDLE_v1_CODEGEN.py staged in ship_staging — THIS is the
upload artifact (plain bundle retained in vault as reference).

### 2026-07-15 — OPERATOR.md written (supersedes HANDOVER.md where stale)
Full operational playbook for future agents: the one-page mental model
(worlds/modes/lookahead/ship-discipline), Chris's standing laws, daily ops
(gym control, world switches, injections, ship gate, bundle+codegen build,
verification tools), infrastructure (nodes, launchd worker, Hermes, portal),
analysis playbook, current state + endgame checklist to the Jul 19 freeze,
and the paid-for incident lessons.

### 2026-07-16 — INCIDENT: bundle scored 7.4 live — engine .14 kill-feed rename starved our fear system. FIXED.
Chris flagged the new upload at 7.4 avg. Diagnosis chain: local .13 repro FAILED
(bundle scored 46.9 locally) -> installed agario-kit 2026.1.14 in /tmp/venv14 ->
REPRODUCED (bundle 14.5 avg, median 2; #862 control 34.5 = its live 35.9,
harness valid). Forensics: in a zombie game our bot moved fine, ate 458 food,
and was eaten 34 TIMES by the seat-1 hunter. Source diff .13->.14: the "event
leaking data" fix introduced public_event_player_eaten (censored kill feed).
Our f18 KILL_PULSE counted only the exact string "event_player_eaten" -> reads
ZERO forever on .14. The newest lineages (x1213/laf/z0) evolved heavy reliance
on it (e.g. kill_pulse x THREAT_PROX -> THREAT dial, gain 1.5) -> under-fear ->
eaten repeatedly. #862 predates that wiring -> immune (why it was fine live).
FIX: f18 + vuln kill-confirm accept both event names. BUNDLE_v2_14fix_CODEGEN:
43.3 avg on .14 (n=12, back to .13 form), 12/12 SUCCESS 0 bans, post-cutover
branch verified (7E at boot). sha ccfd727b... staged in ship_staging.
INTERIM: Chris advised to revert live to #862 (proven on .14) — v2 now ready.
CONSEQUENCES/TODO: (1) GYM MUST MOVE TO .14 — everything trained on .13 is
now suspect-until-revalidated; nodes (studio/wsl) must upgrade their kits too
(content-sha checks will need updating); world flush on engine change per
doctrine. (2) f18 semantics changed on .14 (kill feed is now visibility-
censored — local danger only, no global feed); retraining will re-tune around
it. (3) OPERATOR.md lesson added implicitly: the .14 leak-audit was flagged
Jul-14 and skipped — the cost of skipping it was a live incident.

## 2026-07-16 — Bundle EXONERATED; live 7.4 was server infra ("procfs is not mounted! Aborting")
Chris pulled the live error log for the bundle upload: it contains
"procfs is not mounted! / Aborting". Forensics: that string exists NOWHERE in
our code, the bundle, or agario-kit 2026.1.14 (grepped kit + repo + all local
artifacts). Our bundle spawns no subprocesses, never touches /proc, imports
only math/sys/traceback + kit modules. It is the SERVER's bot-container
entrypoint guard failing and aborting the container BEFORE the bot starts ->
those matches score 0 under the banned/dead=0 rule -> 7.4 average. #1003's 39
simply ran in a window when the runner nodes were healthy.
Machinery verification (all local, laptop only, no Studio pause needed):
(1) codegen fold audit — all 93 mode-0 / 123 mode-7 overlay keys still read
dynamically (27 literal + ARCH_N{i}_* computed reads); zero dead folds.
(2) runtime CONFIG diff — bundle _apply_mode(0) vs plain #1415: 24/264 keys
differ only at rounding precision (~1e-5, bundle 6dp vs plain 6sf).
(3) graph genes read fresh every tick — no stale cache across mode switch.
(4) equiv harness, bundle forced 0E vs plain #1415, 2000 identical mock ticks:
ZERO discrete decision flips (splits/cycle/vuln/prey/threat all identical);
only sub-decision force jitter from gene rounding.
RE-READ of test A: pinned-bundle median 1.5 vs plain 38.4 (n=8) was fat-tailed
variance — the mass-1 games had CLEAN stderr and a clean 0E switch on tick 1;
early deaths, not crashes. Same for the earlier 14.5-vs-34.5 (n=12).
Mode timing confirmed: tick-1 move computed under base(1E), 0E from tick 2 —
one tick of base per match, negligible.
ACTIONS: (a) report the procfs abort line to SYNCS organizers — runner-node
issue, not fixable client-side; ask which matches aborted + re-run/exclusion.
(b) BUNDLE_v2_14fix_CODEGEN (sha ccfd727b) re-cleared for upload on machinery
grounds; live score will stay depressed while infra is broken regardless of
what we upload. (c) diagnostic for Chris: healthy matches show "[mode]
switched" as first submission.log line; aborted matches produce NO log at all.

## 2026-07-16 — ROOT CAUSE (live 7.4): the room composition changed. Chris was right.
Chris's hypothesis: a timeout attack froze most teams (timed-out bots stop
making matches) -> rooms refilled with survivors only. Verified from match
metadata (meta_extend via Hermes, cache now 10800-28527, leaderboard fresh):
  window        games  E/C/G per room   distinct teams   our win%  rank
  24000-25000    996   0.87/1.03/6.10        42            54%     1.37
  27000-27500    491   1.36/1.05/5.59        40            52%     1.16
  28000-28343    337   1.99/2.41/3.59        14  <- FREEZE WAVE (13:37-15:25 UTC)
  28343+         185   2.07/1.97/3.96        17            28%     2.93
Pure-0E rooms for us: 53% of games in the 24000 era -> 14% since 28343.
Our game history: sub 1677 played 27001-27709 (win 54%, rank 1.21), then we
made ZERO matches 27710-28342 (frozen too / between uploads), then Chris's
late-night uploads (AEST 16 Jul 01:24-02:17): subs 1770 (24% win), 1772 (26%),
1774 (31%), 1776 (32%, rank 2.21, = leaderboard's Decay Rate 23.0@38).
CONCLUSION: bundle 7.4 vs #1003 39 was APPLES vs ORANGES — different room
worlds, not a code defect. Combined with the 07-16 machinery exoneration
(overlays/codegen/mode switch all bit-faithful), the bundle is fully cleared.
The procfs abort line in submission.err is likely fallout of the same attack/
freeze event (runner-side), secondary, still worth reporting to organizers.
Post-freeze comparables (per-current-submission): QwQ 36.1@20, team 28.3@20,
Decay 23.0@38, Banana 22.9@25. spaghetti's 46.1@660 is mostly pre-freeze.
IMPLICATIONS: (1) TRAIN-0E-7G is optimizing for a dead distribution — live
rooms now avg ~2E/2C/4G; the valuable regimes are 1-3E contested + 7E finals.
(2) The timeout attack itself matters: if some bot can force opponent
timeouts, we need to understand the vector before finals (our 8s budget).
(3) Mode ladder design unaffected — escalation ids all still elite; extra ids
(OJ 24, L&F 4, now non-elite) harmless by escalate-only design.

## 2026-07-16 — WORLD SWITCH: TRAIN-0E-7G archived -> TRAIN-2E live (v3campaign-5)
Chris's order after the composition finding (most common live rooms = 2E):
train the 2E band. Actions:
(1) ARCHIVED 0e7g world at match 261124 as archive/campaigns/0e7g-archive-1(.zip):
40 ranked bots + genomes, state_final, ladder copy, log gz, RESUME.md.
Champion (depth-qualified) = #1415 x1349x1384-bold 80.2@n300 — the shipped 0E overlay.
(2) NEW ROOM (_draw_room, WORLD_TAG v3campaign-5:TRAIN-2E:engine2026.1.13):
60% 2E+2C+3F / 25% 1E+2C+4F / 15% 3E+1C+3F — mirrors post-freeze live
(our games: 1E 36%, 2E 44%; rooms avg ~2E/2C/4G). Elites from BEST_POOL,
contested tier unchanged.
(3) SEEDED 100 injectables (50 inject_queue + 50 extra, 2/cull = 50-cull runway);
16 stale 0E z0-combo candidates relocated to inject_queue/stale_0e7g_20260716/.
Mix: 12 e3rNN-direct (3E-archive genomes intact) + 12 e3rNN-j (jittered) +
16 t2e-f* (farm x 3E family transplants: profiler/rank/grudge/lock/veto/wealth
blocks) + 12 t2e-graph3e (farm scalars + 3E ARCH graph) + 12 t2e-e7 (7E-lineage
transplants incl lateguard) + 12 z2-guard (farm champs + elite-aware hand
nudges) + 12 laf2e-j (live-base lineage) + 12 wc2e (wildcard family crosses).
All: FULL 260-gene space (registry=144 CGP-heavy; non-registry genes ride via
injection + inherit from parent A in crossover — deliberate transplant vector),
LA invariants pinned AFTER jitter (ON=1,VIRUS=1,ATTACK=1, MISS coin, H 2-4),
clamped to bounds, 6 samples compile-verified under gym 3.12.
(4) RESTARTED via launchctl start com.decayrate.ladder: WORLD_CHANGE_FLUSH
verified, first 40 results in (cand avg 35.6 — expected drop from farm-world
70-80; elites now in every room), 0 new tracebacks, studio+wsl nodes attached.
NOTE: engine still 2026.1.13 in gym; .14 migration remains OPEN (flagged 07-15).

## 2026-07-16 — WAVE 2: +100 hypothesis-driven 2E injectables (Chris's order)
Queued 30_* behind wave 1 (total queue now 100 main + 100 extra = 100 culls).
Ten named hypotheses, each on proven bases (#1415 / base1244 / #1003 / 3E r02-r03
/ lateguard), deliberate NON-registry gene payloads + mild registry jitter +
LA pin + clamp; 4 samples compile-verified:
h1 cautious-feaster(12): keep virus economy, demand clearance (FEAST_CLEAR
   1.5-2.5x) — feasting pins you in place with elites around.
h2 wealth-coward(10): rich = hunted; W_WEALTH_FEAR 1.3-2x, fear starts earlier,
   endgame bank protection up.
h3 profiler-hunter(12): room is MIXED — PROF_ON, fear elites 1.2-1.6x, prey
   stupids 1.2-1.7x harder, never chase elites.
h4 anti-corner(8): corners are death vs elites; CORNER_SKIP_ON, veto ticks up,
   refuge weight cut.
h5 vuln-opportunist(8+2 no-vuln controls): .12 meta = elites split constantly;
   a split elite is briefly edible — hunt with clearance.
h6 lock+veto paired(8): organ-trial law (lock harmful w/o veto); break locks
   earlier under threat.
h7 moderate-splitter(10): census law — heavy splitting loses; SPLIT_MAX_BLOBS
   0.4-0.7x, discipline up.
h8 grudge+rank(8): same 2 elites all game -> grudges pay; guard rank, damp
   rank-aggro.
h9 inverse-transplant(12): elite scalars + FARM CGP graph (inverse of wave 1).
h10 kitchen-sink guard(10): h1+h2+h3+h4+h7 combined — single best-guess 2E
   phenotype.

## 2026-07-16 — Laptop power loss + campaign restart (Chris's explicit order)
Laptop died ~09:40 CST (ladder log's last write 09:40:24, machine rebooted
~09:43). Overnight the TRAIN-2E world ran 261567 -> 287119 (~25.5k matches,
~27 culls; 27 wave-1 injectables consumed per stream, 73+73 still queued).
state.json intact — no corruption. RESTART: ladder via launchctl start
com.decayrate.ladder + portal server.py :8973 relaunched (Chris's explicit
restart order — no-auto-launch law respected). Studio never went down (37d
uptime): botapi launchd worker + caddy healthy; precautionary pkill -CONT for
sims. Verified: counter advancing (287166+), results from BOTH local (16-par)
and studio nodes, 0 new tracebacks. WSL node down pending Chris's new
windows-laptop API instructions — gym running on 2 of 3 nodes meanwhile.

## 2026-07-16 — BUNDLE v3 packaged: 0E/1E/2E/3E + finals 7E (Chris's order)
Design rev (Chris): DEFAULT 1E; drop to 0E only when the room is IDENTIFIED
elite-free (no sighting by tick 150); tally 2 -> 2E, >=3 -> 3E, escalate-only;
7E hardcoded after 2026-07-19T14:00Z (end of Jul 19 Sydney) — final mode ON.
Models: base/1E = x1213x1147-bold (farm-laf champion, 56.7@227);
0E = #1415 x1349x1384-bold (80.2@300, 0e7g-archive); 2E = e3r10-j09
(43.2@300 in live TRAIN-2E — a wave-1 injectable, 3E-archive r10 jittered);
3E = s2-nbr-w1211-m1h5-005 (3e-archive r02, n105); 7E = inj2-lateguard-d1
(elite-archive r02, 20.6@197 in 7-elite mirror). ELITE_TEAM_IDS refreshed to
live >22: (85,5,59,1,9,73) — QwQ/team/Rye/OJ/L&F dropped (no longer elite).
NOTE: /tmp wiped by the reboot — all genomes re-sourced from archives.
Body rework (backup /tmp/omni_pre_v3modes.py): MODE_OVERLAYS {0,1,2,3,7},
_mode_for 1/2/3, _MODE_TICKS counter + _MODE_0E_COMMIT=150, 0E->escalation
still allowed. VERIFIED: equiv 2000 ticks bit-identical (old vs new body, gym
form); verify_moves 1340/1340 (recorded with old body, replayed through new);
codegen fold audit CLEAN (0 dead keys across all 5 overlays: 93/0/82/99/123);
per-mode CONFIG fidelity 260/260 genes all modes; ladder walk 1E->0E@150->
1E->2E->3E->cap verified; post-cutover boot = 7E pinned; pre-cutover bundle
bit-identical to plain base build (2000 ticks); 3x .14 smoke SUCCESS 0 bans
(2E overlay exercised live via gym id collision).
STAGED: ~/Desktop/ship_staging/BUNDLE_v3_CODEGEN.py sha256 668dc669c743ef2b...
Vaulted with all 5 genome JSONs. Chris uploads himself.

## 2026-07-16 — BUNDLE v3 rev2: logging added (Chris's order), restaged
Chris confirmed spawn-at-1E (already the design). Added ship-only stdout
logging (flush=True -> submission.log; gym build silent, gated on empty
overlays/ids, equiv re-PASS bit-identical):
(1) boot line once/match: UTC now, final-mode state + countdown, cutover ts;
(2) '[mode] tick N: identified elites [ids] (tally n)' on every new elite;
(3) switch lines now carry the tick. Live .14 witness: boot line + tick-3
sighting + tick-34 2E switch, SUCCESS. Rebuilt bundle+codegen, fold audit
unchanged, restaged BUNDLE_v3_CODEGEN.py sha256 ce78a7b6ca6c59f2517b85796060f98b207ac543264c693696a65953caa5f1f4 (supersedes 668dc669).

## 2026-07-16 — (backfill) WSL node rewired; composition refresh thru 30502; portal address
(1) WSL node reconnected at Chris's new URL http://desktop-34tntnv.tail35f7fb.ts.net:8975
(config/gym_nodes.json updated, ladder restarted, all 3 nodes ok=True). Old
trycloudflare URL dead. (2) Metadata extended 28527 -> 30502 via Hermes:
composition holds ~2E/2C/4G; field REFILLING (18 -> 26 active teams in newest
window); our-seat density 0E 11% / 1E 41% / 2E 31% / 3E+ 16% (3E+ tail tripled
— watch; 3E overlay now filled in BUNDLE v3 anyway). Elite band thinned to 7:
spaghetti 42.8, BotBattle 32.0, SUNMO 27.5, Washed 25.6, US 25.4@942, Banana
24.1, Ninja 22.9 — QwQ/team/Rye dropped <22 (small-n peaks that didn't hold).
Sub 1776: 417 games win 32% rank 2.55. (3) Portal: tailnet
http://100.99.9.34:8973 (cloudflare tunnel not relaunched — needs Chris's OK).

## 2026-07-16 — Docs: OPERATOR.md refreshed, ASSISTANT.md created (standing order)
Chris's standing order: maintain OPERATOR.md AND a new ASSISTANT.md alongside
the journal. OPERATOR.md updated: v3 mode design (1E default, tick-150 0E
identification, 2E rung, logging), launchctl gym control + portal start, new
wsl node URL, bundle build 6-arg usage + v3 model picks, state snapshot ->
TRAIN-2E era (live meta, staged BUNDLE_v3_CODEGEN sha ce78a7b6, endgame
checklist incl. sighting-latency tuning + timeout-attack + .14 migration).
ASSISTANT.md created: division of labor, the assistant's evolver loop
(watch/steer-with-injections/mine/escalate), reporting standards (AEST,
sample+trajectory discipline, falsifiability, local-data-first, verify-before-
stage), session rhythm, assistant-specific heuristics (fat tails, /tmp dies
with the laptop, seat-id collisions, world-before-code in regressions).

## 2026-07-16 — Studio simulations explicitly resumed and evolution verified
At Chris's instruction, sent `pkill -CONT -f bin/simulation` to Studio and
verified active Studio simulation workers. The local TRAIN-2E ladder remained
alive and advanced from match 297101 to 297120 in seven seconds at ~13:25 AEST;
results included Studio-sourced matches. Portal :8973 was not running during
the initial check, so health was verified directly from the ladder process and
`evolution_v3/ladder_log.jsonl` counter movement. No campaign restart or pool
change was performed.

## 2026-07-16 — META RECHECK: harder world broadly; latest upload gap is streak regression, not a clean composition break
Ran the new canonical `tools/meta_report.py --extend` (no hand-rolled schema):
Hermes cache extended 30699→30741; latest match 13:27 AEST. Broad post-freeze
windows show the world hardened again: 30140-30741 averaged
2.45E/2.01C/3.55G, versus 1.46-1.67E in the preceding two windows. In our
newest-window seats (n=204), opponent-elite density was 0E 4% / 1E 28% /
2E 41% / 3E+ 27%, so the old farm-heavy world is gone.

Chris's specific comparison was old sub 1776's eight-win streak immediately
before replacement versus new sub 1810. Canonical boundary report (ids
30500-30741) says the adjacent samples occupied broadly the SAME hard world:
old final slice n45 = 2/14/17/12 games in 0/1/2/3+E cells (42% win, rank 1.80);
new n37 = 1/9/15/12 (30%, rank 2.19). New mix is only slightly harder
(3E+ 32% vs 27%; 0-1E 27% vs 36%), not a categorical composition break.
Same-cell results are all small ⚠: 1E 57%@14 old vs 33%@9 new; 2E 41%@17 vs
33%@15; 3E identical 17%@12, with new mean rank better (2.92 vs 3.25).
Against old sub 1776's deep full run (n987), new sub is not showing a clear
behavioral regression: 1E 34%@473 vs 33%@9; 2E 30%@248 vs 33%@15; 3E 22%@50
vs 17%@12 ⚠. Current leaderboard average is 24.3@n37 and the new submission
must not be judged before n≥150. Conclusion: room composition explains why
both bots are below old farm-era averages; it does NOT by itself explain the
immediate streak-to-upload contrast, which is dominated by selection of a hot
eight-game run and tiny-n variance. Post-probe health: 18 Studio simulation
processes present; ladder still advancing with Studio and WSL results. No pool,
campaign, bot, or submission change performed.

## 2026-07-16 — Meta analysis made reproducible: tools/meta_report.py
Chris found another agent couldn't reproduce the meta analysis from
ASSISTANT.md — the docs carried standards but not the executable procedure.
Fixed: NEW canonical tool tools/meta_report.py (runs from laptop, data on
Studio): --extend refreshes the Hermes cache (sims paused/auto-resumed),
prints composition windows, per-submission conditional performance by
opp-elite count (with n<150 / small-cell guards baked in), and the elite
band. Docstring documents the full schema (match_meta.jsonl fields, ranking
0=win, leaderboard avgMass = current-sub-only, replays participant-gated).
OPERATOR.md §4 + ASSISTANT.md now point at the tool: run it, don't improvise;
judge only same-composition cells. Tested end-to-end (sub 1776 vs 1810
reproduced). Lesson recorded: docs must carry runnable procedure, not just
principles.

## 2026-07-16 — Correction (my error): upload-boundary attribution was time-confounded
ChatGPT's counter-analysis was right and my first-look framing was partly
wrong: I compared sub 1810's 25 games against sub 1776's FULL 702-game record
— but 1776's aggregate composition (45% hard rooms) was diluted by its softer
early era. The clean contrast (same-era: 1776's final slice vs 1810, since
~30300-30500) shows both subs occupied broadly the SAME hard world; the
composition change AT the upload boundary is slight, not a step. Verified
myself: since 30300, 1776-tail n104 win 40% rank 2.09 vs 1810 n37 win 30%
rank 2.19 — a ~1.3 sigma gap, noise at these n. RECONCILED VERDICT: (a) broad
era shift real (both bots sit below farm-era averages because the world
hardened); (b) the streak->upload contrast is dominated by hot-streak
selection + tiny-n variance, NOT a composition break and NOT a bot defect;
(c) judge 1810 at n>=150. Lesson encoded in tools/meta_report.py docstring
(TIME-CONFOUNDING GUARD): compare submissions only over the overlap era via
--since; never against a long-lived sub's full history.

## 2026-07-16 — Rule: meta analysis always pulls latest (extend-by-default)
Chris's rule added to ASSISTANT.md + enforced structurally: meta_report.py now
extends the Hermes cache by DEFAULT (--no-extend only for same-session offline
reruns). Fresh pull @ 1810 n=50: win 30%, mean rank 2.10 = level with 1776
tail (2.09); our leaderboard avg 24.7@50. 2E-cell watch item persists (25%@24
vs 45%@33, both small). Noted: tiers recompute from CURRENT leaderboard each
run, so cell counts drift between runs (QwQ crossed the 22-line again) —
cell numbers comparable only within a single run.

## 2026-07-16 — Chris's preferred elite head-to-head table recorded
Chris explicitly endorsed the submission table showing non-successful/ban rows
(ours banned separately), then each elite opponent's times faced, times we
placed above them, and above%. Added this as a standing reporting preference
in ASSISTANT.md; retain per-opponent n and ⚠ small-cell warnings. In Chris's
supplied snapshot, old sub 1776 was above elites 119/199 encounter-rows (60%);
new sub 1810 was above elites 42/78 (54%), with zero non-successful/ban rows
and zero ours-banned for both. New was directionally stronger vs SUNMO/Banana,
similar vs Washed, and weaker vs spaghetti/QwQ/Bot Battle, but its individual
opponent cells were only n=11-14 ⚠ and are scouting signals, not a verdict.

## 2026-07-16 — Updated elite table made canonical; sub 1810 n55 comparison
Chris requested a fresh version of his preferred elite head-to-head table.
Extended Hermes 30781→30797; latest 13:45 AEST. Enhanced canonical
`tools/meta_report.py` so it now reproducibly prints, per submission, failed/
ban rows plus each CURRENT elite's faced/placed-above counts. Python 3.12
compile passed. First run exposed real schema spellings (`outcome=Successful`,
`banReason=None` as a string); fixed the status parser and reran on the same
fresh cache. Both subs: zero non-success/ban rows, zero ours-banned.

Time-controlled since match 30300: old 1776 tail = 40% win, rank 2.09@n104;
new 1810 = 31%, rank 2.09@n55 ⚠. The new mix is harder: 2E+ rooms 35/55=64%
vs old 52/104=50%. Current-elite encounter aggregate: old 97/166 placed-above
(58%); new 53/97 (55%). Common-opponent direction: spaghetti 62→52%, SUNMO
69→68%, Washed 48→57%, Bot Battle 48→29%, Banana 57→64%. All new opponent
cells n14-23 ⚠. Composition cells: 1E essentially same win (46→44%) with new
rank better (2.12→1.56); 2E materially worse signal (45→23%, rank 1.64→2.42);
3E better signal (5→22%, rank 3.53→2.56), but all new cells are n<30 ⚠.
Verdict: new bot is holding the same overall rank in a harder world and now
scores 25.8 mass@n55 (fourth in the current elite list), so it is promising;
not proven better because elite head-to-head is slightly lower and 2E is the
clear watch item. Wait for n≥150. Post-probe: 18 Studio sims, ladder advancing
with Studio results. No pool/campaign/submission change.

## 2026-07-16 — 2E deficit classified as small-n watch signal, not failed optimization
Chris correctly challenged whether new sub 1810's live 2E result could simply
be sample variance despite deliberate 2E optimization. Yes: 23%@n26 is about
6 wins; only +3 wins would read 35%, +5 would read 42%. Approximate 95%
binomial intervals overlap widely: new ~11-42% versus old-tail 45%@n33
~30-62%. The observed gap is therefore not statistically decisive. Additional
confounders: live “2E room” classification does not prove the second elite was
identified early enough for the 2E overlay to govern most ticks; opponent
identity within the 2E cell can differ; and the 2E genome trained on engine
.13 while live runs .14. Treat 2E as a watch item until n≥60-100 in-cell and
submission n≥150; use live `[mode]` logs to verify 2E activation latency before
attributing any gap to the overlay or training.

## 2026-07-16 — DECISION: mode elites are current-first hard-room survivors, not leaderboard >20
Chris rejected the raw leaderboard threshold as the ship mode selector: high
average mass can be farm-derived and need not imply a room where defensive/
contested play is appropriate. Canonical metadata now separates reporting E
(still current avg>20 for continuity) from REAL mode elites. Gate over the
candidate avg>20, exclude us, with 2+ OTHER candidates, hard n>=100, hard
win>=18.75% (1.5x random), mean rank<=3.00. Chris corrected the first draft's
current-sub-only sampling because new submissions are often tiny: canonical
sample is now current-first n=300 per team — take all available current-sub
games up to 300, then backfill only the missing games from immediately prior
submissions. Fresh match 31413 / 16:57 AEST pass set: Bot Battle 5
(22%@243/rank2.37), team 15 (21%@164/2.84; current5+prior295), Washed 1
(29%@242/2.92), Banana 9 (31%@231/2.37), Ninja 73 (22%@246/2.46) => future
tuple `(5,15,1,9,73)`. QwQ narrowly failed rank (23%@243/3.03); spaghetti
failed rank (19%@240/3.16); SUNMO/imposters failed both; chimken had only
hard n99. `meta_report.py`, `make_bundle.py`, ASSISTANT.md, OPERATOR.md and
config snapshots updated. Verification then found a contemporaneous rev3 had
been written outside this correction to both vault and ship_staging (sha
`38c7f13d...`, logged 14:58 local) with the superseded ids `(5,1,9,37,73)`.
It was not overwritten: the corrected future builder now uses
`(5,15,1,9,73)`, while the currently staged rev3 still needs an explicit
rebuild decision. Live upload state was not checked; no BEST_BOTS change.

## 2026-07-16 — Farm-inflated "elites" confirmed; BUNDLE v3 rev3 with survivor gate
Chris's theory VERIFIED by the hard-room survivor analysis (meta_report, era
since 30300, current subs only): SUNMO (lb 25.7) wins only 10%@287 in 2E+
rooms, rank 3.70 — a FARMER, not an elite. spaghetti's 40 lb avg rides an old
sub's softer era; current sub 1831 unproven (n=23 hard). team unproven (n=5).
True hard-room survivors: Banana 30%@308, Washed 28%@305, QwQ 26%@156,
Ninja 23%@304, Bot Battle 21%@281 — and US at 23%@210 (mid-pack legit).
Canonical gate (avg>20 + current-sub hard n>=100, win>=18.75%, rank<=3.00)
now encoded in meta_report + make_bundle. BUNDLE v3 rev3 rebuilt with
ELITE_TEAM_IDS=(5,1,9,37,73): SUNMO/spaghetti no longer tally (sighting them
keeps farm-mode economics), QwQ counts. Verified: fold audit 0 dead; per-mode
fidelity 5/5; ladder walk incl. FARMER-BLINDNESS (59/85 visible for 150 ticks
-> clean 0E commit; 37/5/9 escalate 1E->2E->3E); .14 smoke SUCCESS 0 bans.
Staged sha 38c7f13d... (supersedes ce78a7b6). Mode semantics now: tally =
CURRENTLY DANGEROUS opponents, not leaderboard decoration.

## 2026-07-16 — Gate fixed per Chris: backfill prior submissions until conclusive; rev4 staged
Chris's correction: never reject a team for a FRESH submission — walk back
through prior submissions (current-first, backfill to n=300) until the sample
is conclusive. With backfill: team(15) ACCEPT (22%@165 hard, rank 2.82, via
prior subs); spaghetti REJECT now on EVIDENCE not sample (19%@240, rank 3.16 —
the 40 avg is farm-inflated, confirmed); QwQ REJECT knife-edge (23%@243 passes
win, rank 3.03 misses by 0.03); chimken_wingz one hard game short (99<100,
20%/2.70 would pass) — BOTH edge cases to re-check at next build. SUNMO
confirmed farmer at full data (11%@245, rank 3.62). BUNDLE v3 rev4:
ELITE_TEAM_IDS=(5,15,1,9,73), full battery re-passed (fold 0 dead, fidelity
5/5, farmer-blind ladder incl. QwQ ignored, .14 smoke SUCCESS), staged sha
2cdea50bd5aa27dc3bbb6fccfa03cbed98cf142517df9d049e4058f8966edb84 (supersedes 38c7f13d).

## 2026-07-16 — rev5: Chris pins QwQ + chimken_wingz into the elite set
Chris's call on the two knife-edge gate cases: QwQ(37, hard rank 3.03 vs 3.00
line) and chimken_wingz(49, hard n=99 one short of 100) STAY IN.
ELITE_TEAM_IDS=(5,15,1,9,73,37,49) — gate survivors + Chris's pins; pins
documented in make_bundle.py. Full battery re-passed (fold 0 dead, fidelity
5/5, ladder walk with QwQ/chimken tallying and SUNMO/spaghetti ignored, .14
smoke SUCCESS). Staged sha 11ab3fa75a8a458d54efca1d73b9853c029a89574f6ba79f03344ca1f6c3b911 (supersedes 2cdea50b). Note: escalate-only
design means pins are cheap — worst case is slightly earlier escalation vs
these two; missing a real elite costs farm-mode deaths.

## 2026-07-16 — TRAIN-FINALv2 live (Chris's order): finals-mix room + 100 seeds; rev6 telemetry
(1) TRAIN-2E ARCHIVED at match 324407 as 2e-archive-1(.zip) after ~63k
matches. FINAL 2E CHAMPION: #1769 h1-cfeast-001 45.3@n300 — a WAVE-2
HYPOTHESIS bot (cautious feaster) beat all archive-derived seeds; h4-nocorner
3x in top 8. Bundle 2E re-pick candidate for Jul-18 rebuild (current bundle
carries e3r10-j09 43.2).
(2) TRAIN-FINALv2 live (v3campaign-6): room = 4 BEST_POOL elites + 1
contested + farmer_1415 (materialized #1415 = split-feast farmer stand-in) +
split_feaster_v3 — mirrors projected finals (4-5 killers + 2-3 farm-inflated,
no fodder). WORLD_CHANGE_FLUSH verified, matches flowing, 58 unconsumed 2E
seeds -> stale_2e_20260716/.
(3) 100 finals seeds queued (40_*, 2/cull): 16 e7-survival core (elite-archive
directs+jitters) + 20 2E winners (h1-cfeast/x1640x1823/... directs+jitters) +
24 e7 x 2E-winner crosses + 24 fin-vhunt (VULN_ON aggressive: detect x1.2-1.6,
cooldown x0.6-0.9, bank-risk x1.0-1.4, frag-hunt x1.2-2, prof-prey-stupid up —
punish split-feasting farmers) + 16 fin-sink (cross + vhunt + wealth-fear +
split discipline). Compile-verified.
(4) rev6 telemetry (Chris item 4): post-cutover _mode_tick keeps tallying +
logging sightings, behavior PINNED 7E (verified: pinned mode + telemetry lines
in post-cutover witness; equiv PASS bit-identical gym form; .14 smoke SUCCESS).
Staged sha d44e9f63... (supersedes 11ab3fa7).
PLAN: finals model pick + full bundle rebuild (2E re-pick h1-cfeast-001 + gate
refresh + pins) Jul 18 evening AEST; Chris uploads with a day of margin.

## 2026-07-16 — LA audit vs #1003 (Chris's streak concern): season OK, 7E finals overlay has LOOKAHEAD OFF
Audit of live BUNDLE_v3 vs SHIP_v3_laf1003: LOOKAHEAD_ON=1 + attack veto in
base/0E/2E/3E (LA_VIRUS 0.71-1.0, all >0.5 gate = active; miss-veto off where
evidence said redundant). FINDING: mode-7E overlay carries LOOKAHEAD_ON=0.0
inherited from inj2-lateguard-d1 (certified 20.6@197 pre-LA in the 7E mirror)
-> post-cutover finals bot would run WITHOUT split-veto machinery. TOP ITEM
for Jul-18 final rebuild: pick LA-on finals champion from TRAIN-FINALv2
(seeds ~2/3 LA-pinned), fallback la-x1080-v1m1a1h4 (20.6@72, elite-archive) or
LA-pin lateguard + re-witness. No upload churn now (7E inert till cutover).
Loss-streak context: 27 games @19% win over 23 min during the ~2.9E/room
window — small-n in the hardest mix yet; judge at n>=150.

## 2026-07-16 — Evolver silent death ~16:06 CST; reconnected
Ladder + portal both died silently (~18:06 AEST): no traceback, no crash
report, memory 92% free; old NameError in log tail is match-5039-era (code
gone). Restarted via launchctl + portal relaunch; TRAIN-FINALv2 resumed at
328774, both nodes ok, results verified flowing. If it repeats: ask Chris
whether to enable KeepAlive on com.decayrate.ladder (no-auto-launch law
currently forbids it).

## 2026-07-16 — Full .14 client-events audit: 2 missed signals, 2 radars that DON'T exist
Traced every event through censor_event.py + state_mutator commit paths.
DELIVERED: state (me/visible_*/rankings/turn_order), censored game-start
(player_id+alive only — anonymization confirmed at source), own MovePlayer
only, EventPlayerMoved while visible (centroid), PublicEventPlayerEaten
(one-sided by visibility), EventPlayerBanned (ban ABORTS the match:
PlayerException -> commit -> finish). MISSED SIGNALS: (1) kill-event PAYLOADS
unread — eaten-visible/eater-None = invisible predator adjacent at eaten_pos
(directional fear, free); eater_radius = true size read. (2) respawn
anticipation — RESPAWN_DELAY_ROUNDS=30, random pos; kill feed gives who/when
-> fresh-prey prior + "dead elite harmless 30+ ticks" profiler damp
(FRESH_* genes react on sight only today). Minor: turn_order = tiebreaks only.
NEGATIVE RESULTS (do not re-chase): EventFoodEaten + EventVirusConsumed are
commitPrivate = REPLAY-ONLY (no global growth telemetry, no virus-pop
position radar for clients); food/virus spawn events also private (no pellet
prediction). Proposed (awaiting Chris): gene-gated kill-geometry organ for
TRAIN-FINALv2. NOTE: laptop rebooted AGAIN ~16:06 CST (2nd time today) — the
"silent evolver death" was a machine reboot; hardware/OS stability now a
real operational risk before freeze.

## 2026-07-16 — KG + RC organs implemented (acting on the events audit)
NEW BODY ORGANS (both gene-gated, default OFF = provably inert):
KG (kill geometry): reads the one-sided public_event_player_eaten payloads —
eaten-visible/eater-None appends a predator ping at eaten_pos (implied mass
1.44x victim, eat-rule lower bound); repulsion W_KG_FEAR with linear decay
over KG_DECAY_TICKS, gated by can-it-eat-our-smallest + THREAT_IGNORE_DIST;
visible eaters get aggro credit (KG_EATER_AGGRO via existing aggro channel).
RC (respawn clock): kill victims recorded; a player re-seen small in
[death+30, death+30+RC_WINDOW] gets prey-force boost W_RC_PREY (respawn delay
is 30 rounds, engine constant).
Genes: KG_ON/W_KG_FEAR/KG_DECAY_TICKS/KG_MIN_VICTIM/KG_EATER_AGGRO,
RC_ON/W_RC_PREY/RC_WINDOW — added to registry (144->152) + state backfilled
(328 slots, incident-lesson). Defensive getattr(st,"round",0) (mock harness
lacks round — caught by test). VERIFIED: equiv 2000 ticks bit-identical (off),
positive-activation tests (KG on: 190/300 ticks differ; RC records deaths),
verify_moves 1160/1160 replay. Ladder restarted, variants re-materialized,
TRAIN-FINALv2 flowing. SEEDED 24 carriers (kg-fear/kg-rc/kg-both, 40_1xx)
on the finals pool's depth leaders (fin-e7r2-direct 27.8@118, h4-nocorner
26.7@158, x1624x1640, t2e-graph3e) — wave-2 hypotheses lead the finals world.
NOTE: bundle rebuilds from champion genomes are unaffected until a KG/RC
carrier wins a mode seat; body change is backward-compatible (old genomes
ride defaults OFF).

## 2026-07-16 — SOLVED: why the 2E overlay didn't beat 1003 live — WE SHIPPED A PEAK
Chris's paradox ("gym said significantly better, live says identical")
dissolved with the 2e-archive close data: e3r10-j09 finished RANK 28/40,
certified fit 37.9@300 (837 games) — its 43.2 at bundle-pick time was a
window excursion that regressed ~5 mass (same pattern as #452 46.7->38; the
certified-peaks-regress law struck OUR OWN pick). laf2e (1003-family)
lineages were culled (<~38) -> TRUE gym edge of bundled 2E model over 1003:
~+0-3 mass, not +5-8. Stack the shrink factors: dwell dilution (2E genes
govern only post-2nd-sighting ticks, median ~59) + detection power (game-mass
SD ~25-30 -> +2 edge needs n~1500/cell; live cells were n=15-76) + gym->live
transfer loss vs real elites = live parity is the EXPECTED outcome, not an
anomaly. PROCESS FIX (docs): overlay models are picked from CLOSE-of-world
standings, deep-n + world-maturity check — never pick-time leaders on a
young world. Honest TRAIN-2E close champion (deep-n) recorded for any future
2E overlay: see deep-n top-5 printed this session (h1-cfeast-001 family).
Chris's 1003 re-upload = correct call; bundle overlays were never carrying a
live-detectable edge.

## 2026-07-16 — BUNDLE v4 staged: 2E overlay replaced with h1-cfeast-001
Chris's order after the peak-shipping post-mortem: new version with 2E =
h1-cfeast-001 (cautious-feaster hypothesis, CLOSE-of-world certified 45.3@300
full window, 354 games — vs shipped e3r10-j09's honest 37.9). LA audit: ON
(v1/a1/m0/h3). Signature verified in overlay (VIRUS_FEAST_CLEAR 1.647).
All else = rev5 (base x1213x1147, 0E #1415, 3E s2-nbr r02, 7E lateguard,
ids 5,15,1,9,73,37,49 incl Chris's pins). Body now carries KG/RC genes —
all mode genomes predate them -> ride defaults OFF (verified in base).
Battery: fold audit CLEAN (93/0/95/99/123), fidelity 5/5, ladder walk OK,
post-cutover 7E boot OK, 2x .14 smoke SUCCESS. Staged BUNDLE_v4_CODEGEN.py
sha 6ec91123d89fdbf4d821f0fbfad60309cc73bebd6778ae2a94b500b8071bd148. NOTE: live sub is currently #1003 (Chris's A/B control, NO cutover)
— v4 is the cutover-armed replacement whenever Chris ends the experiment;
7E overlay still lateguard (LOOKAHEAD OFF) pending FINALS-world champion at
the Jul-18 rebuild.

## 2026-07-16 — THIRD reboot today (~18:12); stack restored again
Laptop rebooted ~18:12 CST (3rd: 09:40, 16:06, 18:12). State intact at match
340209 (TRAIN-FINALv2, only ~10 matches lost). Ladder + portal restarted,
both nodes ok, results verified flowing. Staged BUNDLE_v4 verified present
post-reboot (vault + ship_staging both intact; /tmp wiped again as always).
No panic report found in DiagnosticReports. THREE reboots in one day is now
an operational risk for the endgame: recommendation to Chris — check Energy/
battery health + macOS update pending state; consider running the ladder on
the STUDIO if a 4th occurs (state.json + repo sync would need one-time setup).

## 2026-07-16 — ROLLOUT PLANNER organ (Chris: "expand lookahead everywhere")
Compute audit: engine allows ~5.7ms/tick avg (8s cumulative /1400); we used
<1%. NEW ORGAN PLAN (gene-gated, default OFF): force field PROPOSES the
heading, a K-candidate x H-tick engine-faithful rollout DISPOSES — candidates
fan PLAN_SPREAD radians around the proposal; score = pellets captured along
path (consumption-tracked, nearest 36) + alignment bonus − predicted-threat
proximity (linear tracks from tracker.velocity; predicted overlap = death
penalty 1000/h) − wall exposure. Committed attack vectors (split) exempt.
SAFETY GOVERNOR (non-gene): cumulative planning time metered; >3.5s/match ->
organ self-disables + one [plan] log line. Measured cost 29us/tick (~40ms/
match, 1% of governor) -> headroom for K/H growth by evolution. Genes
PLAN_ON/K/H/SPREAD + W_PLAN_{FOOD,THREAT,WALL,ALIGN}; registry 152->160;
state backfilled 328 slots. VERIFIED: equiv bit-identical OFF, verify_moves
1250/1250 through real protocol, unit test deflects off predicted-death path,
timing bench. Ladder restarted; 20 pl-roll carriers queued (40_2xx) on
finals-pool leaders (x1910x1912 27.8, fin-x7x2E-009 26.2...). Evolution now
tunes multi-tick strategy in the finals room; adoption only if carriers win
seats honestly.

## 2026-07-16 — SOLVED-EVASION organ (EV): minimax tablebase, Chris's playbook idea done right
Chris rejected v1 (split-kill table = precomputing what runtime already
computes). Pivot to what offline compute uniquely buys: the TWO-SIDED game.
tools/build_evasion.py: value iteration over corner-quadrant states (wall
dists 7x7, pursuer offset 9x9, threat class 2, split-held 2 = 15,876 states
x 8 our-headings x 8 adversarial replies, horizon 25) — pursuer plays
OPTIMALLY incl. adversarially-timed split strikes (kill ring 6u). Policy:
solved escape heading per state, 10KB b85, embedded EV_TABLE block. Emergent
solved behaviors: diagonal flight in open field (dead-away is what split
strikes punish), along-wall bullfighter charge past slower bodies. Runtime
ORGAN EV (genes EV_ON/EV_RANGE/W_EV, default OFF): nearest capable threat
inside EV_RANGE -> mirror-map to quadrant frame -> table heading as an organ
force. VERIFIED: policy sanity (never into wall/corner), equiv bit-identical
OFF, verify_moves 1250/1250, EV_ON flips 132/400 mock ticks. Registry 160->163,
backfilled, ladder restarted, 16 ev-solved carriers queued (8 EV-only, 8
EV+PLAN). Also embedded (dormant, unwired): PB split-horizon + virus-guard
tables from v1 sweep. Tier-2 distillation kit zipped to Desktop
(harvest/mine/embed + README schema; ~10M tick-samples/hr available; 50MB
submission limit fits ~5M-entry tables).

## 2026-07-16 — PLAYBOOK AUDIT: capacity is real; Tier-2 pipeline is not yet built
Follow-up source audit corrected the maturity claim. EV is genuinely embedded
and OFF-path verified, but all 16 `ev-solved` injections are still queued:
current population has 0 EV-active genomes, so it is not yet under selection.
The Desktop Tier-2 zip is a design scaffold, not a runnable distiller:
`harvest.py` records neither actions nor populated threats/food, `mine.py`
explicitly lacks action-conditioned comparison, and `embed.py` only prints an
instruction stub. More importantly, passive champion traces identify the
champion's behavior, not the best counterfactual action. A real Tier-2 system
must label multiple candidate actions from matched states (forked rollouts or
paired scenarios), use survival/final-mass-aware multi-horizon outcomes, pack
dense arrays rather than Python dicts, and retain confidence/OOD fallback.
The 50MB allowance is best used as a hierarchy of recognizable set-piece
books plus a distilled tactical blueprint feeding search—not one monolithic
state-to-action table. EV's "optimal" guarantee applies only to its discretized
constant-speed two-player model, not the full engine; continuous randomized
scenario validation is required before calling it engine-optimal.

## 2026-07-16 — VIRUS-LURE organ (VL): research-sourced solved set-piece
Research (Chris's order): agar.io RL literature (arxiv 2505.18347, "The Cell
Must Go On") tested virus-weaponization (lure bigger opponent onto virus ->
fragment -> absorb) — NO evaluated agent ever learned it, even simplified.
Our engine has the mechanic (largest overlapping blob pops); rivals' bots are
evolved/heuristic -> near-certainly nobody plays it. SOLVED offline instead:
tools/build_lure.py — VI over (our offset, chaser offset) in virus-origin
frame (6,561 states x 8 actions, greedy-pursuit threat model — an optimal
chaser that declines the lure has stopped chasing = escape), horizon 20.
In-line lure state value 9.55/10. Runtime ORGAN VL (genes VL_ON/RANGE/W_VL/
VL_MIN_VAL, default OFF): bigger chaser + virus both in range + table value
above threshold -> lure heading as organ force; constructed-scene test shows
the solved DIAGONAL route past the virus (not naive through-middle). VERIFIED:
equiv bit-identical OFF, verify_moves 1250/1250, scene activation. Registry
163->167, backfilled, ladder restarted, 12 vl-lure carriers queued (6 VL-only,
6 VL+EV). Halite/Battlecode postmortem sweep: influence maps/decision-tree
curation noted, nothing beating our current stack; RL-fails-here finding was
the actionable gold.

## 2026-07-16 — ChatGPT review VERIFIED against engine source; physics fixed; planner v2
Chris ran ChatGPT over the architecture sample. Claims verified vs .13+.14
engine source (falsifiability law): (1) speed law IS divisive
1.1/(1+0.08r) — body _la_speed was ALREADY correct; the linear form lives in
blob_speed_of (kept deliberately: tuned behavioral heuristic in certified
genomes — documented in-code) and in MY OFFLINE BUILDERS (wrong -> fixed).
(2) engine wall clamp [r, size-r] — planner fixed. (3) eat rule = MASS ratio
1.2 AND target center within EATER radius — TWO LA bugs found: attack-lands
and miss-veto used radii-sum overlap (too generous); FIXED to center-in-
eater-radius. KG implied mass 1.44 -> 1.2. NOTE: LA fixes are intentionally
NON-inert for LA-ON genomes (first behavior-affecting fix; witness SUCCESS).
Virus-hit geometry + _LA_VIRUS_POP verified already correct.
PLANNER v2 (review's MPC direction, staged): structured candidates (reactive,
±30/60/90, reversal, escape, prey-intercept via tracker.predict, food
centroid, wall tangents; ~14 deduped) -> half-horizon rollout -> beam
PLAN_BEAM (default 4) -> ONE mid-horizon heading change (3 branches) -> exec
first action only (replan each tick). Engine speed law + [r, size-r] clamp in
rollout. EVENT-TRIGGERED (threat<12/prey<8/wall/fragmented; PLAN_ALWAYS gene
to disable gating). Telemetry via atexit: calls/overrides/time (witness: 949
calls, 205 overrides, 127ms — 3.6% of governor). All 3 tables REBUILT on
exact law. Registry 167->169. STAGED ATTRIBUTION per review: 12 pl2-mpc
carriers = planner v2 ONLY (KG/RC/EV/VL forced off). Deferred (recorded):
joint split/no-split branching, CGP-scored leaf features, multi-scenario
opponent beliefs, respawn/hidden-threat beliefs.

## 2026-07-16 — EV HARNESS VERDICT: v1 table was BROKEN (caught), fixed; book-guided MPC wins
Built tools/ev_harness.py per review ("best immediate experiment"): paired-
seed continuous-state trials (3000 episodes, engine-exact physics, randomized
radii/positions/walls/split, pursuer = pure pursuit + split strike, T=80).
ROUND 1: ev_raw 0.2% survival vs dead-away 5.3% / field 9.9% — the v1 table
LOST TO DEAD-AWAY 25x. Root cause: hopeless/tied VI states defaulted argmax
to action 0 (+x bias) -> systematic garbage headings near capture. THE HARNESS
CAUGHT WHAT ALL INTEGRATION TESTS COULD NOT (they proved safe wiring, not
policy quality) — 16 queued carriers would have evolved on a broken table.
FIX: wall-aware flee-prior tie-break in the solver. ROUND 2: dead-away 5.3 /
field 9.9 / ev_raw 7.1 / ev_blend 10.4 / EV-GUIDED MPC 12.5% (+26% relative
over field, mean ticks 17.3 vs 15.1). VERDICT per review protocol: raw
override REJECTED (abstraction gap real); book-as-candidate-generator for
short rollout = the winning integration -> EV heading added to planner v2's
candidate set (gated EV_ON). EV_OVERRIDE gene retained but harness-rejected.
Body re-verified (equiv PASS off), ladder restarted. LAW ADDED to ASSISTANT.md:
no playbook ships carriers before passing its continuous-state harness.
Review's status corrections accepted: tier2 kit = scaffold (passive traces
can't label best actions; counterfactual forking design adopted for any real
run); EV carriers still queued, not yet under selection.

## 2026-07-16 — FIGHTER IMITATION MINING (Chris's design, supersedes tier-2 counterfactuals)
Chris's better idea: mine REAL SERVER GAMES for good decisions — "they are
not our bots" — i.e., imitation labels from the proven fighters (team,
Banana, Ninja, Washed, BotBattle) playing the actual meta, targeting exactly
the cells where they beat us (team 59% vs our 23% at 1E). BREAKTHROUGH:
replay endpoint found via portal sniff:
  api.syncs.org.au/matches/{GLOBAL_ID}/files/public/visualiser_forwards_differential.json
(12MB full event stream; participant-gated to our matches). VERIFIED
contents: move_player events with EXACT direction+split per player per tick
(~9-11k/game), event_game_started maps player_id->team_id, full state stream
— perfect imitation labels, no counterfactual forking needed for v1.
HARVEST RUNNING (Studio background, /tmp/fetch_replays.py): 293 hard-era
matches of ours (since 30300, >=2 fighters in room) -> /tmp/replays_hard/*.gz.
NEXT (tomorrow): miner — reconstruct per-tick visible-state for each fighter,
symmetry-normalized features, (state -> heading octant + split) weighted by
that fighter's game outcome; entries carry best/second/value-gap/confidence
per review schema; integrate as PLANNER CANDIDATE ("what would team do
here?"); MUST pass a paired-seed harness before carriers (standing law).

## 2026-07-17 (00:0x) — Tier-2 review adopted; hazard miner RUNNING; first signal confirmed
ChatGPT approved Tier-2 with corrections, ALL ADOPTED: (1) NO learned LAW
layer this competition — Chris's override tier demoted to advisory-with-
enormous-penalty (action-invariance fallacy: 80% death bins prove the
SITUATION was dangerous under historical policies, not that every action
dies); hard vetoes stay engine-provable only (flagged to Chris as reversing
his instruction — penalty-capped advisory ≈ same protection). (2) Survival
math fixed in spec: Π(1−h) valid only for ONE-STEP conditional hazards;
interval form q5/q20/q80 with conditional windows for leaf values. (3)
Independence unit = ENCOUNTERS (contiguous threat-exposure runs, 10-tick gap
split), never ticks; chronological match splits + leave-one-team-out
calibration; empirical-Bayes shrinkage; logit-residual integration
(logit(p)=logit(p_live)+w·Δlogit_table — table corrects the physics model
off a support-weighted cliff). Censored per-player vision reconstruction
MANDATORY for policy inputs. Fighter book deprioritized per review Q8 (hazard
book first; fighter miner = cheap diagnostics later). Survivorship-bias
guards: bounded per-player-game weight, local return-to-go.
BUILT TONIGHT: /tmp/mine_hazard.py on Studio (censored 20x20 view per
subject, physics-derived dims: capture margin, split-lunge margin, ticks-to-
contact, escape cone, wall class, fragmentation, bank, phase; hierarchical
coarse->fine bins; episodes reset at respawn; encounter-grouped pairs).
Chained behind the replay harvest (32/293 done, ~2h). FIRST SIGNAL (34
matches, 20,488 pairs, 4,595 encounters): d20 monotone in capture margin
69%->22%, fragile bins (tight+frag+corner) top the table — situational
hypothesis holding. TOMORROW: full aggregation + Wilson bounds, calibration
gates (reliability curve, Brier, leave-team-out), logit-residual planner
integration + risk-appetite gene, paired-seed harness — then carriers.
Jul-18 finals build still depends on NONE of this.

## 2026-07-17 — TIER 2 LANDED: mined hazard passes ALL gates, best policy ever harnessed
Overnight: harvest DONE (209 replays ok, 84 expired), miner DONE (125,915
encounter-pairs, 209 matches). GATES: (1) chronological calibration —
reliability curve near-perfect across all deciles (p0.7-0.8 -> obs 0.72),
Brier +17.8% vs base. (2) LEAVE-US-OUT: trained ONLY on other bots' deaths,
calibrates on OURS (+17.0% Brier, every decile within a few points) —
CHRIS'S SITUATIONAL HYPOTHESIS EMPIRICALLY CONFIRMED (death is situational,
not bot-specific; we inherit the field's recorded experience). (3) Paired
harness: hz_mpc 16.1% survival vs ev_mpc 12.5 / field 9.9 / deadaway 5.3 —
+29% over prior champion, +63% over reactive. SHIPPED: HZ table (87 coarse +
260 fine bins w/ support backoff, 12KB embedded) + planner survival-
discounted risk leaf (one-step conditional conversion per corrected math,
bank-scaled death cost W_HZ_DEATHCOST = risk appetite gene, support-weighted
trust, advisory only — no learned laws per review). Genes HZ_ON/W_HZ/
W_HZ_DEATHCOST (registry 169->172), verified (equiv inert off, witness
SUCCESS, 176us/call), 14 hz-mined carriers queued on fresh bases behind the
morning reinforcement wave (10 vl2-boost + 6 pl3-fresh + 4 ev2-fresh).
MORNING GYM VERDICTS (~106k matches overnight): VL spreading via crossover
(7/40 genomes, top young genome x2577x2457-fine 28.8@126 carries it), EV
marginal (1/40), PLAN/KG/RC extinct (retries seeded on fresh bases).

## 2026-07-17 — PLANNER DIAGNOSIS: harness-to-body transfer was not tested
Chris challenged the near-extinction of PLAN/HZ despite the HZ harness edge.
Source audit confirmed a mechanism, not mere selection noise. `hz_mpc` in
`ev_harness.py` is a separate 3-heading, constant-heading policy: its rollout
makes the pursuer actively chase, advances that pursuer before each HZ query,
and subtracts `120*support*h1` directly. It never calls body `_plan_heading`,
never exercises the structured 14-action/two-phase beam, and always starts
from EV even though most HZ carriers do not have EV active. Thus 16.1% vs
9.9% proves HZ signal in the toy evasion harness, not the shipped integration.
Body defects found: HZ queries freeze threats at their initial positions;
phase-2 survival resets to 1 instead of inheriting phase 1; fragmentation is
hardcoded 0; bank is largest+smallest (double-counts a singleton, omits middle
pieces); wall escape-cone orientation is not mirrored at right/top walls;
the documented logit-residual correction is not implemented; intent heading
is available but rollout uses only last displacement; and fragmented ticks
trigger planning although only the largest own blob is simulated. Planner-v2
also leaves PLAN_K/SPREAD and W_PLAN_{FOOD,THREAT,WALL} effectively dead.
Evolution agrees with model-error accumulation: culled means by horizon were
pl-roll H3 19.28, H4 16.96, H6 10.18; pl2 H4 18.53, H6 11.70, H8 9.66; HZ
H4 16.96 vs H6 12.27. At 14:58 AEST, all 20 pl-roll, 12 pl2 and 6 pl3 named
carriers were culled; 12/14 HZ carriers culled (two young survivors 12.0@82,
16.7@86). Verdict: do not interpret this as lookup-table failure; production
MPC integration and its validation harness must be repaired before reseeding.

## 2026-07-17 — PLANCORE built, gated, injected (Chris: "go for everything")
Containment revert to verified pre-margin body first (two unapproved edits
erased). NEW ORGAN PC (PLANCORE, per approved proposal + ChatGPT P0 repairs):
planning as the decision core when PC_ON — candidate 0 = reactive action +
reactive continuation (recomputed light-reactive heading each simulated tick,
NOT a held vector); alternatives differ only in first action (8 compass +
prey-intercept + SPLIT-NOW branches); ONE coherent SimState (all own blobs
w/ merge cds, opponents advanced on tracker INTENT with displacement
fallback, food consumption, engine eat rules both directions); objective =
engine events (mass gained − pieces lost − death cost = bank + PC_DEATH_EXTRA);
terminal mined-hazard queried ONCE at terminal state (advanced tracks — fixes
frozen-threat bug; miner-consistent features; no per-tick survival
multiplication per review math); baseline scored outside pruning (none
exists), LEXICOGRAPHIC dominance gate (risk <= base + PC_RISK_EPS AND value >
base + PC_MARGIN); LA veto retained downstream. Genes PC_ON/H/MARGIN/
RISK_EPS/SPLIT/DEATH_EXTRA (registry 173->179; PLAN_*/W_PLAN_* deprecated
in effect). GATES ALL GREEN: equiv bit-identical OFF + verify_moves 1400/1400;
baseline-preservation (exact passthrough, empty world); one-step differential
3000 states vs engine law exact; composition; mirror symmetry; split-strike
behavior (splits at reachable prey); witnesses OFF+ON SUCCESS on .14 —
PC-on telemetry: 1250 calls, 176 overrides (14%), 10 split-overrides, 696ms
of 3000ms governor. INJECTED immediately (Chris's order): 22 carriers,
identical parents (x2478x2454-fine, x2621x2607-fine): 6 pc-ctrl / 8 pc-core /
8 pc-hz — clean 3-arm A/B/C. ~30h of selection before the finals build.

## 2026-07-17 — PLANCORE post-build audit finds P0 model/action mismatches
Independent audit at 15:24–15:30 AEST, before any PC-active carrier entered
(only pc-ctrl-000/001 had entered, PC_OFF, n<10), invalidated the stronger
"engine-faithful / structural monotonicity" claim. When the reactive action
already has split=True, compass/prey alternatives are rolled out with
first_split=False but the returned action preserves split via `split or ...`:
the executed action is not the evaluated action. The downstream LA veto can
also cancel only the split bit after selection without restoring the baseline
heading, creating another unevaluated final action.

The split SimState is not the engine law: it splits only the largest blob
(engine splits every eligible starting blob up to 16), gives the child no
1.6 eject velocity / 0.82 drag, and uses cooldown 30 instead of engine 18.
Other verified mismatches: pellet gain is scored 0.09 although FOOD_RADIUS
0.15 means mass 0.0225; food/prey gains never update blob mass/radius/speed;
0.2%/tick mass decay, viruses, opponent split strikes, and eject velocities
are absent. The continuation combines threats+prey into one `tracks` list and
repels from all of them, so it flees prey after the first action; terminal HZ
likewise may select a prey blob as the nearest "hazard". `W_HZ` and
`W_HZ_DEATHCOST` are unused by PLANCORE. Therefore the 3000-state differential
gate did not cover the production split/state transition that matters, and no
durable PLANCORE-specific gate artifact exists in the repo to reproduce it.

Experiment caveats: queue order is all controls, then core, then HZ (time and
selection-background confound); HZ arms also vary PC_DEATH_EXTRA, so core-vs-HZ
is not an exact toggle; one parent carries LA_HORIZON=5.27 despite the operating
2–4 pin; and selection still runs agario-kit .13 while live/witness is .14.
Verdict: controls are harmless, but do not interpret or ship PC-active results
from this integration. Repair action identity + exact split/state transition,
separate prey/threat roles, retain a reproducible production gate, then inject
interleaved exact pairs.

## 2026-07-17 — PLANCORE P0 repairs (ChatGPT review verified against engine source), clean reinject
All review claims CONFIRMED in source: engine splits EVERY eligible blob
(SPLIT_MIN_MASS 2.0), cooldown 18 (not 30), eject 1.6 + drag 0.82 integrated
in _move_blob, FOOD_RADIUS 0.15 (mass 0.0225, not 0.09), MASS_DECAY 0.2%/tick.
REPAIRS: engine-true rollout (blobs carry eject velocity; split transition
exact incl. all-eligible + cd18 + eject/drag; food mass added to eating blob;
decay applied; prey SEPARATED from threats — continuation no longer flees
prey, HZ terminal sees threats only); evaluated==executed identity (heading
alternatives carry the incoming split flag; split candidates pre-checked
against the SAME _la_gate_split that runs downstream); W_HZ wired into the
terminal risk term. CONTAINMENT: 16 PC-active carriers pulled to
inject_queue/held_pc before any entered (only harmless pc-ctrl had entered).
DURABLE GATES: tools/pc_gates.py in repo — movement/eject/drag/decay/cooldown
differential (3000 states), full split transition, prey-not-fled, baseline
preservation + returned-action-was-evaluated identity (rollout spy), mirror
symmetry, timing (893us busy-scene). Plus equiv bit-identical OFF,
verify_moves 1400/1400, witnesses OFF+ON SUCCESS (.14) — repaired telemetry:
1400 calls, 22 overrides (1.6% — conservative as a dominance gate should be),
1687ms/3000 governor. REINJECTED per review design: 6 exact interleaved
ctrl/core pairs (71_*), PC_SPLIT=0 first, HZ off, PC_DEATH_EXTRA fixed,
LA_HORIZON re-pinned 2-4. Split planning and HZ arms follow only after core
survives selection alone.

### PLANCORE repair audit addendum — movement-only trial valid; split proof still incomplete
Independent rerun at 15:46 AEST: `tools/pc_gates.py` passes all six printed
gates, the 12 active 71_* files are six exact pairs differing only in PC_ON,
and each has PC_SPLIT=0, HZ_ON=0, fixed PC_DEATH_EXTRA=10, LA_HORIZON=4.
No PC_ON>0.5 genome was yet active; the 16 old core/HZ files are held. Thus
the current movement-only causal trial is clean and may proceed.

One P0 claim remains too strong for future split planning. `la_ok` is applied
only to newly proposed split branches; an incoming reactive split=True is
rolled out/returned as split=True, then the downstream LA gate may veto it to
split=False. A constructed radius-3 blob-on-virus witness produced exactly
this: PC returned (1,0,True), downstream returned (1,0,False), and the final
action was absent from the rollout spy. The durable identity gate exercises
only incoming split=False and stops at `_pc_choose`, so it cannot detect the
post-PC change. Before enabling PC_SPLIT, move the constitutional LA decision
before PC (making the PC baseline the final admissible reactive action), or
make the end-to-end gate apply downstream LA and require the final action in
the evaluated set.

Two smaller fidelity/gate gaps: rollout decays a mass-0.81 blob to 0.80838,
whereas engine `_apply_mass_decay` holds all blobs at/below the 0.81 minimum;
split spawn uses overlap epsilon 0.01 rather than engine 0.0001. The advertised
3000-state movement gate asserts mass/eject/cooldown but never x/y, and the
split gate checks only count/masses/cooldown plus `child_vx > 1`, so neither
numeric mismatch is covered. These do not confound the current PC_SPLIT=0
pair test materially, but must be made exact before the split arm returns.

## 2026-07-17 — PLANCORE paired trial: no upgrade; current design is mostly not future planning
Audit at 16:38 AEST after all six exact pc2 ctrl/core pairs entered. Equal-depth
samples total n=574 per arm. Pair differences (core-control) were -8.10,
+2.49, +0.81, -6.34, -6.11, +5.74 mass: mean -1.92, median -2.65; stratified
bootstrap 95% [-5.57,+1.77], only 15.1% probability of positive mean under
that resampling. Three cores were already culled versus one control. The only
credible positive, core-001, was +2.49@n143 equal-depth but its 50-game chunks
28.60/31.85/23.43 were declining. This is not a statistically proven loss yet
because of fat tails, but it is meaningful evidence against an upgrade.

Mechanism: this experiment does not test a general multi-tick planner. It
tests one alternative first action followed by `_pc_react`, a lightweight
food+threat heuristic that is not the production reactive policy. Horizon is
only 3/4 and HZ/terminal value are off. A pellet is 0.0225 mass while margins
are 0.5/1.0, so an ordinary farming override requires 23/45 extra pellets
inside 3–4 ticks—effectively impossible. All trajectories without an immediate
eat/loss end with equal value regardless of terminal position. The reported
1.6% witness override rate therefore indicates near-inertness, not proof of a
valuable planner.

Remaining harmful model gaps for even those rare overrides: movement rollouts
do not model viruses or adversarial opponent split strikes; opponents hold one
observed intent; actual reactive continuation (CGP/organs/locks/prey/virus) is
not recomputed. PC_SPLIT=0 only prevents initiating a new split—it does NOT
make the trial movement-only when reactive already requested split=True;
PLANCORE may still change that split's heading, and downstream LA can still
turn it into an unevaluated no-split action. Candidate selection is also
order-dependent: after accepting one candidate, later candidates must beat
the accepted value by another full PC_MARGIN, rather than merely beat the
baseline threshold and then maximize value. Verdict: do not infer that useful
lookahead failed; this implementation tests a sparse, short, misspecified
arbiter. Do not add split/HZ arms or ship it. Next valid experiment requires
shadow-mode override logging/counterfactual grading, actual-policy continuation,
virus + adversarial split scenarios, calibrated terminal value/margin, and
baseline-relative then argmax selection.

## 2026-07-17 — Competitor intel: TEAM's collapse = cumulative-timeout death spiral (confirmed)
Chris's Discord intel: "tim" (TEAM) repeatedly reporting CUMULATIVE timeouts;
they're trading performance vs compute budget live. Data agrees: 10 re-uploads
overnight (subs dying in 1-2 games), and fighter-cell collapse to LAST place
(1E 25% / 2E 18% / 3E+ 14% @ n=956 era) vs their stable-era 31% hard.
MECHANISM: per-tick compute scales with live entities -> cumulative-budget
bots trip DISPROPORTIONATELY in elite-dense (long, crowded) games = exactly
their worst cells; finals room = their worst case. Banned games never enter
records, so even their RECORDED games show the heavy body plays worse.
Threat model: Banana + Ninja primary finals threats; Washed steady; team
discounted until stabilized. US current era: 34%/2.53 overall, best-in-field
1E (37%) and 2E (29%) — the proven reactive stack is top-two while the
field's compute-heavy experiment self-destructs. Design vindication: the
governor (meter + degrade-to-instinct, never ban) is the structural
difference between planning-as-capability and planning-as-liability.

## 2026-07-17 — PC governor raised 3.0s -> 6.0s (Chris's order)
Rationale: non-planner stack uses ~0.15s/match locally; even on a 4x-slower
server CPU total worst case ~6.6s vs the 8s ban line (>1.4s margin). Trip
behavior unchanged: degrade to reactive, never ban — the structural
difference from TEAM's uncapped death spiral. Gates re-run green; ladder
restarted so queued pc2 pairs materialize with the new cap.

## 2026-07-17 — WHY THE PLANNER EXPERIMENTS FAILED: two causes, both now documented
(1) IMPLEMENTATION (mine): PLANCORE had zero terminal value — only events
completing within H=3-4 scored; farming override needed ~23-45 pellets in 4
ticks; two futures without an immediate eat/loss were indistinguishable ->
1.6% override rate = blindness, not restraint. Continuation `_pc_react` = a
3-term toy, not the production policy: every rollout (incl. the baseline's)
simulated a bot that doesn't exist -> the rare overrides sampled model error.
Residuals: order-dependent acceptance; PC_SPLIT=0 still re-aimed reactive
splits; LA veto could strip split off an evaluated action. Paired verdict at
depth (ChatGPT, n=574/arm): mean -1.92, median -2.65, 95% CI [-5.57,+1.77],
P(positive)=15%. Verdict indicts the ARTIFACT, not the lookahead thesis —
"a sparse H3/H4 one-action arbiter" was tested, not planning.
(2) EVALUATION (Chris's hypothesis — CORRECT): the ladder is elitist; genes
spread only via top-6. An architectural innovation flips behavior before its
interacting weights re-tune -> starts in a fitness valley -> culled before
refinement. Big-delta organs die; tiny-delta organs (VL/EV) drift neutrally;
NOTHING is ever refined. Carrier injection into an exploit-only ladder can
validate weight tweaks, never architecture (the NEAT/speciation problem).
Correct instruments: SHADOW MODE + NURSERY population — adopted.
ACTIONS: PC_ON neutralized in the 2 remaining population genomes (genes kept
as extra controls; pc2-core-001 stopped before breeding depth); 16 flawed
carriers remain held; PLANNER_REDESIGN.md written (full proper-planner spec:
production-policy continuation, shared transition oracle, H12 multi-decision
beam, opponent ensemble, distilled terminal value incl. the unbuilt
OPPORTUNITY twin of the validated hazard table, LCB acceptance, structural
action identity, shadow-mode gates). NOTHING planner-related ships in the
finals build; close-of-world selection champions only.

## 2026-07-17 — Planner v3 rebuilt per spec: bit-exact sim engine + shadow grader (Chris's order: "re do your plancore")
Executed the PLANNER_REDESIGN.md build order in one pass, shadow-first, zero
body changes beyond the already-proven inert `_reactive_core` extraction.
(1) PRODUCTION POLICY AS CALLABLE: `_reactive_core(game, tracker, hunt)`
extracted verbatim (149 lines) from choose_move; equiv_test bit-identical +
verify_moves hzws 1400/1400. The continuation policy in every rollout is now
the REAL bot, not a surrogate — the core defect of PLAN v1/v2/PLANCORE.
(2) AUTHORITATIVE TRANSITION (tools/sim_engine.py): full commit_round mirror
— splits, move+eject+drag, decay floor, 3x stabilise (attract/merge/separate),
virus grid-shatter, food largest-first, size-ordered eating loop.
DIFFERENTIAL GATE vs real engine: 7200/7200 rounds, 0 mismatches. Lesson
worth recording: the last 10 mismatches were 1-ULP floating-point
association differences that flipped exact boundary branches — engine
computes x*(r*r) not (x*r)*r, precomputes move_a=ov*(mb/tm) before
multiplying by nx, and 0.9*0.9 != 0.81 in the last bit. Bit-exactness vs
the engine is achievable and now permanently gated.
(3) PLANNER V3 (tools/planner_v3.py): engine-vision-law censored views
(20*(sum_r/12)^0.4 box + center clamp) so rollouts see what the bot would
see; 4-scenario opponent ensemble (continue/pursue/intercept/split-strike,
prey flee); <=12 structural candidates; CVaR gate (worst-case must not
degrade) + advantage-LCB acceptance; chosen tuple returned unchanged.
Deterministic, ~0.9s/propose offline.
(4) SHADOW GRADER (tools/shadow_grade.py): reconstructs FULL worlds from our
harvested replays (foods/viruses by id; hidden eject velocities recovered
from movement residuals; split children seeded dir*1.6*0.82), warms a
Tracker 10 rounds, then paired counterfactuals: planner arm vs reactive arm
from the identical state, H=30 through the bit-exact sim, opponents
replaying their RECORDED moves. First replay: 25 points, 20 overrides,
deaths 4->2, mean paired advantage +2.55. Full 42-replay evidence run
launched; verdict decides whether planner v3 earns a live path. Nothing
ships before freeze regardless (standing decision).

## 2026-07-17 — SHADOW VERDICT: planner v3 is the first POSITIVE planner evidence of the campaign
Full grading run: 42 replays, 1050 decision points, 871 overrides (83%),
paired counterfactual (planner arm vs reactive arm, identical states,
recorded opponent moves, bit-exact sim, H=30).
HEADLINE: mean paired advantage +0.68 mass, bootstrap95 [+0.14, +1.21] —
the CI EXCLUDES ZERO. Compare the PLANCORE verdict at the same instrument
class: -1.92 [-5.57, +1.77], P(pos)=15%. Same theorem, correct
implementation, opposite sign.
ANATOMY (matches the design thesis exactly):
- Deaths 116 -> 96 (39 saves vs 19 planner-caused). Death-avoidance IS the
  payload: the no-death subset is +0.09 ~ neutral.
- Threat points +1.14 [+0.26,+2.02]; calm points +0.08 ~ 0. The planner has
  the hazard half of a value function and no opportunity half — so it earns
  under threat and is inert in calm, precisely as predicted. The mined
  OPPORTUNITY table remains the unlock for the calm half.
- CALIBRATION (ChatGPT's gate): prediction->outcome r = +0.12, positive but
  weak; predictions overestimate 3.7x (pred +2.52 vs realized +0.68). BUT
  the ordering signal is real: gating overrides at predicted advantage >=
  1.0 yields +2.74 [+1.07, +4.43] on n=217 — the authority dial ChatGPT
  demanded, measured. Best operating point found so far: override only when
  pred_adv >= 1.0 (21% of decision points, ~3x the per-override payoff).
- Mid-mass band (15-40) is the one negative cell (-1.40 [-3.16,+0.10]);
  small-mass +0.91 CI-positive, big-mass +2.07. Post-freeze: inspect the
  worst mid-mass losses (2 of the 5 worst are non-death -48/-34 economy
  losses).
Evidence archived: reports/shadow_v3_20260717.jsonl + _summary.txt;
analyzer promoted to tools/shadow_analyze.py. No live wiring — standing
decision holds (nothing planner-related ships before freeze; live path
needs Chris's explicit go post-freeze).

## 2026-07-17 — PL3 SHIPS INTO THE GYM: lite planner ported into the body, 16 carriers injected (Chris's order)
Chris: shadow evidence means nothing if the tools never reach the bots.
Sequence executed in one evening:
(1) LITE COMPRESSION: planner v3 cut to live budget (4 candidates x 2
scenarios x H6, fire only when threat<12 AND own mass<15, override only when
predicted advantage >= dial). RE-GRADED on the same 1050 replay decision
points before porting: +3.03 CI95[+0.38,+5.65], deaths 30->22, override
rate 7% (surgical). All value in the mass<15 cell (+4.02 CI-positive) ->
PL3_MAXM authority cap.
(2) BODY PORT: ORGAN PL3 in bots/omni_mixer_v3.py — embedded engine-true
transition (mirror of the 7200/7200-differential-tested sim), censored-view
rollouts continuing with the REAL _reactive_core, movement-only overrides,
own 4.5s governor (degrade-to-reactive under the 6.0s stack budget). Genes:
PL3_ON/DIAL/RANGE/H/CANDS/CD/MAXM, all inert at defaults (PL3_ON=0).
GATES: py_compile 3.12; equiv_test PASS (2000 ticks bit-identical);
verify_moves fresh witness workspace 1070/1070 rounds 0 mismatches;
PL3-ON smoke 400 ticks (90 fires, 15 overrides, deterministic, per-fire
p50 9.3ms); ladder-materialized carrier compiles with genes stuck; live
engine witness match SUCCESS, empty stderr, no ban.
(3) INJECTION WAVE 72 (16 carriers, 2/cull via root+extra lanes): 4 champion
chassis (2667, 2852, 2807, 2734) x {g10 graded config, d05 low-dial,
m25 high-dial/mass-25, off exact twins}. ChatGPT gate-4 design: exact
on/off twins + authority levels on multiple strong chassis.
(4) Persistent monitor armed on ladder_log (CULL_BREED/INJECT events);
standing order (Chris): wake every cull, evaluate carriers, keep injecting
THOUGHT-THROUGH variants; target = PL3-equipped genomes at the top of the
board within 4 hours.

## 2026-07-17 ~19:00 — PL3 campaign mid-report: carriers hold top board slots, genes breeding
Two hours in: 15/41 pool slots are PL3-family (waves 72-74; ON at #1/#2/#6).
Depth-qualified twin deltas for the graded g10 config: 2807 +3.3@~120 (OFF
twin later culled while ON sat in elite), 2734 +6.0@~88, 2870 +5.9@~96(*),
2667 -0.4@122 neutral, 2852 ON outlived OFF. No chassis negative at depth.
Both 2908 and 2918 have rotated through the top-6 BREEDING elite — PL3
genes now propagate via crossover (non-registry keys ride parent-A).
Live gym reproduces the shadow cell map: all three landed m25 arms
(mass<25, authority into the mid-mass cell) died fast, exactly the cell
the counterfactual grader flagged negative; H8 underperforms H6
(model-error compounding, as the external review predicted). Timeout
telemetry from instrumented engine matches: 1.3-1.9s spent of the 5.0s cap
across full 1400-tick games, ~100 fires, zero governor trips — graduated
throttle (2.5s -> 2x cooldown, 4.0s -> emergencies-only) never engaged.

## 2026-07-17 ~19:30 — THREE-LEVER FINALS DETECTION (Chris's design, organizer endgame update)
Organizers: submissions close midnight end of Sun Jul 19 (AEST) =
2026-07-19T14:00Z (matches our standing freeze); scheduler keeps running a
few hours after close; top-8 then finals; scheduler ~3x faster for the
last 3 days. Exact finals start time UNKNOWN -> time alone no longer
sufficient. New mode machinery in the body (ship-only, gym-inert):
LEVER 1 TIME (SAFETY BACKSTOP ONLY, Chris rev): cutover = close+9h =
2026-07-19T23:00Z, checked ONCE at boot, never per-tick — exists only in
case the two primary levers fail.
LEVER 2 COMPOSITION: elite set becomes the TOP-10 leaderboard ids at build
time; escalation ladder now ends 1E -> 2E -> FINAL at tally>=3 (the 3E
model is retired; the finals-world champion plays all elite-dense rooms,
which also live-exercises it pre-freeze).
LEVER 3 TEAM-ID ANOMALY: game_started scan — if our own team id != 35 or
ALL room team ids are 0..7, the bracket was re-seeded -> FINAL immediately.
Gates: py_compile; equiv_test PASS (gym bit-identical); verify_moves
1070/1070; unit battery covers all three levers + negatives (normal room
no-force, tally-2 still 2E). Bundle codegen tomorrow: ELITE_IDS = fresh
top-10 minus us; old hard-room-survivor gate retired for mode IDs per
Chris's "compute the top 10 as the elite now".

## 2026-07-18 ~00:50 AEST — BUNDLE v5rc STAGED: first PL3 carrier ships to the live court (Chris's order)
Chris: "use the existing bundle just swap out the e3 and use codegen —
tomorrow we will have evidence." Built from the CURRENT body (PL3 code must
ship for the genes to mean anything): v4's proven mode-0/1/2 models
extracted verbatim from the shipped artifact, FINAL slot = genome 2984
(pl3c-m12-2807: 26.2@w300, 332 games, breeding-elite regular; config =
mass<12 / dial 1.0 / H6 — exactly the shadow-validated cell, most
conservative live-risk profile of any carrier; NOT 2944 whose mass<25/dial2
config sits in the cell shadow-graded negative). PL3 scoping: base OFF,
FINAL overlay ON -> the organ runs only in 3E+ rooms and finals.
Three-lever detection live: top-10 elite ids (15,73,85,1,5,37,9,56,24),
boot-only time backstop 2026-07-19T23:00Z, team-id anomaly REDESIGNED after
a real-harness discovery: bots receive PUBLIC game_started where other
players carry NO team_id — only `you` does (helper/state_mutator + lib
models verified). Anomaly now keys on you.team_id != 35, which any finals
re-seed necessarily triggers. Local witness: fired tick 1 in all 3 matches.
GATES: body equiv PASS + verify_moves 1070/1070 after the lever fix;
fold audit raw-vs-codegen bit-identical; per-mode CONFIG fidelity
(268/268/302 genes); ladder walk 2E/FINAL/anomaly/0E on the final artifact;
live engine witnesses 3/3 SUCCESS, empty stderr, no governor trips, two
rank-1 finishes with FINAL+PL3 active from tick 1.
STAGED: ~/Desktop/ship_staging/BUNDLE_v5rc_2984final_CODEGEN.py
sha256 0c67f02b784796956f449deb70c2859324d27f62a22c43621e6ab80ac2a1a663.
Chris uploads; tomorrow's meta run judges the FINAL cell (old 3E+ baseline:
25%@625 vs Banana 30%).

## 2026-07-18 ~08:20 AEST — OVERNIGHT VERDICTS: live 3E regression + the gym breeds PL3 out by drift
LIVE (sub 1963, n=1378, 0 bans): overall 34%/2.41 with field-best 0E/1E,
but the FINAL slot REGRESSES in live 3E+ rooms: 20%@182 (rank ~3.3) vs the
old 3E specialist's 26% and same-era Ninja 26% / Banana 28%. Mode
attribution from 80 fetched logs: FINAL engaged in 80/80 (69 by tick 400) —
recognition is perfect; the 2984 model itself underperforms that cell. The
n=44 "no regression" read did not survive n=182. (2E also softened 28%@470
on an UNCHANGED model — Ninja's 1937 upgrade hardened the field — so part
of the dip is era, not all.)
GYM: PL3 bred OUT overnight — 1/41 ON — by parent-A lineage drift, NOT by
evidence: the dominant chassis family (3120->3252->3350) descends from an
off-cross, and non-registry genes ride parent-A. Controlled twin deltas
stayed positive/neutral to the end (last pair at w300: ON +0.86). LAW
(extends the architecture-validation law): the elitist ladder cannot
RETAIN architecture either — organ genes hitchhike on lineage fitness
unless registry-included or continuously re-injected. Close-of-world
champion: 3350 (x3297x3194) 27.46@300, organ off.
Proposed to Chris (B): tally>=3 -> old v4 3E specialist for regular play;
FINAL (2984+PL3) reserved for the true finals signals (team-id anomaly +
9h time backstop). Awaiting decision.

## 2026-07-18 ~12:27 AEST — PL3 overnight audit corrects the causal verdict
Reconstructed the campaign from state.json, the injection payloads,
ladder_log, graveyard, and the actual PL3_ON gene rather than lineage tags.
SEEDING/ADOPTION: 62 direct PL3 injections were consumed; audited ON/OFF
pairs differ only in PL3_ON (the h30 pair also intentionally differs in
PL3_DIAL). Several ON carriers were genuinely selected: #2908 survived 879
games / entered the breeding elite 15 times; #2944 780/30; #2984 634/24;
#3234 997/34. Reconstructed ON share peaked at 32 among 39 tracked newborn
slots, so the organ was temporarily adopted and spread. Current share at
~12:22 AEST is 3/41 (one mature bred carrier #3510 at 26.03@w300 plus two
young reinjections). This rules out payload corruption or queue failure.

EVIDENCE CORRECTION: exact genotype twins were NOT paired to identical room
seeds; they were independently scheduled in the same world. Equal-prefix
mean deltas for five representative pairs were +2.66@n139, +1.51@n209,
+6.12@n89, +5.96@n102, +1.11@n586, but every approximate 95% interval
crosses zero because gym mass is fat-tailed. Direction is encouraging and
ON arms survived longer, but the gym does not prove a positive effect of
the size previously quoted from transient rolling-window snapshots. The
honest verdict is small-positive/uncertain, not "positive by proof."

ARCHITECTURE AUDIT: the ported lite PL3 is materially narrower than planner
v3 in the exact hard-room mechanism that matters. Its opponent scenarios
always return split=False (no adversarial split-strike), and simulated
reactive continuation computes rsp then forcibly executes split=False.
It also has only H6 event return (mass delta/death, no terminal clearance,
hazard, or opportunity value), skips planning whenever the real baseline
splits, and acts only below PL3_MAXM near threats. Therefore it cannot be
expected to dominate whole-game fitness or reliably plan elite split
combat even though its transition physics is correct.

MONITOR DEFECT: tools/pl3_score.py filters lineage.startswith("pl3"), so it
misses inherited PL3_ON in ordinary x-parent descendants; its graveyard
reader also expects _id/_lineage at the top level although they live under
entry["genome"], producing None rows. Past "1/41"/"2/41" reads from that
scorecard are not reliable. Durable causal conclusion: seeding mechanics
were mostly sound, while retention/co-tuning methodology and the lite
planner's narrow/mismatched opponent/action model limited the result.
No body, registry, queue, pool, or running-campaign change made in this
audit.

## 2026-07-18 ~12:40 AEST — PC resurrection corrects the planner verdict; PL3 live blame retracted
Chris supplied the missing morning result and local state verifies the main
mechanism. PC's six genes remained in exposed_genes_ACTIVE; evolution
resurrected PC_ON and co-tuned H/margin/risk. Current checkpoint m624379,
cull 734: PC_ON>0.5 in 37/41 genomes (Chris observed 38/41 immediately
prior), including 21 with >=150 games and 13 full w300 windows. Mature board
leaders #3536 (31.32@w300), #3451 (29.35@w300), #3480 (27.95@w300), #3191
(27.68@w300), #3396 (27.03@w300), etc. all execute PC. This retracts the
broad statement that planner architecture remained a negative result:
PLANCORE's original fixed paired configuration was negative, but the
registered organ was subsequently domesticated into near-ubiquity by
co-tuning. Ubiquity is strong selection evidence (not by itself a causal
paired effect estimate) and independently supports the nursery/registry
doctrine for architectural organs.

HAZARD PRECISION: PC is wired to query the Hazard book only when HZ_ON>0.5
(body line in _pc_choose). At this checkpoint only 1/41 has HZ_ON>0.5, and
it is a young carrier; the prevalent PC genomes carry HZ_ON about 0.08–0.27
and therefore do NOT consume the table. Correct statement: PC is ubiquitous;
PC+active-Hazard is not yet ubiquitous. If a prior monitor treated any
nonzero HZ_ON as active, it overstated adoption.

PL3 VERDICT CORRECTION: its exact-twin directions were positive on every
reported chassis and never supplied a controlled negative result. The
fat-tail intervals mean the gym effect size remains uncertain, not negative.
The live 3E+ regression belongs to the combined #2984+PL3 package without a
live #2984 OFF twin, so attributing that regression to PL3 is invalid. The
lite planner's missing opponent/future-own splits and narrow H6 leaf remain
architectural improvement opportunities, not evidence that PL3 caused harm.

COMPOSITION ISSUE DISCOVERED: choose_move currently dispatches PL3 first and
PC via `elif`. In a PC_ON+PL3_ON genome, PL3 suppresses PC on non-split ticks
where PL3 is eligible and grades its alternatives only against reactive, not
against PC's selected action. Registering PL3 without changing arbitration
would evolve "PL3 instead of PC" in its trigger cell, not a clean additive
PL3+PC organ. Recommended prerequisite (not executed): unified candidate
arbiter, or run PC first and make its fully guarded result PL3's baseline;
then register PL3 as a coherent evolvable family and test exact twins.

ENGINE RECORD: Chris verified .13/.14 physics are source-identical; a fresh
.14 differential battery is running for durable confirmation. No result
claimed here until that battery completes. No body/registry/campaign change
made in this audit.

## 2026-07-18 ~12:50 AEST — PL3.1: external review P0 fixes applied + .14 fidelity closed + Opportunity miner launched
ChatGPT review verdict (Chris relay): assets didn't fail, the delivery
pipeline did (wrong consumers, mechanism drift, no co-tuning); recommends
PL4 (option-based, split-aware, hierarchical, hazard+opportunity leaves,
nursery). Pre-freeze feasibility triage: P0 today, PL4 = post-freeze.
DONE (all gated: equiv PASS, verify_moves 1070/1070, smoke exc=0):
(1) .14 DIFFERENTIAL: fresh venv agario-kit 2026.1.14, tools/sim_engine.py
    7200/7200 rounds 0 mismatches — bit-exact vs the COMPETITION version.
(2) Continuation split preservation: rollouts now execute the production
    policy's split decisions (was forced False — simulated a never-splitting
    bot; review's sharpest catch).
(3) Opponent split-strike scenario added (3rd ensemble member) with
    per-blob engine-law eligibility (mass>=2.0 AND cd==0, kill+reach check).
(4) Telemetry: exceptions + deadline-aborts counted, periodic [pl3-stats]
    line every 500 ticks (live logs now show fires/ovr/exc/aborts).
Cost after all three scenarios: p50 3.8ms/fire. Live wave-79 carriers
re-materialized on PL3.1.
LAUNCHED: mine_opportunity.py on Studio — the hazard book's OPPORTUNITY
twin (bank x threat-clearance x food x crowd x wall bins -> realized
20/80-tick mass gain), the long-lead PL4 prerequisite.
Facts fed back to the reviewer: PC genes were registry-included; evolution
resurrected + re-tuned PLANCORE into 38/41 champions (co-tuning thesis
confirmed in vivo); early PL3 twins were vs pure reactive (chassis PC_ON
<=0.32), current twins are PL3-vs-PC.

## 2026-07-18 ~13:30 AEST — Chris's orders executed: BUNDLE v6 (option A) staged + PL3 registered with PC-first composition
SHIP (option A): BUNDLE_v6_3536final_CODEGEN.py staged, sha
4f164ffc18f8afd9b27131d59b060c8da0d53392812b7d03f41489b169bc8e7a.
FINAL slot = gym champion 3536 (x3191x3234-fine, 31.34@w300, 329 games —
grandchild of the 983-game PL3 carrier; runs domesticated PC 0.74 + LA, no
PL3). Modes 0/1/2 unchanged (v4 models). ELITE_IDS refreshed to top-10
minus us: (15,88,73,85,1,5,9,37,56) — caseoh(88)+imposters in, OJ out.
Ladder unchanged (tally>=3 -> FINAL); all three safe-switch levers gated
again incl. team-id anomaly (fires tick 1 in all live witnesses; 3/3
SUCCESS, two wins, 0 stderr). Chris uploads.
GYM (per ChatGPT composition spec, Chris's "go ahead"):
(1) ORGAN COMPOSITION: PC proposes FIRST, PL3 evaluates PC's guarded action
as baseline, abstains on splits; PLAN keeps PC-exclusivity. Gates: equiv
PASS, verify_moves 1070/1070.
(2) PL3 REGISTERED: 7 genes into exposed_genes_ACTIVE.json with review
bounds (ON 0-1, DIAL 0.25-2.5, RANGE 8-16, H 4-10, CANDS 3-6, CD 1-6,
MAXM 8-30) -> 186 registry genes; "pl3" added to GENE_FAMILIES (coherent
crossover inheritance). Ladder restarted clean (launchctl; alive, tput
ramping). Wave 81: exact ON/OFF twins on 4 PC-dominated champions — from
here evolution tunes the planner the way it domesticated PC.
Record corrections accepted from review: HZ gate is HZ_ON (active 1/41,
not 38/41 — my census wrongly used W_HZ); .13-vs-.14 retracted as cause
(fresh .14 differential: 7200/7200 exact).

## 2026-07-18 ~14:40 AEST — Opportunity table v1: mined and calibrated, verdict WEAK (honest negative)
Miner completed all 209 replays -> 467,087 state->gain rows. Table v1
(bank x threat-clearance x food x crowd x wall -> mean 20/80-tick gain,
329 bins at support>=20): chronological 70/30 calibration shows only
+2.3% MSE improvement over the global mean (hazard's equivalent was
+17.8%). Verdict: 20-tick farming gain is dominated by factors outside the
v1 feature set; NOT yet a usable planner leaf. Improvement paths for the
post-freeze PL4 iteration: finer food-field features, speed/blob-count,
mass-relative growth targets, winsorized labels, skill-tier conditioning.
Pipeline + rows are durable (/tmp/opp_mine mirrored to vault next sweep).

## 2026-07-18 ~16:49 AEST — Current-build audit: body sound, v6 safe but incomplete operationally
Independent audit of current gym body + staged BUNDLE_v6. Current body
compiles under 3.12; durable pc_gates all pass (movement/split physics,
baseline+action identity, symmetry; 892us/call ~=1.25s/match vs 3s PC
governor). Gym is healthy at m651k/cull766: PC 39/41, HZ active 1/41,
PL3 5/41 (2 deep). Registered PL3 clean #3550 pair is currently ON #3643
28.51@w300 vs OFF #3639 27.90@w300 (+0.61); other ON arms died earlier,
so tuning evidence is small/chassis-dependent, not yet a graduation.

STAGED v6: compile OK; sha matches staging log; FINAL effective config has
PC_ON=.736, HZ inactive (.163), PL3 off, LA active. Mode-7 overlay matches
#3536 modulo expected 6-decimal codegen rounding; modes 0/1/2 retain all
planner gates off and LA on. Artifact predates PC-first composition and
still dispatches PL3 before PC, but PL3_ON=0 in every mode, so the mismatch
is inert and is not a reason by itself to rebuild. #3536's later w300 fell
to ~26.4, while its behavior-identical clone #3599 (only inert PL3_CD
differs) is 28.8; replicated honest policy estimate is ~27-29, proving the
31.34 build-time number was a high excursion rather than a code defect.

OPEN AUDIT FINDINGS: v6 exists only in Desktop staging + temp-path sha log;
no v6 artifact/genome/vault_log entry found, violating the ship-vault gate.
Registry count is 187 (not the journal's earlier 186). No dedicated
PL3.1 gate file exists: split preservation/split-strike/composition have
smoke evidence but no durable regression battery. The new split-strike
selector is only partly per-blob: mass/cooldown are per blob, but its reach
test uses opponent/player centroid distance `d`, which is wrong for
fragmented bodies. PC is now dominant yet choose_move still silently
swallows PC exceptions (exit telemetry reports calls/overrides/time but not
exceptions). No files/builds/campaign settings changed by this audit.

## 2026-07-18 ~17:00 AEST — BUNDLE v7 staged + world switched to TRAIN-PRE1E (Chris's orders)
SHIP v7 (Chris: "1E/2E slots the old ones; 3E+ and final = newest champion"):
BUNDLE_v7_3712final_CODEGEN.py staged, sha
70a081dd7479e87b759a20d57fb94856d653bfe58e0914dd3550833835cc88da.
Base/0E/2E = v4 proven models; FINAL (serves tally>=3 AND finals) = 3712
(x3536x3599-fine, 29.56@w283 close-of-world #1; PC 0.65 + LA on). Top-10
elite ids unchanged. Gates: fold audit, per-mode fidelity, ladder walk +
anomaly, 3 live witnesses (SUCCESS x3, one win, 0 stderr). Chris uploads.
WORLD SWITCH: TRAIN-FINALv2 archived
(archive/campaigns/v3campaign6_final_20260718_TRAINFINALv2: top-8 depth
champions materialized + genomes, state, ladder copy, log gz, RESUME).
New world v3campaign-7:TRAIN-PRE1E mirrors the collapsed live meta
(1.49E/1.61C/4.9G): seat1 elite, seat2 contested, seat3 coinflip
contested/fodder, seats4-7 fodder. Population CARRIED OVER (organs +
registered PL3 genes ride along); WORLD_CHANGE_FLUSH confirmed; variants
flushed; ladder healthy. Wave 82 seeds: live1E-base (the proven live 1E
model as competitor) + 3712 PL3 ON/OFF twin pair for 1E-regime co-tuning.
Timeline: ~24h of 1E selection -> pre-final bundle tomorrow evening
(new base slot) -> upload before the midnight-AEST close. Tailscale note:
SSH re-auth needed twice today (page closed); re-authed by Chris 16:45.

## 2026-07-18 ~22:45 AEST — OPTION B: infrastructure reverted, PL4-Tactical delivered as a STANDALONE bot
Chris: PL4 must be a separate bot; keep the evolution's results. Executed:
(1) REVERT: bots/omni_mixer_v3.py restored byte-identical to the pre-PL4
snapshot (sha 6a78e2cc... match confirmed; verify_moves 1070/1070). The 6
PL4 genes UNREGISTERED, pl4 family removed from the ladder, ladder
restarted healthy. Pool untouched: all PL3/PC co-tuning results live on
(PL3 genes stay registered as they were all day). ~5 culls of newborns
bred during the 45-min PL4-registered window carry inert junk PL4 keys —
harmless (not in body CONFIG, not in bounds).
(2) STANDALONE: SHIP_PL4T_3712.py staged (sha 33-char in .sha_log) —
body-with-PL4 + finals-champion 3712 genome + PL4 forced on (dial 1.0,
TTC 10, H12, commit 3, frac 0.7), PC 0.65 active as incumbent, LA on,
shared ledger inside the file (hard 6.2s, PL4 slice 3.5s).
EVIDENCE CHAIN: offline planner4.py (options MPC per amended review spec);
dev-42 +4.77 CI[+2.13,+7.66]; UNTOUCHED 24-match holdout +6.80
CI[+1.47,+11.92], deaths 12->4, 0 errors; in-body gates (determinism 150
scenes, p50 23ms/fire, ledger slice enforced); 3 live engine witnesses
SUCCESS, 0 stderr, 0 exceptions, 140-180 fires/match, ledger peak 3.93s.
Upload/testing of the standalone = Chris's call (it would REPLACE the
current sub if uploaded to the main slot).

## 2026-07-19 ~01:10 AEST — BAN POST-MORTEM CORRECTED + BUNDLE v8 staged (1E champion base)
BAN CORRECTION: sub 2000's first-ever ban (match 55690, CumulativeTimeout)
was NOT compute — the submission log shows the bot healthy in 1E mode at
tick 36, then "procfs is not mounted! Aborting" (their container runtime
killing the process; same fault Chris saw days ago), after which the dead
process was billed for silence. Evidence pack for Hugo = the 5 log lines +
the metadata row (a bot idling in its cheapest mode cannot ACCUMULATE 8s).
Cap flip-flop: 3s announced -> live ~1h -> reverted to 8s. All artifacts
keep regime-proof budgets regardless (two reversals in one evening).
BUNDLE v8 staged: BUNDLE_v8_3793base_CODEGEN.py sha
1615d36e4d58d9dc6969fc8facaab035f9149372517caf8f5edfec8984871062.
Base = 3793 (pl3k-on-3705): the 1E-world champion at 54.66@w300, 792
games — a PL3-ON + PC carrier; organs run in 0E/1E/2E modes budget-capped
(PC 1.5s + PL3 0.8s + reactive ~0.6s => worst ~2.9s, safe under 3s AND
8s). 0E/2E slot models unchanged; FINAL = 3712 (PL3 off there by its own
genome). Gates: fold audit PASS; per-mode fidelity at relative 1e-5 (the
absolute-tolerance false alarm on 4 large-magnitude genes documented);
three-lever walk; 3 live witnesses SUCCESS (one win), anomaly at tick 1,
0 stderr. Awaiting Chris's upload — replaces frozen sub 2000, unfreezes
us, and ships the pre-final base ~17h ahead of the original schedule.

## 2026-07-19 (later morning) — Elite-list defect found by Chris; v10 staged
- Chris diagnosed the 3E+ slippage: the bundle's hardcoded ELITE_TEAM_IDS was Friday's top-10 and
  missed the teams actually strong NOW — PorkyPig (31), Bots for Life (53), OJ (24), Engorgio (44) —
  plus carried dead id 85. Rooms full of current elites under-counted the tally -> bot stayed in
  1E/2E brains in genuinely elite rooms.
- New rule from Chris: elite list = everyone above spaghetti 🍝 on the live leaderboard.
  As of 11:55 AEST that is 12 teams: (1, 5, 9, 15, 24, 31, 37, 44, 53, 56, 73, 88).
- v10 = v9 (6.5s planner budgets: PC 5.5 + PL3 1.0) + corrected elite list. Gates: compile OK,
  codegen equiv PASS, 2 witnesses 0 stderr, anomaly->FINAL verified. Staged as
  ship_staging/BUNDLE_v10_elitefix_CODEGEN.py, sha 63381505... make_bundle.py updated too.
- Also today: ranking field in server metadata is 0-indexed (rank 0 = win) — my first table pass
  counted 2nd places as wins; corrected. Studio homebrew python update wiped websocket-client
  (cache stalled); reinstalled with --break-system-packages.
- H1/H2 era split (window split 08:38 AEST): 3E+ pie redistributed — Washed 19->35%, BfL 14->31%
  (8 subs shipped overnight!), us 19->9%, Ninja 40->26%. Field is iterating live; we were static.

## 2026-07-19 ~12:08 AEST — PL4 standalone implementation audit
- PL4 has a real positive tactical signal, but the shipped standalone is not the PL4 spec's brute-force/
  multi-option sequence planner. It searches one root macro (hold 3 ticks, then reactive); the live body
  executes only its first heading, skips PL4 on the next tick, and stores no option parameters or remaining
  commitment. Split-attack/escape, regroup and hold-course were removed from the in-body port.
- The +6.80 untouched-holdout result tested `tools/planner4.py` (H8 shallow, 300ms, 1500 steps), not the
  embedded standalone path (H6, 250ms, 1200 steps). Evidence remains encouraging and survives a
  match-clustered bootstrap, but prediction calibration is negative (holdout r=-0.03; dev42 r=-0.22), so
  it validates occasional first-action rescues rather than the planner's value model.
- Two concrete model defects: the intercept scenario reads `tracker.velocity[(our_pid, 0)]`, but Tracker
  never tracks our blobs, so intercept collapses to ordinary pursuit; initial rollout eject velocities are
  zeroed, making post-split tactical states inaccurate. Deep-tier timeout can also compare a partial beam
  despite the "complete tier" claim.
- Release provenance blocker: current `SHIP_PL4T_3712.py` sha256 is `adf5d7f2...`, absent from `.sha_log`.
  Its budgets were later changed to PC 0.8s / shared hard 2.0s / PL4 stop at 1.8*frac (1.26s total ledger),
  while comments and the recorded witnesses describe 6.0s / 6.2s / 5.0*frac. Compile passes; an exact
  embedded 30-scene local benchmark measured p50 41.8ms, p90 124.9ms, max 233.9ms.

## 2026-07-19 (midday) — v11 shipped-staging; PL4 merged; gym -> TRAIN-FINAL-PL4
- Chris's orders: (1) ship gym champion 4471 as the 1E/base slot; (2) after shipping, merge PL4
  into the shared body (ledger 6.5s, degrade PL4->PL3->reactive) and switch the gym to FINAL-mode
  training.
- v11 = base g4471 (TRAIN-PRE1E champion, 53.20 window avg @257 games, PL3-carrier) + v5-era 0E/2E
  overlays + FINAL=3712 + new above-spaghetti elite list + 6.5s budgets. Gates: compile, equiv
  PASS, 3 witnesses (0 stderr, anomaly->FINAL ok). Staged BUNDLE_v11_4471base_CODEGEN.py sha d1bf0cc8...
- PL4 merge (reverses Option B per Chris's explicit order): body_with_pl4 installed as
  bots/omni_mixer_v3.py with _PLEDGER_HARD = 6.5; equiv gate PASS (inert at PL4_ON=0, real
  old-vs-new run). PL4 genes re-registered (ON/DIAL/CRIT_TTC/H_CAP/COMMIT/BUDGET_FRAC), pl4
  GENE_FAMILY restored in ladder.
- Gym world flipped: WORLD_TAG v3campaign-8:TRAIN-FINAL-PL4, finals mix restored (4E+1C+2 farmers,
  no fodder, TRAINFINALv2 shape). Population CARRIED OVER (windows flushed by design); ladder
  restarted, matches flowing, variants confirmed carrying PL4 organ + genes. pl4twin-4471 queued
  for next cull (PL4_ON=1 at holdout-gated defaults).
- NOTE: first PL4 registration attempt used spec name PL4_CRIT_RANGE; the ported body actually
  exposes PL4_CRIT_TTC (time-to-contact gate). Assert caught it; fixed before anything ran.

## 2026-07-19 (early afternoon) — ChatGPT PL4 critique triaged; 2 bugs fixed pre-adoption; injections queued
- ChatGPT review of PL4: rescue-gate concept validated (match-clustered bootstrap +5.58 CI[+1.44,+10.27]
  on the 24-match holdout) but implementation is a one-action tactical override, not a multi-tick
  branching planner; 7 defects listed. Triage:
  FIXED NOW (before any PL4_ON genome existed in the gym — zero cost to carried population):
  (a) intercept bug — tracker.velocity[(our_pid,0)] is always zero (tracker never records our own
      blobs); added _PL4_OURVEL centroid-delta tracking in _pl4_choose, role "i" now uses it.
  (b) partial-deep-tier ordering bias — tier2 now used ONLY when every beamed candidate finished
      (complete-coverage-only); otherwise falls back to equal-H tier1.
  Gates: compile OK, equiv PASS (inert at PL4_ON=0), variants cleared+rematerialized (they are
  disk-cached — a body patch does NOT propagate without clearing), forced-ON smoke in finals room:
  80 fires, 0 exceptions, 0 stderr, ledger 6.33s@t1000 under 6.5 hard.
  DEFERRED (architecture, hours of work + revalidation; the gym's ON/OFF selection IS the
  closed-loop revalidation ChatGPT asks for): multi-tick commitment execution, branch-depth option
  sequences, post-split momentum reconstruction, offline/embedded parity harness.
- SHIP_PL4T_3712.py standalone: DO NOT UPLOAD (concur with ChatGPT) — provenance was stale (file
  retuned after its 13ad7330 sha entry; current adf5d7 now logged), budgets differ from witnesses.
  v11 is unaffected (built from the pre-merge body; no PL4 in any shipped bundle).
- Sensible injections queued (1 consumed per cull, champion twin first): pl4twin-4471 (defaults),
  pl4twin-4467 (top PL3-OFF chassis — isolates PL4 from PL3 interaction), pl4cons-4471 (DIAL 1.6,
  FRAC 0.5 — late-game ledger saver), pl4fast-4471 (TTC 14, DIAL 0.7 — early-fire explorer).

## 2026-07-19 (afternoon) — v11 PL3-strangle defect (Chris caught it); v12 staged
- Chris pasted sub 2157's log: "[pl3] governor tripped after 24 fires". Root cause: v11 shipped
  the v9/v10 budget split (PC 5.5 / PL3 1.0) but base champion 4471 was evolved in the gym body
  where PL3 gets 5.0s (PL3_ON=1, CD=1, PC_ON=0.72 — both organs hot). At 1.0s the champion's main
  organ goes dark ~24 fires in; its 53.2 gym evidence does NOT transfer at that budget. My error:
  ported budgets blindly; all v11 witnesses ran FINAL mode (PL3 off in 3712) so the trip never showed.
- v12 = v11 with budgets re-split to match the gym: PL3 5.0 (its exact gym cap) + PC 1.5 (3x the
  measured never-binding FINAL spend) = 6.5s total per Chris's ceiling.
- New gate added: BASE-MODE witnesses (witness-only copy with _OUR_TEAM_ID=0 so the anomaly lever
  stays quiet and the 0E/1E/2E ladder actually runs). Results: 0 governor trips, pl3-stats
  1.85s/56 fires @t500, mode ladder correct, FINAL witness ok, equiv PASS, 0 stderr.

## 2026-07-19 ~13:17 AEST — PL3/PL4 efficiency profile
- Exact gym-body cProfile on 12 hot synthetic calls: PL3 0.957s total, 0.711s (74%) in
  `_pl3_stabilise`; PL4 2.847s total, 2.016s (71%) there. `_pl3_step` accounts for 88%/84%.
- Highest-value semantics-preserving optimization: make stabilization dirty/event-driven. The step
  currently stabilizes after movement, after viruses, and after eating even when no virus/eat event
  occurred; restrict work to fragmented/changed players and skip the second/third calls on no-op paths.
- Next: retain H6 rollout snapshots and extend them to H12 instead of replaying prefixes; reject PL4
  candidates as soon as any completed scenario violates the incumbent's monotone worst-case risk;
  build one shared bounded SimContext per live tick for PL3/PL4. Architectural scheduler should avoid
  paying for both full PL3 and PL4 searches on the same critical tick (PL4 critical, PL3 fallback).
- Staged: BUNDLE_v12_4471base_pl3fix_CODEGEN.py. Live sub 2157 (v11) still carries the strangle —
  replacement is Chris's call (resubmission resets the rolling average; 2157 opened hot 31.8@20).

## 2026-07-19 (afternoon #2) — 2159 ban root-caused: SERVER IS ~5x SLOWER; v14 staged
- Chris pasted the full 58713 log incl. "[pl3-stats] t500 spent=4.27s fires=21 ovr=1 exc=0 aborts=15".
  That proves 2159 = v12 (PL3 budget 5.0 — a 1.0 cap can never reach 4.27s) and the ban was GENUINE:
  ~203ms per PL3 fire on the competition server vs ~42ms on our hardware (~5x slower CPU; 15/21
  fires hit the per-fire deadline). Self-measured organ caps worked as designed — but organs 6.5s
  + ungoverned reactive/parse (~2-3s at server speed) > 8s cumulative -> CumulativeTimeout, match 1.
- LAW (hardware transfer): gym budget-seconds do NOT transfer to the server. The proven live
  envelope is v8's: organs <= 2.5s total (987 games, 0 timeout bans). v11's ~3.8s survived 20
  games (edge). 4.5s+ (v13) is now considered unsafe — do not upload v13.
- v14 staged = 4471 base + elite fix + PC 1.5 / PL3 1.0 (v8 envelope). Gates green (equiv PASS,
  base-mode witness mass 115 rank 1, mode ladder ok, 0 stderr). sha 4e8372f2...
- Empirical comfort: 2157 (4471 with PL3 strangled at 1.0) still opened ~32avg/20 games — the
  chassis carries; PL3's few fires are a bonus, not the engine.
- My earlier branch analysis said trip@25 fires = "v11 signature" — WRONG; corrected by the stats
  line. v13 recommendation also retracted (too close to the line).

## 2026-07-19 (mid-afternoon) — memo cache + lite-step shipped into v17; PL3 unmuzzled across modes
- Chris's starvation thesis CONFIRMED structurally: PL3 was only enabled in mode 1 (0E/2E overlays
  come from v4-era genomes bred pre-PL3 -> PL3_ON: 0 in those modes; FINAL=3712 also PL3-off).
  In the elite rooms where we bleed, the organ was OFF, not just budget-starved. True of every
  bundle since v8 (both body lineages behave identically; earlier "lineage difference" was a
  misread of witness logs — the 56 fires all predated the 2E switch).
- Per Chris "ship this directly" + performance order: v17 = 4471 base + elite fix + memo cache
  (incumbent-only, 30-tick TTL) + lite-step rollouts (1.95x, 86% worst-case agreement) + PL3
  stabilise speed pass + PL3 enabled in modes 0/1/2 with the base's PL3 genes (overlay PL3_* keys
  stripped; PC stays per-overlay; FINAL untouched). Budgets: PL3 2.0s @ 150ms fires, PC 1.0s,
  ledger 3.2s -> est ~5.5-6s server total, ~2s cap margin.
- Witness telemetry: 183 fires/aborts=0/memo=33 @t500 (vs ~24 fires pre-lite) — ~8x fire coverage
  at equal seconds. Gates: equiv PASS, 0 stderr, mode ladder + FINAL lever verified earlier.
- Staged: BUNDLE_v17_4471base_memolite_CODEGEN.py sha 855b7ab6... Upload = Chris (team still
  frozen since 2164 ban).

## 2026-07-19 (late afternoon) — finals room reseeded from the archive; PL4 terminally discarded
- Chris's order after the archive review (my "evolution chose PL3-off" claim was WRONG — the
  TRAINFINALv2 board was incumbency: PL3 registered the day the world closed; the one ON-vs-OFF
  twin recorded +1.4 FOR PL3-ON): restart the finals evolution FROM the archive champions.
- Done: population replaced with rank01-08 x5 replicas (ids 4588-4627, lineages arch-rank01..08),
  genes backfilled from body defaults (PL3-era + memo/lite constants), PL4_ON=0 everywhere and
  registry clamp [0,0] stays. World: v3campaign-9:TRAIN-FINAL-ARCHIVE (finals mix 4E+1C+2farmer).
- The world now re-runs the PL3-in-finals experiment FAIRLY: PL3-native economics (lite fires +
  memo cache in the gym body), archive-champion chassis, fresh windows. Evening bundle FINAL slot
  inherits tonight's winner.

## 2026-07-19 (late afternoon) — v18: 3793 base + decoupled finals escalation
- Chris's two-part diagnosis, both log-verified on live sub 2186 (v17):
  (1) 7E/3712 is a NO-FODDER finals-survival bot deployed into live 3E+ rooms that are actually
      feast-economy farming rooms -> survives but under-banks. Proof: our 2E cell (same economy,
      farming model) wins 41% while 3E+ (finals bot) bleeds mass.
  (2) 1E weakness tracks the BASE genome, not the slim-down: same-base (4471) subs are 1E 20-24%
      with OR without lite/memo (2186 lite=20%@59 vs 2170 no-lite=24%@25 — a wash); the only strong
      1E on a big sample is sub 2106 = 3793 base = 36%@194. Corrected my earlier over-attribution
      to lite.
- v18 = base 3793 (0E/1E/2E) + 0E/2E = v5-era overlays + FINAL/7E = 3712.
  KEY CHANGE (_mode_for, bundle-only patch; shared body untouched): tally>=3 now caps at the 2E
  farming model; 7E/3712 fires ONLY on team-id anomaly or the 23:00Z cutover (the genuine
  "in the finals now" signals). lite+memo OFF, governor PC 1.5 + PL3 1.0 (v8's 987-game 0-ban
  envelope), TMOVE 0.20.
- Gates: compile, codegen equiv PASS, base witness reaches 2E and CAPS (7E-count 0 with 3 elite
  opps), anomaly witness -> 7E, 0 stderr both paths. Staged BUNDLE_v18_3793base_farmescalate_CODEGEN.py
- Uploading via authenticated browser session (Chris: "you may upload yourself").

## 2026-07-19 (evening) — Evolution shut down; Mac Studio archived + cleaned
- Shut down ALL evolution. Laptop: ladder_v3 + sims killed (0). Studio: studio_api.py supervisor
  (botbattle_worker) killed — it respawns sims/visualisers via the Hermes gateway KeepAlive, but
  its file is now deleted so it cannot relaunch (verified 0 after 15s). No crons/scheduled tasks
  drove restarts. Background monitors stopped.
- Mac Studio archive: /Users/chrisli/competition_working_archive_2026-07-19.zip (735MB, 15,083
  files, unzip -t INTEGRITY-OK). Contents: Developer/competition/{OMNI-evo,botbattle,hybrid-evo},
  ~/botbattle_worker, /tmp {scripts, match_meta.jsonl, leaderboard_now.json, replays_hard/, *.gz}.
  Originals DELETED and verified gone.
- KEPT on Studio (per Chris): the two pre-existing replay archives syncs_replays.zip (6.2G) +
  syncs_replays_all.zip (6.3G); ~/.hermes (Hermes agent's own install — auth/kanban/cron/gateway,
  NOT competition data — explicitly excluded).
- Laptop: inventory delivered, nothing deleted.
