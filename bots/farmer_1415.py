"""ARCH v3 (2026-07-13): dial sockets + 16 node slots + 3 defense sensors.
All extensions NEUTRAL AT DEFAULT (dial guards skip new math at exactly 0.0;
new nodes ship OFF; sensors only extend the feature vector). Node-output
feature base moved 19 -> 22 (genomes migrated +3 on A/B refs >= 19).
Dial targets: 9=THREAT_MULT 10=FEAST_BOLD 11=CYCLE_GATE 12=VULN_MARGIN
13=PREY_BOLD. Force-phase dials (9,10,13): 1-tick latency via tracker.dials;
gate dials (11,12): same-tick.

OMNI-2 BODY (2026-07-10) — omni_feaster + five organs for the previously-
inexpressible behavior classes: wealth-fear (banking), virus-respawn camping,
grudge memory, rank posture, virus slot timing. All zeroable, neutral-at-default.
Built from:

split_feaster - elite_g30 genome + SPLIT-FEAST CYCLE ORGAN (the .12 virus economy).

Decoded from Team-15's 100-mass WINS (raw replays match_1719/1721/1723): the apex
splits aggressively (~21 split-moves/match), oscillates blob count 1<->16, and
vacuums respawning viruses. On engine .12 each virus grants +2.25 mass, CONSERVED
through the shatter (piece_count = max(1, 16-blobs+1)) -- so a consumption at >=15
blobs is ~free mass (pieces=1) with no fragmentation. elite_g30 in the SAME lobby
(match 1721) sent 0 splits, sat at 1 blob, ate 2 viruses, flatlined at ~1 mass and
died r1190 -- its split is a vestigial prey-lunge gated behind mass it never reaches.

CYCLE ORGAN (should_cycle_split): in feast posture, no lethal threat within
CYCLE_THREAT_CLEAR, viruses on the map -> split toward 16 blobs while mass supports
viable halves; the existing virus-feast force vacuums them (free mass at high blob
count); when viruses exhaust or a threat enters, stop splitting and let blobs
regroup/merge. Repeat. Genes SPLIT_CYCLE_ON (vetoable), CYCLE_MIN_MASS,
CYCLE_THREAT_CLEAR -- evolvable, bounds added to evolve_v2.

SHIPPED (live audition, 2026-07-09): cycle genes tuned to 30/28 ("only split-feast
once big AND safe" -- minimises deaths-while-fragmented). Uncontested reference
(n=4) reproduces the 910 oscillation: splits 45, cons 39, peak mass 99 (~Team-15's
100). The gym A/B scored it ~parity with elite_g30 (-1.85 n=100), but the gym is
proven UNFAITHFUL (elite_g30 = 52% gym / dead-at-5.4-mass in real match 1721), so
it penalises the very virtue under test -- this ships to the LIVE court. Live
tripwires (n>=15): cons/match >=15, avg mass vs elite_g30 19.2 baseline, bust rate,
deaths-while-fragmented.

--- base elite_g30 genome below ---
gen099_m12b - .12 mass-space re-derived margins (from gen099_m12).

m12 ported radius-VALUES into mass-space, doubling effective caution (flee at
1.086x radius vs lethal 1.095x -> flagged non-lethal enemies as threats). m12b
re-derives the margin at the .12 rule: SAFETY_RATIO seeded at 1.39 in mass-space (the measured optimum)
(soft threat-avoid flags only enemies that can actually eat us, mass >= 1.2x +
small buffer), evolvable with mass-space bounds (1.15, 2.0). The hard VETO still
fires at the true lethal line (EAT_RATIO=1.2, kill_envelope). Prey eligibility
unchanged (mass >= 1.2, already correct in m12). Pilot series isolated the variable: m12 (1.18) lost -6.45, m12b(1.30) lost
-3.08, i19's effective radius-margin (~1.39 in mass) won. Seeded at 1.39 = the
measured optimum so evolution explores AROUND the known-good setting rather than
climbing to it. Evolvable, bounds (1.15, 2.0). Below is the m12 port note.

gen099_m12 - .12 mass-rule port of gen099_i19.

Engine 2026.1.12 changed engine/state/state_mutator.py _can_eat_blob from
radius-space to mass-space:
    .11:  eater.radius < target.radius * EAT_SIZE_RATIO   (radius x 1.2)
    .12:  eater.mass   < target.mass   * EAT_SIZE_RATIO   (mass  x 1.2)
EAT_SIZE_RATIO unchanged = 1.2; since mass ~ radius^2 the lethal RADIUS ratio
dropped 1.2 -> sqrt(1.2) ~ 1.0954. Every eat/flee/prey/safety comparison is
ported radius-space -> mass-space (radii wrapped in mass(); split-halves via
mass(r/sqrt(2)) = mass(r)/2). EAT_RATIO(1.2)/SAFETY_RATIO(1.18) reused as-is
(already <= the 1.2 mass eat ratio -> correct margins). 6 sites ported
(gen099_i19 lines 186,191,254,257,272,287). NOT ported: the SPLIT_SAFETY_RATIO
=0.0101 split-lunge gate (a degenerate evolved gene, not the 1.2 eat ratio).
Virus gate unchanged in .12. The intent_split branch is inert under .12 move-
event censoring.

--- base gen099_i19 ---
SYNCS Bot Battle 2026 — potential-field bot.

Architecture (single file, as required for submission):
  1. CONFIG        — every tunable weight lives here. Tune nothing else.
  2. Tracker       — remembers enemy blob positions across ticks -> velocity
                     estimates for predictive interception/fleeing.
  3. Forces        — each visible object contributes an attraction/repulsion
                     vector; we move along the weighted sum.
  4. Split logic   — hard-coded tactical rule, gated by safety checks.

Engine facts baked in (from lib/config):
  arena 60x60, 8 players, 1400 rounds @ 0.1s, eat ratio 1.2x,
  speed = 1.1 - 0.08*r (min 0.25), mass decay 0.2%/tick,
  split needs mass >= 2.0, eject speed 1.6 w/ drag 0.82, max 16 blobs,
  6 viruses r=1.5, respawn after 30 rounds. Mass ~ radius^2.
"""

import math
import sys
import traceback

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.events.moves.typing import MoveType
from lib.interface.queries.query_move import QueryMovePlayer
from lib.interface.queries.typing import QueryType
from lib.models.penguin_model import DirectionModel

BASE_PLAYER_SPEED = 1.1
PLAYER_SPEED_RADIUS_FACTOR = 0.08
MIN_PLAYER_SPEED = 0.25


def blob_speed(radius: float) -> float:
    return max(BASE_PLAYER_SPEED - PLAYER_SPEED_RADIUS_FACTOR * radius, MIN_PLAYER_SPEED)

# ----------------------------------------------------------------------------
# 1. CONFIG — the only block you should touch when tuning.
# ----------------------------------------------------------------------------
CONFIG = {
    "LOOKAHEAD_ON": 1,
    "LA_HORIZON": 2,
    "LA_VIRUS": 0.950424,
    "LA_MISS": 0,
    "LA_ATTACK": 1,
    "W_FOOD": 0.000947525,
    "W_PREY": 12.2394,
    "W_THREAT": 1.15635,
    "W_VIRUS_BIG": 0.0605746,
    "W_WALL": 2.99618e-06,
    "W_REGROUP": 1.8555e-07,
    "FOOD_FALLOFF": 1.81871,
    "PREY_FALLOFF": 0.175839,
    "THREAT_FALLOFF": 2.52484e-07,
    "THREAT_PANIC_DIST": 0.100971,
    "THREAT_PANIC_MULT": 7.2491e-05,
    "THREAT_IGNORE_DIST": 30.7329,
    "SPLIT_REACH": 51.3259,
    "W_SPLIT_ZONE": 0.05,
    "WALL_MARGIN": 1.10337e-06,
    "FRESH_MASS": 3.39598,
    "FRESH_CAUTION": 0.000285424,
    "VETO_ENABLED": False,
    "VETO_MARGIN": 5.23265e-06,
    "VETO_HORIZON": 8.61426,
    "VETO_SOFT_MASS": 1.02335,
    "LOCK_ENABLED": False,
    "LOCK_MIN_VALUE": 0.000586905,
    "LOCK_TICKS_MAX": 49.3216,
    "LOCK_ABANDON_T": 21.2219,
    "W_LOCK": 0.00541653,
    "LOCK_THREAT_BREAK": 0.000106604,
    "LUNGE_DISC_PANIC": 2,
    "SPLIT_RUN_ENABLED": False,
    "SPLIT_RUN_MAX_MASS": 5.49263e-08,
    "SPLIT_RUN_TRIGGER": 0.0273276,
    "EAT_RATIO": 1.2,
    "SAFETY_RATIO": 1.15,
    "LEAD_TICKS": 1.8833,
    "LUNGE_ALARM_DIST": 12,
    "W_LUNGE_ALARM": 2,
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 22.3817,
    "SPLIT_SAFETY_RATIO": 4.68492e-05,
    "SPLIT_MAX_BLOBS": 1.06671,
    "SPLIT_THREAT_CLEARANCE": 12,
    "SPLIT_MIN_MASS": 2,
    "SPLIT_MAX_MASS": 413.751,
    "VIRUS_DANGER_MASS_RATIO": 1.2,
    "VIRUS_AVOID_DIST": 1.12378,
    "VIRUS_FEAST_CLEAR": 7.96238,
    # (BOOT_* and W_VIRUS_FOOD amputated 07-09: dead code paths, wasted mutations)
    "FEAST_MIN_MASS": 4,
    "FEAST_SLOT_SAT": 0.3,
    "W_VIRUS_FEAST": 2.5,
    # --- SPLIT-FEAST CYCLE ORGAN (Team-15 virus economy; matches 1719/1721/1723) ---
    "SPLIT_CYCLE_ON": 0.6589,        # vetoable master switch (>0.5 = on); bounds (0,1)
    "CYCLE_MIN_MASS": 44.1637,       # only cycle once BIG (don't fragment a small bank); bounds (4,40)
    "CYCLE_THREAT_CLEAR": 2.9215,   # only cycle when threats are FAR (avoid deaths-while-fragmented); bounds (2,30)
    # --- OMNI SWEEP (2026-07-09): every organ zeroable; magic numbers freed ---
    # promoted magic numbers (were hardcoded; evolution could never reach them)
    "HUNTER_AVOID_MULT": 0.75,     # virus-avoid radius mult when hunter near (was 1.5)
    "HUNTER_REPEL_MULT": 3,     # virus repulsion mult when hunter near (was 2.0)
    "WALL_ESC_MARGIN_MULT": 1.43412,  # wall-escape activation margin (was 1.2)
    "WALL_ESC_NUDGE": 0.116942,        # outward nudge strength (was 0.2)
    "LUNGE_DISC_FRAC": 0.690378,       # deep-disc panic fraction (was 0.9)
    "SPLIT_ALIGN_MIN": 0.45046,       # prey-lunge alignment gate (was 0.7)
    "DEATH_COST_SCALE": 12.7258,     # bank-size fear scaling divisor (was 25)
    "VIRUS_FEAST_FALLOFF": 0.2,   # feast attraction falloff exponent (was 1/d)
    "CYCLE_TARGET_BLOBS": 9.12059,   # cycle split ceiling (was 16)
    # ORGAN: corner-siege fix (uncatchable corner-tucked prey -> zero force)
    "CORNER_SKIP_ON": 0.899687,        # >0.5 on; bounds (0,1). Hard-ON fleet-wide 2026-07-13:
                                  # veto existed but 0.394 gated it off and the gene was
                                  # frozen out of the registry (500-round corner sieges)
    "CORNER_TUCK": 0.579234,
    "CORNER_MARGIN": 0.000185717,
    "CORNER_VETO_TICKS": 28.2811,       # sticky veto: uncatchable corner target is blacklisted
                                  # this many ticks (refreshed while tucked; released early
                                  # if it leaves 2x the tuck zone) — kills siege oscillation.
                                  # 0 = exact original per-tick corner-fix reading (blacklist
                                  # expires instantly). EVOLVABLE (Chris 2026-07-13): bounds
                                  # (0,150) in registry; right dose unknown (30? 50? 100?)
    # ORGAN: sized threat gate (only count watchers that can actually eat us)
    "THREAT_SIZE_GATE": 0,      # 0=all threats count (legacy); >0: hunter_near only if threat mass >= ours*gate
    # ORGAN: virus shield (hide behind viruses; big pursuers pop crossing them)
    "W_VIRUS_SHIELD": 0.00236869,        # 0=off; attraction to viruses when fleeing while small
    "SHIELD_MAX_MASS": 2,       # only shield when total below this (we pass under gate)
    # ORGAN: fragment hunting (counter the split-feast meta: eat cyclers mid-cycle)
    "W_FRAG_HUNT": 0.000475288,           # 0=off; prey-force mult vs players at high blob count
    "FRAG_HUNT_MIN_BLOBS": 5.04291,   # enemy blob count to trigger
    # ORGAN: piece guard (post-consumption regroup surge; heals the loss30 wound)
    "W_PIECE_GUARD": 0.00571743,         # 0=off; extra regroup for GUARD_TICKS after our shatter
    "PIECE_GUARD_TICKS": 3.02803,
    # ORGAN: idle merge drive (cycle regroup half: pull together when no virus work)
    "W_MERGE_IDLE": 3.90184e-06,          # 0=off; regroup when fragmented + no viruses visible
    # ORGAN: map positioning (center vs edge preference; evolution picks sign)
    "W_CENTER": 0.000110134,              # 0=off; + seeks center, - seeks edges
    # ORGAN: hunger-scaled food greed (small bots chase pellets harder)
    "FOOD_HUNGER_EXP": 1.21218e-05,       # 0=off; food force *= (1/total_mass)^exp
    # ORGAN: stall kick (anti-deadlock: displacement ~0 while mass decays -> kick)
    "STALL_KICK_ON": 0.00539431,         # >0.5 on
    "STALL_TICKS": 16.4997,
    "STALL_DIST": 0.225005,
    "W_STALL_KICK": 0.477484,
    # ORGAN: endgame posture (protect the bank late; final mass IS the score)
    "ENDGAME_START": 0.3,         # fraction of EXPECTED_ROUNDS after which endgame fear applies; 1.0=off
    "ENDGAME_FEAR_MULT": 2.22362,     # threat-force mult in endgame; 1.0=neutral
    "EXPECTED_ROUNDS": 1400,
    # ORGAN: speed-aware threat pricing (slow giants can't catch us outside envelope)
    "W_ENVELOPE_SCALE": 0.174885,      # 0=off; scales threat force by kill-envelope proximity
    # ORGAN: per-player aggression memory (avoid players who hunt US specifically)
    "AGGRO_ON": 3.91473e-07,              # >0.5 on
    "W_AGGRO": 8.02757e-06,               # extra threat weight vs measured aggressors
    # ===== OMNI-2 ORGANS (2026-07-10): the four inexpressible classes + virus timing =====
    # ORGAN W1: WEALTH PRESERVATION — mass-conditional fear (banking). live evidence: peak-69 -> final-0.8 deaths
    "W_WEALTH_FEAR": 0,         # 0=off; threat force mult grows with own mass above WEALTH_START
    "WEALTH_START": 40,         # own total mass where wealth fear begins
    "WEALTH_EXP": 1,            # curve shape
    # ORGAN W2: VIRUS-RESPAWN CAMPING — engine law: virus respawns ~30 rounds after consumption
    "W_CAMP": 0,                # 0=off; attraction to due-respawn sites inside the window
    "CAMP_WINDOW_LO": 18,       # rounds since consumption when attraction starts
    "CAMP_WINDOW_HI": 45,       # ... and ends (site pruned)
    "CAMP_MAX_MASS": 148.002,        # too rich to camp (banking dominates)
    # ORGAN W3: GRUDGE MEMORY — per-opponent caution after they cost us mass
    "W_GRUDGE": 0,              # 0=off; extra threat weight vs players who ate our blobs
    "GRUDGE_DECAY": 0.995,        # per-tick decay
    # ORGAN W4: RANK POSTURE — visible-field standings condition greed/fear
    "W_RANK_GUARD": 0,          # 0=off; threat mult when leading the visible field
    "W_RANK_AGGRO": 0,          # 0=off; prey mult when trailing the visible field
    # ORGAN W5: VIRUS SLOT TIMING — pieces=max(1,17-blobs): saturated consumption is free mass
    "VIRUS_SLOT_EXP": 0,        # 0=off; feast force *= (blobs/16)^exp
    # ===== OMNI-2.1 PROFILER (in-body stupid/mid/elite classifier; Chris's order 2026-07-10) =====
    "PROF_ON": 0,                 # MASTER GATE: <=0.5 -> entire profiler off (zero compute, zero state)
    "PROF_ELITE_T": 0.62,           # EMA score above -> ELITE
    "PROF_STUPID_T": 0.42,          # EMA score below -> STUPID
    "PROF_RADIUS": 14,            # elite-proximity radius gating feast boldness
    "PROF_PREY_STUPID": 0,        # extra prey force vs STUPID targets
    "PROF_PREY_ELITE_DISC": 0,    # prey force discount vs ELITE targets (0..1)
    "PROF_THREAT_STUPID_DISC": 0, # threat force discount for STUPID giants (0..1)
    "PROF_THREAT_ELITE_MULT": 0,  # extra threat force vs proven-ELITE hunters
    "PROF_FEAST_BOLD": 0,         # virus-feast/cycle boldness when no ELITE within PROF_RADIUS
    # ===== OMNI-2.1 corner refuge (gate = weight > 0) =====
    "W_CORNER_REFUGE": 0,         # when hunted by an uncatchable-for-us giant: tuck into ITS unreachable corner
    "AGGRO_DECAY": 0.9,
    # ===== VULN ORGAN v2 (2026-07-12): targeted split-kill executor =====
    # Target selector + short pursuit lock + safety evaluator + ATOMIC direction+split.
    # Bypasses the CGP graph entirely (tactical, not strategic). Conservative v1 gates.
    "VULN_ON": 1,
    "VULN_DETECT_RANGE": 15,     # approach/detection radius (NOT the commit range)
    "VULN_COMMIT_MARGIN": 0.75,    # subtracted from physics-derived max split reach
    "VULN_MIN_COOLDOWN": 10,       # target merge_cooldown must exceed this
    "VULN_EAT_MARGIN": 1.12997,       # post-split half must out-mass target*EAT_RATIO*this
    "VULN_THREAT_CLEAR": 12,     # hard veto: any half-eater within this range
    "VULN_APPROACH_WEIGHT": 0.5,   # steering blend toward target in approach phase
    "VULN_MIN_TARGET_MASS": 0.5,   # do not split for crumbs
    "VULN_MAX_BANK_RISK": 53.8042,    # never fire while wealthy (bank is the score)
    "VULN_LOCK_TICKS": 4,          # short pursuit lock (fleeting opportunity)
    "VULN_MAX_BLOBS": 2,           # v1: only act when 1-2 blobs (whole-bot commit)
    # ===== ARCH-EVO RESIDUAL GRAPH =====
    # Evolves small decision architecture on top of the proven chassis.
    # Each node chooses two inputs, an operation, and an output target.
    # Integer-like genes should be rounded/clamped by the evolution harness.
    # Feature ids 0..15; node outputs are appended sequentially:
    # N0=16, N1=17, ... N10=26. A node may only consume base features or
    # outputs from earlier nodes, which keeps the graph acyclic and safe.
    # Ops: 0=A, 1=A+B, 2=A-B, 3=A*B, 4=max, 5=min,
    #      6=sigmoid(K*A+BIAS), 7=(A>B), 8=abs(A-B), 9=A/(|B|+.1), 10=1-A.
    # Strategic mixer targets:
    # 0=none, 1=food logit, 2=prey logit, 3=escape logit, 4=virus logit,
    # 5=center logit, 6=incumbent-vector logit, 7=guarded ordinary split vote,
    # 8=guarded cycle-split vote. The graph constructs the movement policy,
    # rather than merely adding small residual forces.
    "ARCH_ON": 1,
    "ARCH_AUTHORITY": 0.35,       # graph share of final steering; evolve in [0.35, 1.0]
    "ARCH_MIN_AUTHORITY": 0.35,   # prevents selection solving architecture by silencing it
    "ARCH_SPLIT_THRESHOLD": 0.452162,
    "ARCH_SPLIT_THREAT_CLEAR": 12,
    "ARCH_MAX_ACTIVE": 8,
    # Baseline channel logits. exp(logit) becomes the primitive's positive weight.
    # The incumbent channel keeps the mature controller available, but does not dominate.
    "ARCH_BASE_FOOD": -1,
    "ARCH_BASE_PREY": -0.8,
    "ARCH_BASE_ESCAPE": -0.8,
    "ARCH_BASE_VIRUS": -1,
    "ARCH_BASE_CENTER": -1.5,
    "ARCH_BASE_INCUMBENT": 0.5,

    "ARCH_N0_ON": 0.987313,
    "ARCH_N0_OP": 4,
    "ARCH_N0_A": 14,       # late_phase
    "ARCH_N0_B": 1,        # prey_opportunity
    "ARCH_N0_K": 0.2,
    "ARCH_N0_BIAS": -2,
    "ARCH_N0_TARGET": 4,   # prey channel logit
    "ARCH_N0_GAIN": 1.03965,

    "ARCH_N1_ON": 0.283439,
    "ARCH_N1_OP": 10,
    "ARCH_N1_A": 5,        # threat_pressure
    "ARCH_N1_B": 3,        # wealth
    "ARCH_N1_K": 2.00883,
    "ARCH_N1_BIAS": -0.122259,
    "ARCH_N1_TARGET": 4,   # escape channel logit
    "ARCH_N1_GAIN": -0.0333917,

    "ARCH_N2_ON": 0.640335,
    "ARCH_N2_OP": 5,
    "ARCH_N2_A": 14,       # feast_ready
    "ARCH_N2_B": 23,        # threat_pressure
    "ARCH_N2_K": 6,
    "ARCH_N2_BIAS": -2,
    "ARCH_N2_TARGET": 6,   # guarded ordinary split vote
    "ARCH_N2_GAIN": 0.679025,

    "ARCH_N3_ON": 1,
    "ARCH_N3_OP": 0,
    "ARCH_N3_A": 8,
    "ARCH_N3_B": 0,
    "ARCH_N3_K": 0.2,
    "ARCH_N3_BIAS": -1.33025,
    "ARCH_N3_TARGET": 5,
    "ARCH_N3_GAIN": -1.5,

    "ARCH_N4_ON": 1,
    "ARCH_N4_OP": 3,
    "ARCH_N4_A": 11,
    "ARCH_N4_B": 19,
    "ARCH_N4_K": 6,
    "ARCH_N4_BIAS": -0.309839,
    "ARCH_N4_TARGET": 5,
    "ARCH_N4_GAIN": -0.622176,

    "ARCH_N5_ON": 1,
    "ARCH_N5_OP": 3,
    "ARCH_N5_A": 20,
    "ARCH_N5_B": 19,
    "ARCH_N5_K": 1.02967,
    "ARCH_N5_BIAS": -2,
    "ARCH_N5_TARGET": 3,
    "ARCH_N5_GAIN": 1.5,

    "ARCH_N6_ON": 1,
    "ARCH_N6_OP": 0,
    "ARCH_N6_A": 19,
    "ARCH_N6_B": 0,
    "ARCH_N6_K": 5.50626,
    "ARCH_N6_BIAS": 0.0630914,
    "ARCH_N6_TARGET": 9,
    "ARCH_N6_GAIN": -0.651235,

    "ARCH_N7_ON": 1,
    "ARCH_N7_OP": 3,
    "ARCH_N7_A": 3,
    "ARCH_N7_B": 19,
    "ARCH_N7_K": 3.16674,
    "ARCH_N7_BIAS": 1.23705,
    "ARCH_N7_TARGET": 13,
    "ARCH_N7_GAIN": 1.31445,

    "ARCH_N8_ON": 0.499292,
    "ARCH_N8_OP": 3,
    "ARCH_N8_A": 10,
    "ARCH_N8_B": 19,
    "ARCH_N8_K": 1.61652,
    "ARCH_N8_BIAS": -1.15824,
    "ARCH_N8_TARGET": 9,
    "ARCH_N8_GAIN": 1.5,

    "ARCH_N9_ON": 0,
    "ARCH_N9_OP": 3,
    "ARCH_N9_A": 18,
    "ARCH_N9_B": 19,
    "ARCH_N9_K": 0.2,
    "ARCH_N9_BIAS": 0.368604,
    "ARCH_N9_TARGET": 9,
    "ARCH_N9_GAIN": 1.5,

    "ARCH_N10_ON": 0,
    "ARCH_N10_OP": 4,
    "ARCH_N10_A": 12,
    "ARCH_N10_B": 19,
    "ARCH_N10_K": 0.684808,
    "ARCH_N10_BIAS": -1.18862,
    "ARCH_N10_TARGET": 3,
    "ARCH_N10_GAIN": -1.5,
    "ARCH_N11_ON": 0.812803,
    "ARCH_N11_OP": 3,
    "ARCH_N11_A": 28,
    "ARCH_N11_B": 6,
    "ARCH_N11_K": 2.0785,
    "ARCH_N11_BIAS": -0.676983,
    "ARCH_N11_TARGET": 5,
    "ARCH_N11_GAIN": -1.5,
    "ARCH_N12_ON": 0.980387,
    "ARCH_N12_OP": 3,
    "ARCH_N12_A": 23,
    "ARCH_N12_B": 14,
    "ARCH_N12_K": 3.24323,
    "ARCH_N12_BIAS": -2,
    "ARCH_N12_TARGET": 11,
    "ARCH_N12_GAIN": -1.5,
    "ARCH_N13_ON": 0.410537,
    "ARCH_N13_OP": 3,
    "ARCH_N13_A": 8,
    "ARCH_N13_B": 9,
    "ARCH_N13_K": 3.41717,
    "ARCH_N13_BIAS": -2,
    "ARCH_N13_TARGET": 11,
    "ARCH_N13_GAIN": -0.146441,
    "ARCH_N14_ON": 0,
    "ARCH_N14_OP": 0,
    "ARCH_N14_A": 12,
    "ARCH_N14_B": 0,
    "ARCH_N14_K": 6,
    "ARCH_N14_BIAS": -0.118625,
    "ARCH_N14_TARGET": 7,
    "ARCH_N14_GAIN": 1.19661,
    "ARCH_N15_ON": 0.939132,
    "ARCH_N15_OP": 6,
    "ARCH_N15_A": 25,
    "ARCH_N15_B": 0,
    "ARCH_N15_K": 0.2,
    "ARCH_N15_BIAS": -2,
    "ARCH_N15_TARGET": 6,
    "ARCH_N15_GAIN": -0.731979,

}

ARENA_SIZE = 60.0
# Engine 2026.1.9: consume gate fixed to documented rule — blob.mass >
# virus.radius^2 * EAT_SIZE_RATIO = 2.7 (blob radius ~1.643). Consuming now
# grants ZERO mass (total_mass=blob.mass): viruses are PURE HAZARDS.
VIRUS_MASS = 2.25
EPS = 1e-9


def mass(radius: float) -> float:
    return radius * radius


# ----------------------------------------------------------------------------
# 2. Velocity tracker for enemy blobs.
# ----------------------------------------------------------------------------
class Tracker:
    def __init__(self) -> None:
        self._last: dict[tuple[int, int], tuple[float, float]] = {}
        self.velocity: dict[tuple[int, int], tuple[float, float]] = {}
        # broadcast intent (engine currently leaks every player's submitted move)
        self.intent_dir: dict[int, tuple[float, float]] = {}   # player_id -> unit direction
        self.intent_split: dict[int, bool] = {}                # player_id -> split flag last tick
        self.split_clock: dict[int, int] = {}                  # rounds since player last split
        # OMNI: per-player blob counts (fragment hunting), own shatter clock,
        # aggression memory, tick counter, stall detection
        self.blob_count: dict[int, int] = {}
        self.my_blob_count: int = 1
        self.shatter_clock: int = 9999
        self.aggro: dict[int, float] = {}
        self.tick: int = 0
        self._stall_anchor: tuple[float, float] = (0.0, 0.0)
        self._stall_since: int = 0
        # OMNI-2 state
        self.grudge: dict[int, float] = {}                 # player_id -> grudge score
        self.prev_total_mass: float = 0.0
        self.prev_virus_pos: list = []                     # last tick's virus positions
        self.camp_sites: list = []                         # (x, y, tick_of_consumption)
        self.corner_veto: dict[int, int] = {}              # player_id -> veto expiry tick
        # ARCH v3 dials (graph-computed dose multipliers; 0.0 = exactly neutral)
        self.dials = {"threat": 0.0, "feast": 0.0, "prey": 0.0,
                      "cycle_gate": 0.0, "vuln_margin": 0.0}
        # OMNI-2.1 profiler state (only written when PROF_ON)
        self.vuln_target_key = None        # (player_id, blob_id) pursuit lock
        self.vuln_lock_left = 0
        self.vuln_last_score = 0.0
        self.vuln_commit = None            # (tick, player_id, blob_id) of last commit
        self.vuln_stats = {"detect": 0, "commit": 0, "kill10": 0, "switch": 0}
        self.prof_score: dict[int, float] = {}             # player_id -> EMA skill score (0..1, init 0.5)
        self.prof_last: dict[int, tuple] = {}              # player_id -> (cx, cy, mass)

    def read_intents(self, game: Game) -> None:
        """Engine currently forwards every player's move_player event unchanged.
        Harvest direction + split flag; degrade gracefully if this gets patched."""
        self.intent_split = {}
        for pid in list(self.split_clock):
            self.split_clock[pid] += 1
        try:
            new = game.state.event_history[game.state.new_events:]
        except Exception:
            return
        for e in new:
            if getattr(e, "event_type", None) == "move_player":
                pid = getattr(e, "player_id", None)
                if pid is None or pid == game.state.me.player_id:
                    continue
                try:
                    dx, dy = e.direction.to_vector()
                    d = math.hypot(dx, dy)
                    if d > EPS:
                        self.intent_dir[pid] = (dx / d, dy / d)
                except Exception:
                    pass
                if getattr(e, "split", False):
                    self.intent_split[pid] = True
                    self.split_clock[pid] = 0

    def update(self, blobs, my_player_id: int) -> None:
        self.tick += 1
        self.shatter_clock += 1
        counts: dict[int, int] = {}
        my_count = 0
        for b in blobs:
            if b.player_id == my_player_id:
                my_count += 1
            else:
                counts[b.player_id] = counts.get(b.player_id, 0) + 1
        if my_count > self.my_blob_count + 3:   # sudden jump = we shattered
            self.shatter_clock = 0
        self.my_blob_count = max(my_count, 1)
        self.blob_count = counts
        seen: set[tuple[int, int]] = set()
        for b in blobs:
            if b.player_id == my_player_id:
                continue
            key = (b.player_id, b.blob_id)
            seen.add(key)
            if key in self._last:
                lx, ly = self._last[key]
                self.velocity[key] = (b.pos[0] - lx, b.pos[1] - ly)
            self._last[key] = b.pos
        for pid in list(self.aggro):
            self.aggro[pid] *= CONFIG["AGGRO_DECAY"]
        if CONFIG["W_GRUDGE"] > 0 and self.grudge:   # contract: zero compute when organ off
            for pid in list(self.grudge):
                self.grudge[pid] *= CONFIG["GRUDGE_DECAY"]
                if self.grudge[pid] < 0.01:
                    del self.grudge[pid]
        # drop stale entries so respawned ids don't inherit old velocity
        for key in list(self._last):
            if key not in seen:
                self._last.pop(key, None)
                self.velocity.pop(key, None)

    def predict(self, blob, ticks: int) -> tuple[float, float]:
        # prefer broadcast intent (exact heading) scaled by size-derived speed
        d = self.intent_dir.get(blob.player_id)
        if d is not None:
            step = blob_speed(blob.radius)
            return (blob.pos[0] + d[0] * step * ticks, blob.pos[1] + d[1] * step * ticks)
        vx, vy = self.velocity.get((blob.player_id, blob.blob_id), (0.0, 0.0))
        return (blob.pos[0] + vx * ticks, blob.pos[1] + vy * ticks)


SPLIT_COOLDOWN_T = 18


def blob_speed_of(r: float) -> float:
    return max(1.1 - 0.08 * r, 0.25)


def kill_envelope(threat, my_r: float, tracker) -> float:
    """Radius inside which this threat can plausibly kill a blob of radius my_r.
    Physics frozen: contact always; chase only at positive closing speed;
    lunge disc only if halves eat us AND its split cooldown has elapsed."""
    r = 0.0
    if mass(threat.radius) >= mass(my_r) * CONFIG["EAT_RATIO"]:
        r = threat.radius + my_r + 1.0
        closing = blob_speed_of(threat.radius) - blob_speed_of(my_r)
        if closing > 0:
            r = max(r, threat.radius + my_r + closing * CONFIG["VETO_HORIZON"] * 2)
    if mass(threat.radius / math.sqrt(2)) >= mass(my_r) * CONFIG["EAT_RATIO"] and mass(threat.radius) >= 4.0:
        if tracker.split_clock.get(threat.player_id, SPLIT_COOLDOWN_T + 1) > SPLIT_COOLDOWN_T:
            r = max(r, 8.9 + my_r + threat.radius / math.sqrt(2))
    return (r + CONFIG["VETO_MARGIN"]) if r > 0 else 0.0


class HuntLock:
    def __init__(self) -> None:
        self.key = None
        self.ticks = 0


HUNT = HuntLock()
N_VETO_DIRS = 16
VETO_DIRS = [(math.cos(2 * math.pi * k / N_VETO_DIRS), math.sin(2 * math.pi * k / N_VETO_DIRS))
             for k in range(N_VETO_DIRS)]


# ----------------------------------------------------------------------------
# 3. Force computation.
# ----------------------------------------------------------------------------
def unit(dx: float, dy: float) -> tuple[float, float, float]:
    d = math.hypot(dx, dy)
    if d < EPS:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


def compute_forces(game: Game, tracker: Tracker) -> tuple[float, float, dict]:
    st = game.state
    me = st.me
    cx, cy = me.x, me.y
    my_blobs = list(me.blobs.values())
    my_largest = max((b.radius for b in my_blobs), default=me.radius)
    my_smallest = min((b.radius for b in my_blobs), default=me.radius)
    total_mass = sum(mass(b.radius) for b in my_blobs) or mass(me.radius)

    fx, fy = 0.0, 0.0
    info = {"threats": [], "prey": []}

    # FRESH-SPAWN SURVIVAL MODE: respawn-farming killed us repeatedly.
    # Until re-established (total mass < FRESH_MASS), fear doubles, greed halves.
    fresh = total_mass < CONFIG["FRESH_MASS"]
    caution = CONFIG["FRESH_CAUTION"] if fresh else 1.0

    # --- OMNI-2 bookkeeping ---
    # visible-field standings (W4): sum visible mass per player
    _vis = {}
    for _b in st.visible_blobs:
        _vis[_b.player_id] = _vis.get(_b.player_id, 0.0) + mass(_b.radius)
    rank_lead = total_mass >= max(_vis.values(), default=0.0)
    # grudge attribution (W3): sharp own-mass drop -> blame nearest visible threat-sized blob
    if CONFIG["W_GRUDGE"] > 0:
        if tracker.prev_total_mass > 8.0 and total_mass < tracker.prev_total_mass * 0.72:
            _cands = [(_b, (_b.pos[0]-cx)**2 + (_b.pos[1]-cy)**2) for _b in st.visible_blobs
                      if mass(_b.radius) >= total_mass]
            if _cands:
                _culprit = min(_cands, key=lambda t: t[1])[0]
                tracker.grudge[_culprit.player_id] = tracker.grudge.get(_culprit.player_id, 0.0) + 1.0
        tracker.prev_total_mass = total_mass
    # respawn-site bookkeeping (W2): a virus present last tick but gone now was consumed
    if CONFIG["W_CAMP"] > 0:
        _now = [v.pos for v in st.visible_viruses]
        for _p in tracker.prev_virus_pos:
            if all((_p[0]-q[0])**2 + (_p[1]-q[1])**2 > 2.25 for q in _now):
                if (cx-_p[0])**2 + (cy-_p[1])**2 < 900:   # only sites we can plausibly see
                    tracker.camp_sites.append((_p[0], _p[1], tracker.tick))
        tracker.prev_virus_pos = _now
        tracker.camp_sites = [c for c in tracker.camp_sites
                              if tracker.tick - c[2] <= CONFIG["CAMP_WINDOW_HI"]]
    # OMNI-2.1 PROFILER sensing (master-gated; contract: zero compute when off)
    prof_tier = {}
    prof_elite_near = False
    if CONFIG["PROF_ON"] > 0.5:
        _cent = {}
        for _b in st.visible_blobs:
            c0 = _cent.setdefault(_b.player_id, [0.0, 0.0, 0.0, 0])
            c0[0] += _b.pos[0]; c0[1] += _b.pos[1]; c0[2] += mass(_b.radius); c0[3] += 1
        for pid, (sx, sy, sm, sn) in _cent.items():
            px, py = sx / sn, sy / sn
            sig = None
            last = tracker.prof_last.get(pid)
            if last is not None:
                lvx, lvy = px - last[0], py - last[1]
                sp = math.hypot(lvx, lvy)
                dux, duy, dd = unit(px - cx, py - cy)
                if sp > 0.05 and dd > EPS:
                    ev = 0.0
                    if sm < total_mass * 0.75 and dd < 15.0:
                        # smaller than us & near: smart prey vectors AWAY from us
                        ev = 1.0 if (lvx * dux + lvy * duy) / sp > 0.35 else 0.0
                    elif sm > total_mass * 1.3 and dd < 20.0:
                        # bigger: smart hunters vector TOWARD us
                        ev = 1.0 if (lvx * dux + lvy * duy) / sp < -0.35 else 0.0
                    else:
                        ev = None
                    growth = 1.0 if sm > last[2] * 1.02 else 0.0
                    split_skill = 1.0 if tracker.intent_split.get(pid) else 0.0
                    parts = [v for v in (ev, growth if sm > 6 else None, split_skill or None) if v is not None]
                    if parts:
                        sig = sum(parts) / len(parts)
            tracker.prof_last[pid] = (px, py, sm)
            if sig is not None:
                old = tracker.prof_score.get(pid, 0.5)
                tracker.prof_score[pid] = 0.97 * old + 0.03 * sig
        for pid, (sx, sy, sm, sn) in _cent.items():
            sc = tracker.prof_score.get(pid, 0.5)
            prof_tier[pid] = "E" if sc > CONFIG["PROF_ELITE_T"] else ("S" if sc < CONFIG["PROF_STUPID_T"] else "M")
            if prof_tier[pid] == "E" and math.hypot(sx / sn - cx, sy / sn - cy) < CONFIG["PROF_RADIUS"]:
                prof_elite_near = True

    # --- food ---
    for food in st.visible_food:
        ux, uy, d = unit(food.pos[0] - cx, food.pos[1] - cy)
        if d < EPS:
            continue
        f = CONFIG["W_FOOD"] / (d ** CONFIG["FOOD_FALLOFF"] + EPS)
        # ORGAN hunger-scaled greed: small bots chase pellets harder (0 = off)
        if CONFIG["FOOD_HUNGER_EXP"] > 0:
            f *= (1.0 / max(total_mass, 0.5)) ** CONFIG["FOOD_HUNGER_EXP"] * 4.0
        fx += ux * f
        fy += uy * f

    # --- enemy blobs ---
    for b in st.visible_blobs:
        if b.player_id == me.player_id:
            continue
        px, py = tracker.predict(b, CONFIG["LEAD_TICKS"])
        ux, uy, d = unit(px - cx, py - cy)
        if d < EPS:
            d = EPS

        if mass(b.radius) >= mass(my_smallest) * CONFIG["SAFETY_RATIO"]:
            # can eat (or nearly eat) at least one of our blobs -> threat
            info["threats"].append((b, d))
            can_split_kill = mass(b.radius / math.sqrt(2)) >= mass(my_smallest) * CONFIG["EAT_RATIO"] \
                and mass(b.radius) >= 2 * 2.0  # halves stay above engine split min
            # SPLIT-ZONE PROPHYLAXIS: never linger inside a split-capable
            # threat's lunge radius (~9u). "Big means slow" does NOT apply to
            # ejected halves; this overrides THREAT_IGNORE_DIST.
            if can_split_kill and d < CONFIG["SPLIT_REACH"] + my_smallest:
                f = caution * CONFIG["W_SPLIT_ZONE"] * mass(b.radius) / (d + EPS)
                if d < CONFIG["LUNGE_DISC_FRAC"] * CONFIG["SPLIT_REACH"]:
                    f *= CONFIG["LUNGE_DISC_PANIC"]  # deep in the disc: this is law
                # the bigger we are, the more a death costs (avg-final-weight metric)
                f *= 1.0 + mass(my_largest) / CONFIG["DEATH_COST_SCALE"]
                fx -= ux * f
                fy -= uy * f
            # SPLIT-LUNGE ALARM: a threat just submitted split aimed our way.
            # Split halves travel ~8.9 units; react even beyond normal ignore range.
            if tracker.intent_split.get(b.player_id) and mass(b.radius / math.sqrt(2)) >= mass(my_smallest) * CONFIG["EAT_RATIO"]:
                idir = tracker.intent_dir.get(b.player_id)
                if idir is not None and d < CONFIG["LUNGE_ALARM_DIST"]:
                    toward = (idir[0] * ux + idir[1] * uy)  # +1 = aimed straight at us
                    if toward > 0.5:
                        f = CONFIG["W_LUNGE_ALARM"] * mass(b.radius) / (d + EPS)
                        fx -= ux * f
                        fy -= uy * f
            if d > CONFIG["THREAT_IGNORE_DIST"]:
                continue  # big means slow: distant threats can't catch us, keep farming
            f = caution * CONFIG["W_THREAT"] * mass(b.radius) / (d ** CONFIG["THREAT_FALLOFF"] + EPS)
            if d < CONFIG["THREAT_PANIC_DIST"]:
                f *= CONFIG["THREAT_PANIC_MULT"]
            # ORGAN aggression memory: players who hunt US get extra berth
            if CONFIG["AGGRO_ON"] > 0.5:
                vx, vy = tracker.velocity.get((b.player_id, b.blob_id), (0.0, 0.0))
                sp = math.hypot(vx, vy)
                if sp > EPS and ((-ux) * vx + (-uy) * vy) / sp > 0.7:
                    tracker.aggro[b.player_id] = tracker.aggro.get(b.player_id, 0.0) + 0.01
                f *= 1.0 + CONFIG["W_AGGRO"] * tracker.aggro.get(b.player_id, 0.0)
            # ORGAN envelope pricing: threats outside their kill envelope are cheap
            if CONFIG["W_ENVELOPE_SCALE"] > 0:
                env = kill_envelope(b, my_smallest, tracker)
                f *= 1.0 + CONFIG["W_ENVELOPE_SCALE"] * max(0.0, (env - d) / (env + EPS))
            # ORGAN endgame fear: late game, the bank IS the score
            if CONFIG["ENDGAME_START"] < 1.0 and tracker.tick > CONFIG["ENDGAME_START"] * CONFIG["EXPECTED_ROUNDS"]:
                f *= CONFIG["ENDGAME_FEAR_MULT"]
            # OMNI-2 W1 wealth fear: the bank IS the score; fear scales with own mass
            if CONFIG["W_WEALTH_FEAR"] > 0 and total_mass > CONFIG["WEALTH_START"]:
                _over = (total_mass - CONFIG["WEALTH_START"]) / max(CONFIG["WEALTH_START"], EPS)
                f *= 1.0 + CONFIG["W_WEALTH_FEAR"] * (_over ** max(CONFIG["WEALTH_EXP"], 0.1))
            # OMNI-2 W3 grudge: proven killers get extra berth
            if CONFIG["W_GRUDGE"] > 0:
                f *= 1.0 + CONFIG["W_GRUDGE"] * tracker.grudge.get(b.player_id, 0.0)
            # OMNI-2 W4 rank guard: leading the visible field -> protect the lead
            if CONFIG["W_RANK_GUARD"] > 0 and rank_lead:
                f *= 1.0 + CONFIG["W_RANK_GUARD"]
            # OMNI-2.1 PROFILER threat shaping: fear proven hunters, not dumb mass
            if CONFIG["PROF_ON"] > 0.5:
                _t = prof_tier.get(b.player_id, "M")
                if _t == "S" and CONFIG["PROF_THREAT_STUPID_DISC"] > 0:
                    f *= max(0.0, 1.0 - CONFIG["PROF_THREAT_STUPID_DISC"])
                elif _t == "E" and CONFIG["PROF_THREAT_ELITE_MULT"] > 0:
                    f *= 1.0 + CONFIG["PROF_THREAT_ELITE_MULT"]
            _dt = tracker.dials["threat"]
            if _dt != 0.0:
                f *= math.exp(_clip(_dt, -2.0, 2.0))   # ARCH v3 threat dial
            fx -= ux * f
            fy -= uy * f
        elif mass(my_largest) >= mass(b.radius) * CONFIG["EAT_RATIO"]:
            # ORGAN corner-skip: geometrically uncatchable corner-tucked prey
            if CONFIG["CORNER_SKIP_ON"] > 0.5:
                wdx = min(b.pos[0], ARENA_SIZE - b.pos[0])
                wdy = min(b.pos[1], ARENA_SIZE - b.pos[1])
                # sticky veto: once judged uncatchable, stay hands-off for
                # CORNER_VETO_TICKS even if it drifts across the tuck boundary
                # (else approach->re-tuck->veto->approach oscillates forever).
                # ZONE-SCOPED (v2, 2026-07-13): the blacklist only suppresses
                # pursuit of this player's blobs NEAR the corner (2x tuck) —
                # their open-field fragments stay huntable (a cornered runt
                # must not shield its owner's 15 harvestable fragments).
                # Entries expire by time only.
                _exp = tracker.corner_veto.get(b.player_id)
                if _exp is not None:
                    if tracker.tick >= _exp:
                        del tracker.corner_veto[b.player_id]
                    elif (wdx < 2.0 * CONFIG["CORNER_TUCK"]
                          and wdy < 2.0 * CONFIG["CORNER_TUCK"]):
                        continue
                if wdx < CONFIG["CORNER_TUCK"] and wdy < CONFIG["CORNER_TUCK"]:
                    # ENGINE TRUTH (state_mutator._can_eat_blob + _clamp_blob_to_arena):
                    # eat iff center-dist <= eater.radius; centers clamped >= radius from walls.
                    # Catchable iff ANY of my mass-capable blobs can reach: from its best corner
                    # position (R, R), distance to prey center must be <= R (minus safety margin).
                    # Old test used touch-range (R + prey_r) -> chased uncatchable corner prey.
                    if not any(
                        mass(mb.radius) >= mass(b.radius) * CONFIG["EAT_RATIO"]
                        and math.hypot(max(mb.radius - wdx, 0.0), max(mb.radius - wdy, 0.0))
                            <= mb.radius - CONFIG["CORNER_MARGIN"]
                        for mb in my_blobs
                    ):
                        tracker.corner_veto[b.player_id] = tracker.tick + int(CONFIG["CORNER_VETO_TICKS"])
                        continue  # geometrically uncatchable -> no force, no info["prey"] entry
                        # (LOCK + split-lunge draw from info["prey"], so the veto covers all pursuit paths)
            f = (CONFIG["W_PREY"] / caution) * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)
            # OMNI-2 W4 rank-aggro: trailing the visible field -> hunt harder
            if CONFIG["W_RANK_AGGRO"] > 0 and not rank_lead:
                f *= 1.0 + CONFIG["W_RANK_AGGRO"]
            # OMNI-2.1 PROFILER prey shaping: stupid prey is real, elite "prey" is bait
            if CONFIG["PROF_ON"] > 0.5:
                _t = prof_tier.get(b.player_id, "M")
                if _t == "S" and CONFIG["PROF_PREY_STUPID"] > 0:
                    f *= 1.0 + CONFIG["PROF_PREY_STUPID"]
                elif _t == "E" and CONFIG["PROF_PREY_ELITE_DISC"] > 0:
                    f *= max(0.0, 1.0 - CONFIG["PROF_PREY_ELITE_DISC"])
            # ORGAN fragment-hunt: cyclers mid-cycle are meals-in-waiting
            if CONFIG["W_FRAG_HUNT"] > 0 and tracker.blob_count.get(b.player_id, 1) >= CONFIG["FRAG_HUNT_MIN_BLOBS"]:
                f *= 1.0 + CONFIG["W_FRAG_HUNT"]
            _dp = tracker.dials["prey"]
            if _dp != 0.0:
                f *= math.exp(_clip(_dp, -2.0, 2.0))   # ARCH v3 prey dial
            fx += ux * f
            fy += uy * f
            info["prey"].append((b, d))

    # --- viruses (2026.1.9): zero reward, pure fragmentation hazard. Avoid
    # whenever we are big enough to pop; harder while any hunter is around. ---
    # 2026.1.11: consuming grants +2.25; shatter = open blob slots.
    # FEAST when posture is safe (big enough OR slot-saturated) and no hunter;
    # otherwise treat poppable viruses as hazards exactly as before.
    can_pop = mass(my_largest) > VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]
    if CONFIG["THREAT_SIZE_GATE"] > 0:
        hunter_near = any(d < CONFIG["VIRUS_FEAST_CLEAR"]
                          and mass(t.radius) >= total_mass * CONFIG["THREAT_SIZE_GATE"]
                          for t, d in info["threats"])
    else:
        hunter_near = any(d < CONFIG["VIRUS_FEAST_CLEAR"] for _, d in info["threats"])
    feast_posture = (total_mass >= CONFIG["FEAST_MIN_MASS"]
                     or len(my_blobs) >= CONFIG["FEAST_SLOT_SAT"])
    for v in st.visible_viruses:
        if not can_pop:
            continue  # sub-threshold blobs pass through harmlessly
        ux, uy, d = unit(v.pos[0] - cx, v.pos[1] - cy)
        if d < EPS:
            continue
        if feast_posture and not hunter_near:
            f = CONFIG["W_VIRUS_FEAST"] / (d ** CONFIG["VIRUS_FEAST_FALLOFF"] + EPS)
            # OMNI-2 W5: value viruses most when slot-saturated (shatter pieces -> 1)
            if CONFIG["VIRUS_SLOT_EXP"] > 0:
                f *= (max(len(my_blobs), 1) / 16.0) ** CONFIG["VIRUS_SLOT_EXP"]
            # OMNI-2.1 PROFILER feast boldness: no elite nearby -> vacuum hard; elite near -> stay modest
            if CONFIG["PROF_ON"] > 0.5 and CONFIG["PROF_FEAST_BOLD"] > 0 and not prof_elite_near:
                f *= 1.0 + CONFIG["PROF_FEAST_BOLD"]
            _df = tracker.dials["feast"]
            if _df != 0.0:
                f *= math.exp(_clip(_df, -2.0, 2.0))   # ARCH v3 feast dial
            fx += ux * f
            fy += uy * f
        elif d < CONFIG["VIRUS_AVOID_DIST"] * (CONFIG["HUNTER_AVOID_MULT"] if hunter_near else 1.0):
            f = CONFIG["W_VIRUS_BIG"] * (CONFIG["HUNTER_REPEL_MULT"] if hunter_near else 1.0) / (d * d + EPS)
            fx -= ux * f
            fy -= uy * f
        # ORGAN virus shield: small and hunted -> stand behind the mine
        if (CONFIG["W_VIRUS_SHIELD"] > 0 and total_mass < CONFIG["SHIELD_MAX_MASS"]
                and not can_pop and info["threats"]):
            f = CONFIG["W_VIRUS_SHIELD"] / (d + EPS)
            fx += ux * f
            fy += uy * f

# --- OMNI-2.1 corner refuge: the mirror of the corner fix (gate = weight > 0) ---
    if CONFIG["W_CORNER_REFUGE"] > 0:
        _hunter = None
        for _t, _d in info["threats"]:
            if _d < 18.0 and _t.radius > my_largest * 1.35:
                if _hunter is None or _d < _hunter[1]:
                    _hunter = (_t, _d)
        if _hunter is not None:
            _R = _hunter[0].radius
            # pick the nearest corner the hunter cannot reach INTO for us:
            # we fit at (r, r); hunter's best reach toward corner is hypot capped by its clamp (R, R)
            _corners = ((0.0, 0.0), (0.0, ARENA_SIZE), (ARENA_SIZE, 0.0), (ARENA_SIZE, ARENA_SIZE))
            _best = None
            for _cxn, _cyn in _corners:
                _tuck_x = my_smallest * 1.05
                _tuck_y = my_smallest * 1.05
                # hunter reach at our tuck point:
                if math.hypot(max(_R - _tuck_x, 0.0), max(_R - _tuck_y, 0.0)) > _R:
                    _dd = math.hypot((_cxn - cx), (_cyn - cy))
                    if _best is None or _dd < _best[0]:
                        _best = (_dd, _cxn, _cyn)
            if _best is not None and _best[0] > EPS:
                ux, uy, d = unit(_best[1] - cx, _best[2] - cy)
                fx += ux * CONFIG["W_CORNER_REFUGE"] / (d + EPS)
                fy += uy * CONFIG["W_CORNER_REFUGE"] / (d + EPS)

    # --- OMNI-2 W2: virus-respawn camping ---
    if CONFIG["W_CAMP"] > 0 and total_mass < CONFIG["CAMP_MAX_MASS"]:
        for (_sx, _sy, _t0) in tracker.camp_sites:
            _age = tracker.tick - _t0
            if CONFIG["CAMP_WINDOW_LO"] <= _age <= CONFIG["CAMP_WINDOW_HI"]:
                ux, uy, d = unit(_sx - cx, _sy - cy)
                if d > EPS:
                    fx += ux * CONFIG["W_CAMP"] / (d + EPS)
                    fy += uy * CONFIG["W_CAMP"] / (d + EPS)

        # --- walls ---
    m = CONFIG["WALL_MARGIN"]
    if cx < m:
        fx += CONFIG["W_WALL"] * (m - cx) / m
    if ARENA_SIZE - cx < m:
        fx -= CONFIG["W_WALL"] * (m - (ARENA_SIZE - cx)) / m
    if cy < m:
        fy += CONFIG["W_WALL"] * (m - cy) / m
    if ARENA_SIZE - cy < m:
        fy -= CONFIG["W_WALL"] * (m - (ARENA_SIZE - cy)) / m

    # --- TANGENTIAL WALL ESCAPE ---
    # Fleeing straight away from a threat into a wall = cornered = dead.
    # If a threat is near and our net force presses into a close wall,
    # remove the into-wall component and slide along the wall instead.
    near_threat = any(d < CONFIG["SPLIT_REACH"] for _, d in info["threats"])
    if near_threat:
        wm = CONFIG["WALL_MARGIN"] * CONFIG["WALL_ESC_MARGIN_MULT"]
        if cx < wm and fx < 0:
            fy += math.copysign(abs(fx), fy if abs(fy) > EPS else 1.0)
            fx = CONFIG["WALL_ESC_NUDGE"]  # gentle outward nudge
        elif ARENA_SIZE - cx < wm and fx > 0:
            fy += math.copysign(abs(fx), fy if abs(fy) > EPS else 1.0)
            fx = -CONFIG["WALL_ESC_NUDGE"]
        if cy < wm and fy < 0:
            fx += math.copysign(abs(fy), fx if abs(fx) > EPS else 1.0)
            fy = CONFIG["WALL_ESC_NUDGE"]
        elif ARENA_SIZE - cy < wm and fy > 0:
            fx += math.copysign(abs(fy), fx if abs(fx) > EPS else 1.0)
            fy = -CONFIG["WALL_ESC_NUDGE"]

    # ORGAN map positioning: center (+) or edge (-) preference
    if CONFIG["W_CENTER"] != 0:
        ux, uy, d = unit(ARENA_SIZE / 2 - cx, ARENA_SIZE / 2 - cy)
        fx += ux * CONFIG["W_CENTER"] * d / ARENA_SIZE
        fy += uy * CONFIG["W_CENTER"] * d / ARENA_SIZE

    # ORGAN idle merge drive: fragmented with no virus work -> pull together
    if CONFIG["W_MERGE_IDLE"] > 0 and len(my_blobs) > 1 and not st.visible_viruses:
        gx = sum(b.pos[0] * mass(b.radius) for b in my_blobs) / total_mass
        gy = sum(b.pos[1] * mass(b.radius) for b in my_blobs) / total_mass
        ux, uy, d = unit(gx - cx, gy - cy)
        fx += ux * CONFIG["W_MERGE_IDLE"] * d
        fy += uy * CONFIG["W_MERGE_IDLE"] * d

    # ORGAN piece guard: just shattered -> regroup surge (heal the loss30 wound)
    if (CONFIG["W_PIECE_GUARD"] > 0 and tracker.shatter_clock < CONFIG["PIECE_GUARD_TICKS"]
            and len(my_blobs) > 1):
        gx = sum(b.pos[0] * mass(b.radius) for b in my_blobs) / total_mass
        gy = sum(b.pos[1] * mass(b.radius) for b in my_blobs) / total_mass
        ux, uy, d = unit(gx - cx, gy - cy)
        fx += ux * CONFIG["W_PIECE_GUARD"] * d
        fy += uy * CONFIG["W_PIECE_GUARD"] * d

    # ORGAN stall kick: pinned/deadlocked -> perpendicular kick to break sieges
    _camping_now = (CONFIG["W_CAMP"] > 0 and total_mass < CONFIG["CAMP_MAX_MASS"] and any(
        CONFIG["CAMP_WINDOW_LO"] <= tracker.tick - c[2] <= CONFIG["CAMP_WINDOW_HI"] and
        (c[0]-cx)**2 + (c[1]-cy)**2 < 25.0 for c in tracker.camp_sites))
    if CONFIG["STALL_KICK_ON"] > 0.5 and not _camping_now:
        ax, ay = tracker._stall_anchor
        if math.hypot(cx - ax, cy - ay) > CONFIG["STALL_DIST"]:
            tracker._stall_anchor = (cx, cy)
            tracker._stall_since = tracker.tick
        elif tracker.tick - tracker._stall_since > CONFIG["STALL_TICKS"]:
            fmag = math.hypot(fx, fy) + EPS
            fx, fy = fx + (-fy / fmag) * CONFIG["W_STALL_KICK"], fy + (fx / fmag) * CONFIG["W_STALL_KICK"]

    # --- regroup our own blobs under threat ---
    if len(my_blobs) > 1 and info["threats"]:
        gx = sum(b.pos[0] * mass(b.radius) for b in my_blobs) / total_mass
        gy = sum(b.pos[1] * mass(b.radius) for b in my_blobs) / total_mass
        ux, uy, d = unit(gx - cx, gy - cy)
        fx += ux * CONFIG["W_REGROUP"] * d
        fy += uy * CONFIG["W_REGROUP"] * d

    return fx, fy, info



# ----------------------------------------------------------------------------
# 3b. ARCH-EVO strategic mixer graph.
# ----------------------------------------------------------------------------


# ============ ELITE-TALLY MODE SWITCH (Chris's design, 2026-07-16 rev) ============
# Five parameter modes (0E/1E/2E/3E + finals 7E) bundled in one bot. In the GYM
# these overlays are EMPTY -> switching is a no-op and behavior is bit-exact.
# At SHIP time the bundler populates MODE_OVERLAYS with hand-picked models
# (gene diffs vs the base CONFIG) and ELITE_TEAM_IDS with the live top teams.
# In-game: every identified elite (by team_id, once each) increments the tally;
# mode escalates 1E -> 2E (tally 2) -> 3E (tally>=3). Escalate-only upward.
# TIME GATE: after the official competition ends (end of Jul 19 Sydney =
# 2026-07-19T14:00:00Z) the bot HARDCODES 7E mode — finals room is 7 elites.
MODE_OVERLAYS = {0: {}, 1: {}, 2: {}, 3: {}, 7: {}}
# Chris 2026-07-16: DEFAULT IS 1E (89% of live rooms have >=1 elite). Drop to
# 0E only once the room is IDENTIFIED as elite-free: no elite sighted by tick
# _MODE_0E_COMMIT. A later sighting still escalates out of 0E permanently.
ELITE_TEAM_IDS = ()          # empty in gym -> tally code never runs
_MODE_CUTOVER_UTC = "2026-07-19T14:00:00"
_MODE_0E_COMMIT = 150
_BASE_CONFIG = dict(CONFIG)
_SEEN_ELITES = set()
_MODE = [1]
_MODE_TICKS = [0]

def _mode_for(tally):
    return 3 if tally >= 3 else 2 if tally == 2 else 1

def _apply_mode(m):
    if m == _MODE[0]:
        return
    _MODE[0] = m
    CONFIG.clear()
    CONFIG.update(_BASE_CONFIG)
    CONFIG.update(MODE_OVERLAYS.get(m, {}))
    try:
        print(f"[mode] tick {_MODE_TICKS[0]}: switched to {m}E "
              f"(elites seen: {len(_SEEN_ELITES)})", flush=True)
    except Exception:
        pass

try:
    from datetime import datetime as _md, timezone as _mtz
    _FORCE_7E = _md.now(_mtz.utc).strftime("%Y-%m-%dT%H:%M:%S") >= _MODE_CUTOVER_UTC
except Exception:
    _FORCE_7E = False

# Boot line (once per match, ship only — silent in gym where overlays/ids are
# empty): current UTC time, whether the 7E final mode is on, and time until it is.
if ELITE_TEAM_IDS or MODE_OVERLAYS[7]:
    try:
        _now = _md.now(_mtz.utc)
        _cut = _md.strptime(_MODE_CUTOVER_UTC, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=_mtz.utc)
        _left = (_cut - _now).total_seconds()
        _eta = "ON" if _left <= 0 else f"armed, on in {int(_left // 3600)}h{int(_left % 3600 // 60):02d}m"
        print(f"[boot] {_now.strftime('%Y-%m-%d %H:%M:%S')}Z | final mode 7E: {_eta} "
              f"| cutover {_MODE_CUTOVER_UTC}Z", flush=True)
    except Exception:
        pass
if _FORCE_7E and (MODE_OVERLAYS[7] or ELITE_TEAM_IDS):
    _apply_mode(7)

def _mode_tick(visible_blobs):
    """Per-tick elite tally + mode selection (Chris 2026-07-16 final design):
    START in 1E. Tally 2 -> 2E, tally>=3 -> 3E, escalate-only. Drop to 0E only
    when the room is identified elite-free: zero sightings for the first
    _MODE_0E_COMMIT ticks. 0E is abandoned permanently on first contact.
    No-op when ELITE_TEAM_IDS is empty (gym) or after cutover (pinned 7E)."""
    if not ELITE_TEAM_IDS or _FORCE_7E:
        return
    try:
        _MODE_TICKS[0] += 1
        _before = len(_SEEN_ELITES)
        for _b in visible_blobs:
            _t = getattr(_b, "team_id", None)
            if _t in ELITE_TEAM_IDS:
                _SEEN_ELITES.add(_t)
        if len(_SEEN_ELITES) > _before:
            try:
                print(f"[mode] tick {_MODE_TICKS[0]}: identified elites "
                      f"{sorted(_SEEN_ELITES)} (tally {len(_SEEN_ELITES)})", flush=True)
            except Exception:
                pass
        if _SEEN_ELITES:
            _apply_mode(_mode_for(len(_SEEN_ELITES)))
        elif _MODE_TICKS[0] >= _MODE_0E_COMMIT and _MODE[0] == 1:
            _apply_mode(0)
    except Exception:
        pass
# ============ end MODE SWITCH ============

# ============ LOOKAHEAD VETO GATE (2026-07-15) — inlined, engine-faithful ============
# Simulates split-half trajectories (parent + ballistic child) a few ticks ahead to
# VETO unsafe splits the reactive force field cannot see. Dead code unless
# CONFIG["LOOKAHEAD_ON"] > 0.5, so bit-exact-neutral when off.
_LA_BASE_SPEED = 1.1; _LA_SPD_FACTOR = 0.08; _LA_MIN_SPEED = 0.25
_LA_SPLIT_MIN_MASS = 2.0; _LA_EJECT = 1.6; _LA_DRAG = 0.82; _LA_EAT = 1.2
_LA_VIRUS_POP = (1.5 ** 2) * 1.2  # 2.7: half-mass must exceed this to pop

def _la_speed(r):
    return max(_LA_MIN_SPEED, _LA_BASE_SPEED / (1.0 + r * _LA_SPD_FACTOR))

def _la_unit(dx, dy):
    d = math.hypot(dx, dy)
    return (dx / d, dy / d) if d > 1e-9 else (0.0, 0.0)

def _la_step(x, y, vx, vy, r, sx, sy):
    sp = _la_speed(r)
    x += sx * sp + vx; y += sy * sp + vy
    vx *= _LA_DRAG; vy *= _LA_DRAG
    if abs(vx) < 1e-4: vx = 0.0
    if abs(vy) < 1e-4: vy = 0.0
    return min(60.0, max(0.0, x)), min(60.0, max(0.0, y)), vx, vy

def _la_hits_virus(x, y, r, vx, vy, sx, sy, viruses, horizon):
    for _ in range(horizon):
        for (vx0, vy0) in viruses:
            if (x - vx0) ** 2 + (y - vy0) ** 2 <= r * r:
                return True
        x, y, vx, vy = _la_step(x, y, vx, vy, r, sx, sy)
    return False

def _la_virus_veto(my_blobs, sx, sy, viruses, horizon):
    if not viruses: return False
    for (bx, by, m) in my_blobs:
        if m < _LA_SPLIT_MIN_MASS: continue
        half = m / 2.0
        if half <= _LA_VIRUS_POP: continue
        hr = math.sqrt(half)
        if _la_hits_virus(bx, by, hr, 0.0, 0.0, sx, sy, viruses, horizon): return True
        cx = bx + sx * (hr + hr); cy = by + sy * (hr + hr)
        if _la_hits_virus(cx, cy, hr, sx * _LA_EJECT, sy * _LA_EJECT, sx, sy, viruses, horizon): return True
    return False

def _la_miss_veto(my_blobs, sx, sy, threats, horizon):
    if not threats: return False
    for (bx, by, m) in my_blobs:
        if m < _LA_SPLIT_MIN_MASS: continue
        cm = m / 2.0; cr = math.sqrt(cm)
        cx = bx + sx * (cr + cr); cy = by + sy * (cr + cr)
        evx = sx * _LA_EJECT; evy = sy * _LA_EJECT
        for (tx, ty, tm) in threats:
            if tm <= cm * _LA_EAT: continue
            hx, hy, hvx, hvy = cx, cy, evx, evy; ex, ey = tx, ty
            tr = math.sqrt(tm); ts = _la_speed(tr)
            for _ in range(horizon):
                ux, uy = _la_unit(hx - ex, hy - ey)
                ex += ux * ts; ey += uy * ts
                hx, hy, hvx, hvy = _la_step(hx, hy, hvx, hvy, cr, sx, sy)
                if (hx - ex) ** 2 + (hy - ey) ** 2 <= (tr + cr) ** 2: return True
    return False

def _la_attack_lands(bx, by, m, target, sx, sy, horizon):
    tx, ty, tm = target
    cm = m / 2.0
    if cm <= tm * _LA_EAT: return False
    cr = math.sqrt(cm)
    cx = bx + sx * (cr + cr); cy = by + sy * (cr + cr)
    vx = sx * _LA_EJECT; vy = sy * _LA_EJECT
    tr = math.sqrt(tm); ts = _la_speed(tr)
    for _ in range(horizon):
        fx, fy = _la_unit(tx - bx, ty - by)
        tx += fx * ts; ty += fy * ts
        cx, cy, vx, vy = _la_step(cx, cy, vx, vy, cr, sx, sy)
        if (cx - tx) ** 2 + (cy - ty) ** 2 <= (cr + tr) ** 2: return True
    return False

def _la_gate_split(fx, fy, my_blobs, viruses, threats, target):
    """Returns False if the proposed split should be vetoed. CONFIG-driven sub-toggles."""
    sx, sy = _la_unit(fx, fy)
    if sx == 0.0 and sy == 0.0: return True
    h = int(round(CONFIG.get("LA_HORIZON", 5.0)))
    if CONFIG.get("LA_VIRUS", 1.0) > 0.5 and _la_virus_veto(my_blobs, sx, sy, viruses, h): return False
    if CONFIG.get("LA_MISS", 1.0) > 0.5 and _la_miss_veto(my_blobs, sx, sy, threats, h): return False
    if CONFIG.get("LA_ATTACK", 1.0) > 0.5 and target is not None and my_blobs:
        bx, by, m = my_blobs[0]
        if not _la_attack_lands(bx, by, m, target, sx, sy, h): return False
    return True
# ============ end LOOKAHEAD ============

def _clip(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _sigmoid(v: float) -> float:
    v = max(-20.0, min(20.0, v))
    return 2.0 / (1.0 + math.exp(-v)) - 1.0


def _arch_op(op: int, a: float, b: float, k: float, bias: float) -> float:
    if op == 0:
        z = a
    elif op == 1:
        z = a + b
    elif op == 2:
        z = a - b
    elif op == 3:
        z = a * b
    elif op == 4:
        z = max(a, b)
    elif op == 5:
        z = min(a, b)
    elif op == 6:
        z = _sigmoid(k * a + bias)
    elif op == 7:
        z = 1.0 if a > b else -1.0
    elif op == 8:
        z = abs(a - b)
    elif op == 9:
        z = a / (abs(b) + 0.1)
    elif op == 10:
        z = 1.0 - a
    else:
        z = a
    return _clip(z)


def _nearest_direction(cx: float, cy: float, objects, away: bool = False):
    if not objects:
        return 0.0, 0.0
    obj, _d = min(objects, key=lambda t: t[1])
    dx, dy = obj.pos[0] - cx, obj.pos[1] - cy
    if away:
        dx, dy = -dx, -dy
    ux, uy, _ = unit(dx, dy)
    return ux, uy


def _nearest_plain_direction(cx: float, cy: float, objects):
    if not objects:
        return 0.0, 0.0
    obj = min(objects, key=lambda q: (q.pos[0] - cx) ** 2 + (q.pos[1] - cy) ** 2)
    return unit(obj.pos[0] - cx, obj.pos[1] - cy)[:2]


def _positive_weight(logit: float) -> float:
    """Stable positive channel weight. Range is broad enough to suppress or dominate."""
    return math.exp(max(-4.0, min(4.0, logit)))


def apply_architecture(game: Game, tracker: Tracker, info: dict,
                       fx: float, fy: float) -> tuple[float, float, float, float]:
    """Evaluate the 11-slot graph as a strategic steering mixer.

    The mature controller still computes geometry, tracking and tactical primitives.
    The graph decides how strongly food, prey, escape, virus, centre and the full
    incumbent vector should steer the bot on this tick. ARCH_AUTHORITY determines
    the graph's share of final direction and is prevented from falling below the
    architecture experiment's minimum. It also emits guarded ordinary/cycle split
    votes. Hard legality and lethal-range vetoes remain outside the graph.
    """
    if CONFIG["ARCH_ON"] <= 0.5:
        return fx, fy, 0.0, 0.0

    st = game.state
    me = st.me
    blobs = list(me.blobs.values())
    total = sum(mass(b.radius) for b in blobs) or mass(me.radius)
    cx, cy = me.x, me.y
    tick_frac = _clip(tracker.tick / max(CONFIG["EXPECTED_ROUNDS"], 1.0), 0.0, 1.0)

    threat_pressure = max((max(0.0, 1.0 - d / 20.0) for _t, d in info["threats"]), default=0.0)
    prey_opportunity = max((max(0.0, 1.0 - d / 20.0) * min(1.0, mass(p.radius) / 20.0)
                            for p, d in info["prey"]), default=0.0)
    virus_visible = 1.0 if st.visible_viruses else 0.0
    food_visible = 1.0 if st.visible_food else 0.0
    edge_dist = min(cx, cy, ARENA_SIZE - cx, ARENA_SIZE - cy)
    edge_pressure = max(0.0, 1.0 - edge_dist / 12.0)
    wealth = _clip((total - CONFIG["WEALTH_START"]) / 50.0, 0.0, 1.0)
    fragmented = _clip((len(blobs) - 1) / 15.0, 0.0, 1.0)
    base_mag_raw = math.hypot(fx, fy)
    base_mag = _clip(base_mag_raw / 20.0, 0.0, 1.0)
    feast_ready = 1.0 if (st.visible_viruses and total >= CONFIG["FEAST_MIN_MASS"]) else 0.0
    late_phase = 1.0 if tick_frac >= CONFIG["ENDGAME_START"] else 0.0
    vis_mass = {}
    for b in st.visible_blobs:
        vis_mass[b.player_id] = vis_mass.get(b.player_id, 0.0) + mass(b.radius)
    rank_lead = 1.0 if total >= max(vis_mass.values(), default=0.0) else 0.0

    values = [
        1.0, tick_frac, _clip(total / 80.0, 0, 1), wealth,
        _clip(len(blobs) / 16.0, 0, 1), threat_pressure, prey_opportunity,
        virus_visible, edge_pressure, fragmented, rank_lead, base_mag,
        1.0 if threat_pressure > 0.35 else 0.0, late_phase, feast_ready,
        _clip((1.0 - threat_pressure) * prey_opportunity, 0, 1),
    ]
    # ===== ENGINE-AUDIT SENSORS (2026-07-12): channels no other bot likely reads =====
    # 16: TRUE GLOBAL RANK (rankings = player ids by size, desc — beyond vision)
    try:
        _rk = st.rankings.index(me.player_id) / 7.0
    except (ValueError, AttributeError):
        _rk = 0.5
    values.append(_clip(_rk, 0, 1))
    # 17: VULNERABLE-PREY WINDOW (enemy merge_cooldown = defenseless-piece clock)
    _vuln = 0.0
    _half_m = mass(max((b.radius for b in blobs), default=me.radius)) / 2.0
    for _b in st.visible_blobs:
        if _b.player_id == me.player_id: continue
        if getattr(_b, "merge_cooldown", 0) > 10 and _half_m >= mass(_b.radius) * 1.2:
            _d = math.hypot(_b.pos[0] - cx, _b.pos[1] - cy)
            if _d < 15.0:
                _vuln = max(_vuln, min(1.0, _b.merge_cooldown / 60.0) * (1.0 - _d / 15.0))
    values.append(_vuln)
    # 18: KILL PULSE (partial global kill feed -> local danger tempo, EMA)
    _new = st.event_history[st.new_events:] if hasattr(st, "event_history") else []
    _kills = sum(1 for _e in _new if getattr(_e, "event_type", "") in ("event_player_eaten", "public_event_player_eaten"))
    tracker._kill_ema = 0.9 * getattr(tracker, "_kill_ema", 0.0) + 0.1 * min(1.0, _kills / 3.0)
    values.append(_clip(tracker._kill_ema, 0, 1))
    # ===== ARCH v3 DEFENSE SENSORS =====
    _ntd = min((d for _t, d in info["threats"]), default=99.0)
    values.append(max(0.0, 1.0 - _ntd / 25.0))                 # 19 threat proximity
    _big = max((v for k, v in vis_mass.items() if k != me.player_id), default=0.0)
    values.append(_clip(_big / (max(total, EPS) * 3.0), 0.0, 1.0))  # 20 dominance
    _oc = {}
    for _b in st.visible_blobs:
        if _b.player_id != me.player_id:
            _oc[_b.player_id] = _oc.get(_b.player_id, 0) + 1
    values.append(_clip((max(_oc.values(), default=1) - 1) / 15.0, 0.0, 1.0))  # 21 opp frag

    food_dir = _nearest_plain_direction(cx, cy, st.visible_food)
    prey_dir = _nearest_direction(cx, cy, info["prey"], away=False)
    escape_dir = _nearest_direction(cx, cy, info["threats"], away=True)
    virus_dir = _nearest_plain_direction(cx, cy, st.visible_viruses)
    center_dir = unit(ARENA_SIZE / 2 - cx, ARENA_SIZE / 2 - cy)[:2]
    incumbent_dir = (fx / base_mag_raw, fy / base_mag_raw) if base_mag_raw > EPS else (0.0, 0.0)

    logits = {
        1: CONFIG["ARCH_BASE_FOOD"],
        2: CONFIG["ARCH_BASE_PREY"],
        3: CONFIG["ARCH_BASE_ESCAPE"],
        4: CONFIG["ARCH_BASE_VIRUS"],
        5: CONFIG["ARCH_BASE_CENTER"],
        6: CONFIG["ARCH_BASE_INCUMBENT"],
    }
    ordinary_split_vote = 0.0
    cycle_split_vote = 0.0
    active_used = 0
    active_cap = max(0, min(16, int(round(CONFIG.get("ARCH_MAX_ACTIVE", 8.0)))))

    dial_acc = {9: 0.0, 10: 0.0, 11: 0.0, 12: 0.0, 13: 0.0}
    for i in range(16):
        enabled = CONFIG[f"ARCH_N{i}_ON"] > 0.5 and active_used < active_cap
        if not enabled:
            values.append(0.0)
            continue
        active_used += 1
        max_input = 21 + i  # base 0..21 (defense sensors 19-21) plus previous node outputs
        a_idx = max(0, min(max_input, int(round(CONFIG[f"ARCH_N{i}_A"]))))
        b_idx = max(0, min(max_input, int(round(CONFIG[f"ARCH_N{i}_B"]))))
        a, b = values[a_idx], values[b_idx]
        out = _arch_op(int(round(CONFIG[f"ARCH_N{i}_OP"])), a, b,
                       CONFIG[f"ARCH_N{i}_K"], CONFIG[f"ARCH_N{i}_BIAS"])
        values.append(out)
        target = int(round(CONFIG[f"ARCH_N{i}_TARGET"]))
        amount = CONFIG[f"ARCH_N{i}_GAIN"] * out
        if target in logits:
            logits[target] += amount
        elif target == 7:
            ordinary_split_vote += amount
        elif target == 8:
            cycle_split_vote += amount
        elif target in dial_acc:
            dial_acc[target] += amount

    # ARCH v3: publish dials (force phase reads NEXT tick; gates read SAME tick)
    tracker.dials["threat"] = dial_acc[9]
    tracker.dials["feast"] = dial_acc[10]
    tracker.dials["cycle_gate"] = dial_acc[11]
    tracker.dials["vuln_margin"] = dial_acc[12]
    tracker.dials["prey"] = dial_acc[13]

    channels = (
        (_positive_weight(logits[1]) * food_visible, food_dir),
        (_positive_weight(logits[2]), prey_dir),
        (_positive_weight(logits[3]), escape_dir),
        (_positive_weight(logits[4]) * virus_visible, virus_dir),
        (_positive_weight(logits[5]), center_dir),
        (_positive_weight(logits[6]), incumbent_dir),
    )
    graph_x = sum(w * d[0] for w, d in channels)
    graph_y = sum(w * d[1] for w, d in channels)
    graph_mag = math.hypot(graph_x, graph_y)
    if graph_mag > EPS:
        graph_x /= graph_mag
        graph_y /= graph_mag
    else:
        graph_x, graph_y = incumbent_dir

    authority = max(CONFIG["ARCH_MIN_AUTHORITY"], min(1.0, CONFIG["ARCH_AUTHORITY"]))
    old_x, old_y = incumbent_dir
    final_x = (1.0 - authority) * old_x + authority * graph_x
    final_y = (1.0 - authority) * old_y + authority * graph_y
    final_mag = math.hypot(final_x, final_y)
    if final_mag > EPS:
        # Direction is the meaningful action; preserve a healthy nonzero magnitude.
        final_x /= final_mag
        final_y /= final_mag
    return final_x, final_y, ordinary_split_vote, cycle_split_vote



# ----------------------------------------------------------------------------
# VULN ORGAN v2 — target selector, pursuit lock, safety evaluator, atomic
# direction-plus-split executor. Never a scalar into the mixer.
# ----------------------------------------------------------------------------
SPLIT_TRAVEL = 8.9   # engine: launched half travel distance (same constant as kill_envelope)

def _vuln_corner_uncatchable(t, half_r):
    """Reuse corner-fix geometry: catchable iff our half, tucked at (r, r), reaches the
    target center (eat = center-dist <= eater radius, centers clamped >= r from walls)."""
    wdx = min(t.pos[0], ARENA_SIZE - t.pos[0]); wdy = min(t.pos[1], ARENA_SIZE - t.pos[1])
    if wdx < CONFIG["CORNER_TUCK"] and wdy < CONFIG["CORNER_TUCK"]:
        return math.hypot(max(half_r - wdx, 0.0), max(half_r - wdy, 0.0)) > half_r - CONFIG["CORNER_MARGIN"]
    return False

def find_vulnerable_opportunity(game, tracker, info):
    if CONFIG["VULN_ON"] <= 0.5:
        return None
    st = game.state; me = st.me
    my_blobs = list(me.blobs.values())
    if len(my_blobs) > CONFIG["VULN_MAX_BLOBS"]:
        return None                                       # v1: whole-bot commits only
    total_mass = sum(mass(b.radius) for b in my_blobs) or mass(me.radius)
    if total_mass > CONFIG["VULN_MAX_BANK_RISK"]:
        return None                                       # wealthy: bank > snack
    cx, cy = me.x, me.y

    # ---- enemy blobs grouped by owner (for retaliation checks) ----
    by_owner = {}
    for b in st.visible_blobs:
        if b.player_id != me.player_id:
            by_owner.setdefault(b.player_id, []).append(b)

    best = None
    for own in my_blobs:                                  # explicit attacker blob
        own_m = mass(own.radius)
        if own_m < 2 * CONFIG["SPLIT_MIN_MASS"]:
            continue
        half_m = own_m / 2.0
        half_r = own.radius / math.sqrt(2)
        commit_range = SPLIT_TRAVEL + half_r - CONFIG["VULN_COMMIT_MARGIN"]
        for owner, blobs in by_owner.items():
            for t in blobs:
                t_m = mass(t.radius)
                if t_m < CONFIG["VULN_MIN_TARGET_MASS"]:
                    continue
                cd = getattr(t, "merge_cooldown", 0)
                if cd <= CONFIG["VULN_MIN_COOLDOWN"]:
                    continue
                # offensive validity with margin above the bare 1.2
                _vm = CONFIG["VULN_EAT_MARGIN"]
                _dv = tracker.dials["vuln_margin"]
                if _dv != 0.0:
                    _vm *= math.exp(_clip(_dv, -1.0, 1.0))   # ARCH v3 VULN-margin dial
                if half_m < t_m * CONFIG["EAT_RATIO"] * _vm:
                    continue
                dx, dy = t.pos[0] - own.pos[0], t.pos[1] - own.pos[1]
                d = math.hypot(dx, dy)
                if d < EPS or d > CONFIG["VULN_DETECT_RANGE"]:
                    continue
                _cexp = tracker.corner_veto.get(t.player_id)
                if _cexp is not None and tracker.tick < _cexp:
                    _twdx = min(t.pos[0], ARENA_SIZE - t.pos[0])
                    _twdy = min(t.pos[1], ARENA_SIZE - t.pos[1])
                    if (_twdx < 2.0 * CONFIG["CORNER_TUCK"]
                            and _twdy < 2.0 * CONFIG["CORNER_TUCK"]):
                        continue                          # zone-scoped sticky blacklist
                if _vuln_corner_uncatchable(t, half_r):
                    tracker.corner_veto[t.player_id] = tracker.tick + int(CONFIG["CORNER_VETO_TICKS"])
                    continue
                # ---- score: value x margin x reach x cooldown (safety is a VETO, not a factor)
                target_value = min(1.0, t_m / 10.0)
                eat_margin = half_m / (CONFIG["EAT_RATIO"] * t_m)
                margin_q = max(0.0, min(1.0, (eat_margin - 1.0) / 0.35))
                reach_q = max(0.0, min(1.0, (CONFIG["VULN_DETECT_RANGE"] - d) / CONFIG["VULN_DETECT_RANGE"]))
                cool_q = max(0.0, min(1.0, (cd - CONFIG["VULN_MIN_COOLDOWN"]) / 40.0))
                score = target_value * margin_q * reach_q * cool_q
                if score <= 0.0:
                    continue
                # ---- HARD SAFETY VETOES (all enemies, incl. target-owner retaliation
                #      and third-party interception: anything able to eat our HALF) ----
                unsafe = False
                for ob in st.visible_blobs:
                    if ob.player_id == me.player_id: continue
                    if ob.player_id == owner and ob.blob_id == t.blob_id: continue
                    if mass(ob.radius) >= half_m * CONFIG["EAT_RATIO"]:
                        od = math.hypot(ob.pos[0] - own.pos[0], ob.pos[1] - own.pos[1])
                        td = math.hypot(ob.pos[0] - t.pos[0], ob.pos[1] - t.pos[1])
                        if min(od, td) < CONFIG["VULN_THREAT_CLEAR"]:
                            unsafe = True; break
                if unsafe:
                    continue
                cand = {"key": (owner, t.blob_id), "owner": owner,
                        "direction": (dx / d, dy / d), "distance": d,
                        "target_mass": t_m, "cooldown": cd, "score": score,
                        "commit_ready": d <= commit_range,
                        "attacker_blob": own.blob_id}
                if best is None or cand["score"] > best["score"]:
                    best = cand

    # ---- short pursuit lock: no jitter, no mid-lunge retargeting ----
    if best is not None:
        tracker.vuln_stats["detect"] += 1
        if tracker.vuln_target_key is not None and tracker.vuln_lock_left > 0 \
                and best["key"] != tracker.vuln_target_key:
            # keep the locked target unless the new one is materially (25%) better
            locked = None
            for owner, blobs in by_owner.items():
                for t in blobs:
                    if (owner, t.blob_id) == tracker.vuln_target_key:
                        locked = t; break
            if locked is not None and best["score"] < tracker.vuln_last_score * 1.25:
                dx, dy = locked.pos[0] - cx, locked.pos[1] - cy
                d = math.hypot(dx, dy)
                if d > EPS and d <= CONFIG["VULN_DETECT_RANGE"]:
                    tracker.vuln_lock_left -= 1
                    return {"key": tracker.vuln_target_key, "owner": tracker.vuln_target_key[0],
                            "direction": (dx / d, dy / d), "distance": d,
                            "target_mass": mass(locked.radius),
                            "cooldown": getattr(locked, "merge_cooldown", 0),
                            "score": tracker.vuln_last_score,
                            "commit_ready": d <= SPLIT_TRAVEL + (max(b.radius for b in me.blobs.values()) / math.sqrt(2)) - CONFIG["VULN_COMMIT_MARGIN"],
                            "attacker_blob": None}
            else:
                tracker.vuln_stats["switch"] += 1
        tracker.vuln_target_key = best["key"]
        tracker.vuln_last_score = best["score"]
        tracker.vuln_lock_left = int(CONFIG["VULN_LOCK_TICKS"])
    else:
        tracker.vuln_lock_left = max(0, tracker.vuln_lock_left - 1)
        if tracker.vuln_lock_left == 0:
            tracker.vuln_target_key = None
    return best

def architecture_safe_split(game: Game, info: dict) -> bool:
    """Hard safety shell around graph-generated ordinary or cycle split requests."""
    if not CONFIG["SPLIT_ENABLED"]:
        return False
    me = game.state.me
    blobs = list(me.blobs.values())
    if len(blobs) >= 16:
        return False
    total = sum(mass(b.radius) for b in blobs) or mass(me.radius)
    largest = max((b.radius for b in blobs), default=me.radius)
    if mass(largest) < 2.0 * CONFIG["SPLIT_MIN_MASS"]:
        return False
    if total > CONFIG["SPLIT_MAX_MASS"]:
        return False
    if any(d < CONFIG["ARCH_SPLIT_THREAT_CLEAR"] for _t, d in info["threats"]):
        return False
    return bool(info["prey"] or game.state.visible_viruses)

# ----------------------------------------------------------------------------
# 4. Split decision.
# ----------------------------------------------------------------------------
def should_split(game: Game, info: dict, fx: float, fy: float) -> bool:
    if not CONFIG["SPLIT_ENABLED"]:
        return False
    me = game.state.me
    my_blobs = list(me.blobs.values())
    if len(my_blobs) >= CONFIG["SPLIT_MAX_BLOBS"]:
        return False
    largest = max((b.radius for b in my_blobs), default=me.radius)
    if mass(largest) < CONFIG["SPLIT_MIN_MASS"] * 2:  # keep halves viable
        return False
    # BANK PROTECTION: when big, a lunge risks the whole score for a snack.
    if sum(mass(b.radius) for b in my_blobs) > CONFIG["SPLIT_MAX_MASS"]:
        return False
    # any threat too close -> never fragment
    for _, d in info["threats"]:
        if d < CONFIG["SPLIT_THREAT_CLEARANCE"]:
            return False
    # a half has radius largest/sqrt(2); require comfortable margin over prey
    half_r = largest / math.sqrt(2)
    for prey, d in info["prey"]:
        if d <= CONFIG["SPLIT_MAX_RANGE"] and half_r >= prey.radius * CONFIG["SPLIT_SAFETY_RATIO"]:
            # only lunge if we're actually moving toward it
            ux, uy, _ = unit(prey.pos[0] - me.x, prey.pos[1] - me.y)
            fmag = math.hypot(fx, fy)
            if fmag > EPS and (fx * ux + fy * uy) / fmag > CONFIG["SPLIT_ALIGN_MIN"]:
                return True
    return False


def should_cycle_split(game: Game, info: dict, tracker=None) -> bool:
    """SPLIT-FEAST CYCLE ORGAN. Reproduce Team-15's virus economy (matches
    1719/1721/1723): split toward 16 blobs in a safe feast posture so virus
    consumptions land at high blob count (pieces=1 -> +2.25 free mass, no
    fragmentation). Vetoable via SPLIT_CYCLE_ON; regroups (stops splitting) when
    viruses exhaust or a threat enters CYCLE_THREAT_CLEAR."""
    if CONFIG["SPLIT_CYCLE_ON"] <= 0.5:
        return False
    st = game.state
    if not st.visible_viruses:
        return False  # viruses exhausted -> don't fragment; let blobs merge
    me = st.me
    my_blobs = list(me.blobs.values())
    if len(my_blobs) >= CONFIG["CYCLE_TARGET_BLOBS"]:
        return False  # slots saturated -> vacuum (feast force), don't split further
    total_m = sum(mass(b.radius) for b in my_blobs) or mass(me.radius)
    if total_m < CONFIG["CYCLE_MIN_MASS"]:
        return False  # too small: halves not viable / not worth spreading
    largest = max((b.radius for b in my_blobs), default=me.radius)
    if mass(largest) < CONFIG["SPLIT_MIN_MASS"] * 2:
        return False  # keep each half above the engine split-min (mass 2.0)
    _clear = CONFIG["CYCLE_THREAT_CLEAR"]
    if tracker is not None:
        _dc = tracker.dials["cycle_gate"]
        if _dc != 0.0:
            _clear *= math.exp(_clip(_dc, -1.5, 1.5))   # ARCH v3 cycle-gate dial
    for _t, d in info["threats"]:
        if d < _clear:
            return False  # threat in clearance -> veto cycle, regroup instead
    return True


# ----------------------------------------------------------------------------
# Main loop.
# ----------------------------------------------------------------------------
import atexit as _vuln_atexit, json as _vuln_json
def _vuln_dump(tr):
    try:
        with open("/tmp/vuln_organ_stats.jsonl", "a") as f:
            f.write(_vuln_json.dumps(tr.vuln_stats) + "\n")
    except Exception:
        pass

def main() -> None:
    game = Game()
    tracker = Tracker()
    _vuln_atexit.register(_vuln_dump, tracker)

    while True:
        query: QueryType = game.get_next_query()

        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryMovePlayer():
                    # Repeated bot errors get us banned from the leaderboard:
                    # any exception in decision code falls back to a legal
                    # drift toward the arena centre instead of crashing.
                    try:
                        tracker.read_intents(game)
                        tracker.update(game.state.visible_blobs, game.state.me.player_id)
                        fx, fy, info = compute_forces(game, tracker)
                        me_ = game.state.me
                        my_blobs_ = list(me_.blobs.values())
                        my_small_ = min((b.radius for b in my_blobs_), default=me_.radius)
                        my_large_ = max((b.radius for b in my_blobs_), default=me_.radius)
                        total_m_ = sum(mass(b.radius) for b in my_blobs_) or mass(me_.radius)

                        # ---- COMMITMENT LATCH: one target, hunted to conclusion ----
                        if CONFIG["LOCK_ENABLED"]:
                            tgt = None
                            if HUNT.key is not None:
                                for p, _d in info["prey"]:
                                    if (p.player_id, p.blob_id) == HUNT.key:
                                        tgt = p
                                        break
                            if tgt is None or HUNT.ticks > CONFIG["LOCK_TICKS_MAX"]:
                                HUNT.key, HUNT.ticks, best = None, 0, 0.0
                                for p, _d in info["prey"]:
                                    val = mass(p.radius)
                                    if val < CONFIG["LOCK_MIN_VALUE"]:
                                        continue
                                    closing = blob_speed_of(my_large_) - blob_speed_of(p.radius)
                                    if closing <= 0.02:
                                        continue
                                    d = math.hypot(p.pos[0] - me_.x, p.pos[1] - me_.y)
                                    if d / max(closing, 0.05) > CONFIG["LOCK_ABANDON_T"] * 3:
                                        continue
                                    sc = val / (1.0 + d)
                                    if sc > best:
                                        best, tgt = sc, p
                                if tgt is not None:
                                    HUNT.key = (tgt.player_id, tgt.blob_id)
                            if tgt is not None:
                                threat_close = any(dd < CONFIG["LOCK_THREAT_BREAK"] for _t, dd in info["threats"])
                                closing = blob_speed_of(my_large_) - blob_speed_of(tgt.radius)
                                d = math.hypot(tgt.pos[0] - me_.x, tgt.pos[1] - me_.y)
                                if threat_close or closing <= 0.02 or d / max(closing, 0.05) > CONFIG["LOCK_ABANDON_T"]:
                                    HUNT.key = None
                                else:
                                    HUNT.ticks += 1
                                    ix, iy = tracker.predict(tgt, min(d / max(blob_speed_of(my_large_), 0.05), 12))
                                    ux, uy, _dd = unit(ix - me_.x, iy - me_.y)
                                    fx += ux * CONFIG["W_LOCK"]
                                    fy += uy * CONFIG["W_LOCK"]

                        # ---- CONSTITUTIONAL VETO: lethal directions cannot win ----
                        if CONFIG["VETO_ENABLED"] and total_m_ > CONFIG["VETO_SOFT_MASS"] and info["threats"]:
                            env = []
                            for t, _d in info["threats"]:
                                er = kill_envelope(t, my_small_, tracker)
                                if er > 0:
                                    px, py = tracker.predict(t, 4)
                                    env.append((px, py, er))
                            if env:
                                fux, fuy, fmag = unit(fx, fy)
                                if fmag > EPS:
                                    step = blob_speed_of(my_large_) * CONFIG["VETO_HORIZON"]
                                    def lethal(dx, dy):
                                        qx, qy = me_.x + dx * step, me_.y + dy * step
                                        q2x, q2y = me_.x + dx * step * 0.4, me_.y + dy * step * 0.4
                                        for px, py, er in env:
                                            if math.hypot(qx - px, qy - py) < er or math.hypot(q2x - px, q2y - py) < er:
                                                return True
                                        return False
                                    if lethal(fux, fuy):
                                        best_dir, best_dot = None, -2.0
                                        for dx, dy in VETO_DIRS:
                                            if lethal(dx, dy):
                                                continue
                                            dot = dx * fux + dy * fuy
                                            if dot > best_dot:
                                                best_dot, best_dir = dot, (dx, dy)
                                        if best_dir is not None:
                                            fx, fy = best_dir
                                        # all 16 lethal: keep original force (least-bad)

                        # ARCH-EVO strategic mixer: controls steering composition and
                        # casts separate guarded votes for ordinary and cycle splitting.
                        # DECIMATION REMOVED (2026-07-12): caching the full steering
                        # vector made the bot repeat last tick's direction on odd ticks —
                        # measured cost -19 mass/game (raw-vs-mimic paired A/B, n=24).
                        # The graph eval is 11 arithmetic nodes: negligible compute.
                        fx, fy, arch_split_bias, arch_cycle_bias = apply_architecture(
                            game, tracker, info, fx, fy)

                        ordinary_split = should_split(game, info, fx, fy)
                        cycle_split = should_cycle_split(game, info, tracker)
                        if arch_split_bias <= -CONFIG["ARCH_SPLIT_THRESHOLD"]:
                            ordinary_split = False
                        elif (arch_split_bias >= CONFIG["ARCH_SPLIT_THRESHOLD"]
                              and architecture_safe_split(game, info)):
                            ordinary_split = True
                        if arch_cycle_bias <= -CONFIG["ARCH_SPLIT_THRESHOLD"]:
                            cycle_split = False
                        elif (arch_cycle_bias >= CONFIG["ARCH_SPLIT_THRESHOLD"]
                              and architecture_safe_split(game, info)):
                            cycle_split = True
                        split = ordinary_split or cycle_split
                        # ===== VULN ORGAN v2: atomic direction+split commit =====
                        # After the mixer so it cannot be diluted; bypasses
                        # ARCH_SPLIT_THRESHOLD and the vote path entirely.
                        _v = find_vulnerable_opportunity(game, tracker, info)
                        if _v is not None:
                            if _v["commit_ready"]:
                                fx, fy = _v["direction"]
                                split = True
                                tracker.vuln_stats["commit"] += 1
                                tracker.vuln_commit = (tracker.tick, _v["key"][0], _v["key"][1])
                            else:
                                _w = CONFIG["VULN_APPROACH_WEIGHT"]
                                _m = math.hypot(fx, fy) or 1.0
                                fx = (1 - _w) * (fx / _m) + _w * _v["direction"][0]
                                fy = (1 - _w) * (fy / _m) + _w * _v["direction"][1]
                        # confirm kills: engine kill feed within 10 ticks of commit
                        if tracker.vuln_commit is not None:
                            _ct, _cp, _cb = tracker.vuln_commit
                            if tracker.tick - _ct <= 10:
                                try:
                                    for _e in game.state.event_history[game.state.new_events:]:
                                        if getattr(_e, "event_type", "") in ("event_player_eaten", "public_event_player_eaten") \
                                                and getattr(_e, "eater_player_id", -1) == game.state.me.player_id \
                                                and getattr(_e, "eaten_player_id", -1) == _cp:
                                            tracker.vuln_stats["kill10"] += 1
                                            tracker.vuln_commit = None
                                except Exception:
                                    pass
                            else:
                                tracker.vuln_commit = None
                        # SPLIT-RUN: exactly one closing killer, small bank, no
                        # bystanders to eat our pieces -> fire halves away at 1.6.
                        if CONFIG["SPLIT_RUN_ENABLED"] and not split:
                            me_ = game.state.me
                            tm = sum(mass(b.radius) for b in me_.blobs.values())
                            close = [(t, d) for t, d in info["threats"] if d < CONFIG["SPLIT_RUN_TRIGGER"]]
                            if (len(close) == 1 and len(info["threats"]) == 1
                                    and tm < CONFIG["SPLIT_RUN_MAX_MASS"]
                                    and mass(max((b.radius for b in me_.blobs.values()), default=me_.radius)) >= 2 * CONFIG["SPLIT_MIN_MASS"]
                                    and len(me_.blobs) <= 2):
                                t, d = close[0]
                                hx, hy = tracker.intent_dir.get(t.player_id, (0.0, 0.0))
                                ux, uy, dd = unit(me_.x - t.pos[0], me_.y - t.pos[1])
                                if dd > EPS and (hx * ux + hy * uy) > 0.6:  # it is coming AT us
                                    fx, fy = ux, uy   # dead away
                                    split = True      # halves launch at eject speed
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                        fx, fy, split = 0.0, 0.0, False
                    if abs(fx) < EPS and abs(fy) < EPS:
                        # no signal: drift toward arena centre (food-rich, wall-safe)
                        fx = ARENA_SIZE / 2 - game.state.me.x
                        fy = ARENA_SIZE / 2 - game.state.me.y
                        if abs(fx) < EPS and abs(fy) < EPS:
                            fx = 1.0
                    _mode_tick(game.state.visible_blobs)
                    if split and CONFIG["LOOKAHEAD_ON"] > 0.5:
                        try:
                            _mb = [(b.pos[0], b.pos[1], mass(b.radius)) for b in game.state.me.blobs.values()]
                            _vir = [(v.pos[0], v.pos[1]) for v in game.state.visible_viruses]
                            _thr = [(t.pos[0], t.pos[1], mass(t.radius)) for t, _d in info["threats"]]
                            _tgt = None
                            if info["prey"]:
                                _pp = min(info["prey"], key=lambda pd: pd[1])[0]
                                _tgt = (_pp.pos[0], _pp.pos[1], mass(_pp.radius))
                            if not _la_gate_split(fx, fy, _mb, _vir, _thr, _tgt):
                                split = False
                        except Exception:
                            pass  # safety layer must never crash the bot
                    return MovePlayer(
                        player_id=game.state.me.player_id,
                        direction=DirectionModel(x=fx, y=fy),
                        split=split,
                    )
            raise RuntimeError(f"Unsupported query type: {type(query)}")

        game.send_move(choose_move(query))


if __name__ == "__main__":
    main()
