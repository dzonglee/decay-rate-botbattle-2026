"""OMNI-2 BODY (2026-07-10) — omni_feaster + five organs for the previously-
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
    "W_FOOD": 0.7188,
    "W_PREY": 15.6015,
    "W_THREAT": 1.2691,
    "W_VIRUS_BIG": 141.807,
    "W_WALL": 0.0981,
    "W_REGROUP": 0,
    "FOOD_FALLOFF": 2.4002,
    "PREY_FALLOFF": 0.7647,
    "THREAT_FALLOFF": 0.0408,
    "THREAT_PANIC_DIST": 1.3707,
    "THREAT_PANIC_MULT": 0.0584,
    "THREAT_IGNORE_DIST": 18.5502,
    "SPLIT_REACH": 51.3259,
    "W_SPLIT_ZONE": 0.1877,
    "WALL_MARGIN": 0.0165,
    "FRESH_MASS": 1.4497,
    "FRESH_CAUTION": 0.0083,
    "VETO_ENABLED": False,
    "VETO_MARGIN": 0.0128,
    "VETO_HORIZON": 3.8834,
    "VETO_SOFT_MASS": 2.068,
    "LOCK_ENABLED": False,
    "LOCK_MIN_VALUE": 0.3674,
    "LOCK_TICKS_MAX": 150.396,
    "LOCK_ABANDON_T": 15.1416,
    "W_LOCK": 2.3612,
    "LOCK_THREAT_BREAK": 0.0102,
    "LUNGE_DISC_PANIC": 0.795288,
    "SPLIT_RUN_ENABLED": False,
    "SPLIT_RUN_MAX_MASS": 0.0029,
    "SPLIT_RUN_TRIGGER": 0.0094,
    "EAT_RATIO": 1.2,
    "SAFETY_RATIO": 1.15,
    "LEAD_TICKS": 1.1066,
    "LUNGE_ALARM_DIST": 0.0173,
    "W_LUNGE_ALARM": 0.3255,
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 17.1548,
    "SPLIT_SAFETY_RATIO": 0.0087,
    "SPLIT_MAX_BLOBS": 1.0613,
    "SPLIT_THREAT_CLEARANCE": 0.0393,
    "SPLIT_MIN_MASS": 2.0,
    "SPLIT_MAX_MASS": 95.3591,
    "VIRUS_DANGER_MASS_RATIO": 1.2,
    "VIRUS_AVOID_DIST": 1.8909,
    "VIRUS_FEAST_CLEAR": 2,
    # (BOOT_* and W_VIRUS_FOOD amputated 07-09: dead code paths, wasted mutations)
    "FEAST_MIN_MASS": 5.5174,
    "FEAST_SLOT_SAT": 0.3012,
    "W_VIRUS_FEAST": 1.3777,
    # --- SPLIT-FEAST CYCLE ORGAN (Team-15 virus economy; matches 1719/1721/1723) ---
    "SPLIT_CYCLE_ON": 0.9462,        # vetoable master switch (>0.5 = on); bounds (0,1)
    "CYCLE_MIN_MASS": 52.6056,       # only cycle once BIG (don't fragment a small bank); bounds (4,40)
    "CYCLE_THREAT_CLEAR": 30,   # only cycle when threats are FAR (avoid deaths-while-fragmented); bounds (2,30)
    # --- OMNI SWEEP (2026-07-09): every organ zeroable; magic numbers freed ---
    # promoted magic numbers (were hardcoded; evolution could never reach them)
    "HUNTER_AVOID_MULT": 1.7557,     # virus-avoid radius mult when hunter near (was 1.5)
    "HUNTER_REPEL_MULT": 2.7157,     # virus repulsion mult when hunter near (was 2.0)
    "WALL_ESC_MARGIN_MULT": 1.2685,  # wall-escape activation margin (was 1.2)
    "WALL_ESC_NUDGE": 0.1782,        # outward nudge strength (was 0.2)
    "LUNGE_DISC_FRAC": 0.9272,       # deep-disc panic fraction (was 0.9)
    "SPLIT_ALIGN_MIN": 0.6,       # prey-lunge alignment gate (was 0.7)
    "DEATH_COST_SCALE": 15.8005,     # bank-size fear scaling divisor (was 25)
    "VIRUS_FEAST_FALLOFF": 0.5,   # feast attraction falloff exponent (was 1/d)
    "CYCLE_TARGET_BLOBS": 15.5241,   # cycle split ceiling (was 16)
    # ORGAN: corner-siege fix (uncatchable corner-tucked prey -> zero force)
    "CORNER_SKIP_ON": 1,        # >0.5 on; bounds (0,1)
    "CORNER_TUCK": 1.1997,
    "CORNER_MARGIN": 0.4162,
    # ORGAN: sized threat gate (only count watchers that can actually eat us)
    "THREAT_SIZE_GATE": 0.0671,      # 0=all threats count (legacy); >0: hunter_near only if threat mass >= ours*gate
    # ORGAN: virus shield (hide behind viruses; big pursuers pop crossing them)
    "W_VIRUS_SHIELD": 0.1071,        # 0=off; attraction to viruses when fleeing while small
    "SHIELD_MAX_MASS": 8.8807,       # only shield when total below this (we pass under gate)
    # ORGAN: fragment hunting (counter the split-feast meta: eat cyclers mid-cycle)
    "W_FRAG_HUNT": 0.2049,           # 0=off; prey-force mult vs players at high blob count
    "FRAG_HUNT_MIN_BLOBS": 9.6227,   # enemy blob count to trigger
    # ORGAN: piece guard (post-consumption regroup surge; heals the loss30 wound)
    "W_PIECE_GUARD": 0,         # 0=off; extra regroup for GUARD_TICKS after our shatter
    "PIECE_GUARD_TICKS": 12.28,
    # ORGAN: idle merge drive (cycle regroup half: pull together when no virus work)
    "W_MERGE_IDLE": 0.3152,          # 0=off; regroup when fragmented + no viruses visible
    # ORGAN: map positioning (center vs edge preference; evolution picks sign)
    "W_CENTER": 0.0081,              # 0=off; + seeks center, - seeks edges
    # ORGAN: hunger-scaled food greed (small bots chase pellets harder)
    "FOOD_HUNGER_EXP": 0.0264,       # 0=off; food force *= (1/total_mass)^exp
    # ORGAN: stall kick (anti-deadlock: displacement ~0 while mass decays -> kick)
    "STALL_KICK_ON": 0.4179,         # >0.5 on
    "STALL_TICKS": 63.69,
    "STALL_DIST": 0.929,
    "W_STALL_KICK": 1.9867,
    # ORGAN: endgame posture (protect the bank late; final mass IS the score)
    "ENDGAME_START": 0.7806,         # fraction of EXPECTED_ROUNDS after which endgame fear applies; 1.0=off
    "ENDGAME_FEAR_MULT": 1.2248,     # threat-force mult in endgame; 1.0=neutral
    "EXPECTED_ROUNDS": 1400.0,
    # ORGAN: speed-aware threat pricing (slow giants can't catch us outside envelope)
    "W_ENVELOPE_SCALE": 0.4827,      # 0=off; scales threat force by kill-envelope proximity
    # ORGAN: per-player aggression memory (avoid players who hunt US specifically)
    "AGGRO_ON": 0.1396,              # >0.5 on
    "W_AGGRO": 0.6343,               # extra threat weight vs measured aggressors
    # ===== OMNI-2 ORGANS (2026-07-10): the four inexpressible classes + virus timing =====
    # ORGAN W1: WEALTH PRESERVATION — mass-conditional fear (banking). live evidence: peak-69 -> final-0.8 deaths
    "W_WEALTH_FEAR": 0.0448,         # 0=off; threat force mult grows with own mass above WEALTH_START
    "WEALTH_START": 54.4821,         # own total mass where wealth fear begins
    "WEALTH_EXP": 0.6774,            # curve shape
    # ORGAN W2: VIRUS-RESPAWN CAMPING — engine law: virus respawns ~30 rounds after consumption
    "W_CAMP": 0.199,                # 0=off; attraction to due-respawn sites inside the window
    "CAMP_WINDOW_LO": 22.7304,       # rounds since consumption when attraction starts
    "CAMP_WINDOW_HI": 57.3835,       # ... and ends (site pruned)
    "CAMP_MAX_MASS": 78.9632,        # too rich to camp (banking dominates)
    # ORGAN W3: GRUDGE MEMORY — per-opponent caution after they cost us mass
    "W_GRUDGE": 0.0903,              # 0=off; extra threat weight vs players who ate our blobs
    "GRUDGE_DECAY": 0.9995,        # per-tick decay
    # ORGAN W4: RANK POSTURE — visible-field standings condition greed/fear
    "W_RANK_GUARD": 1.6438,          # 0=off; threat mult when leading the visible field
    "W_RANK_AGGRO": 0.1157,          # 0=off; prey mult when trailing the visible field
    # ORGAN W5: VIRUS SLOT TIMING — pieces=max(1,17-blobs): saturated consumption is free mass
    "VIRUS_SLOT_EXP": 0.1134,        # 0=off; feast force *= (blobs/16)^exp
    # ===== OMNI-2.1 PROFILER (in-body stupid/mid/elite classifier; Chris's order 2026-07-10) =====
    "PROF_ON": 0.6241,                 # MASTER GATE: <=0.5 -> entire profiler off (zero compute, zero state)
    "PROF_ELITE_T": 0.5,           # EMA score above -> ELITE
    "PROF_STUPID_T": 0.3093,          # EMA score below -> STUPID
    "PROF_RADIUS": 22.736,            # elite-proximity radius gating feast boldness
    "PROF_PREY_STUPID": 0,        # extra prey force vs STUPID targets
    "PROF_PREY_ELITE_DISC": 0.017,    # prey force discount vs ELITE targets (0..1)
    "PROF_THREAT_STUPID_DISC": 0, # threat force discount for STUPID giants (0..1)
    "PROF_THREAT_ELITE_MULT": 0.0791,  # extra threat force vs proven-ELITE hunters
    "PROF_FEAST_BOLD": 0.0331,         # virus-feast/cycle boldness when no ELITE within PROF_RADIUS
    # ===== OMNI-2.1 corner refuge (gate = weight > 0) =====
    "W_CORNER_REFUGE": 0.4055,         # when hunted by an uncatchable-for-us giant: tuck into ITS unreachable corner
    "AGGRO_DECAY": 0.9,
    # ===== FARM-1 ISOLATION-FARMING ORGAN (2026-07-12, from Team-15 autopsy) =====
    # Team-15 (37.55 leader): 530 food/game in EMPTY space, 0.2 threats-within-15u always.
    # Package = conditional: threats near -> evacuate (damp everything else);
    # clear -> vacuum food with organ-local weight (+ edge-ring bias). Master-gated.
    "FARM_ON": 1.0,             # MASTER GATE: <=0.5 -> zero compute, chassis identical
    "FARM_ISO_R": 15.0,         # isolation radius (Team-15 keeps ~15u clear)
    "FARM_W_ISO": 3.0,          # evacuation force weight
    "FARM_ISO_DAMP": 0.3,       # multiplier on all other drives while evacuating
    "FARM_W_FOOD": 0.6,         # organ food-vacuum weight (only when isolated/clear)
    "FARM_FF": 1.8,             # food falloff for the vacuum
    "FARM_EDGE": 0.2,           # edge-ring preference while farming (0=off)
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
        # OMNI-2.1 profiler state (only written when PROF_ON)
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
            fx -= ux * f
            fy -= uy * f
        elif mass(my_largest) >= mass(b.radius) * CONFIG["EAT_RATIO"]:
            # ORGAN corner-skip: geometrically uncatchable corner-tucked prey
            if CONFIG["CORNER_SKIP_ON"] > 0.5:
                wdx = min(b.pos[0], ARENA_SIZE - b.pos[0])
                wdy = min(b.pos[1], ARENA_SIZE - b.pos[1])
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

    # ===== FARM-1: conditional isolation-farming (master-gated) =====
    if CONFIG["FARM_ON"] > 0.5:
        _near = [(t, d) for t, d in info["threats"] if d < CONFIG["FARM_ISO_R"]]
        if _near:
            # EVACUATE: damp every other drive, flee the mass-weighted threat centroid
            _tm = sum(mass(t.radius) for t, _ in _near)
            _tx = sum(t.pos[0] * mass(t.radius) for t, _ in _near) / _tm
            _ty = sum(t.pos[1] * mass(t.radius) for t, _ in _near) / _tm
            fx *= CONFIG["FARM_ISO_DAMP"]
            fy *= CONFIG["FARM_ISO_DAMP"]
            ux, uy, _d = unit(cx - _tx, cy - _ty)
            fx += ux * CONFIG["FARM_W_ISO"]
            fy += uy * CONFIG["FARM_W_ISO"]
        else:
            # FARM: vacuum food; prefer the edge ring
            for _f in st.visible_food:
                ux, uy, d = unit(_f.pos[0] - cx, _f.pos[1] - cy)
                if d < EPS: continue
                fx += ux * CONFIG["FARM_W_FOOD"] / (d ** CONFIG["FARM_FF"] + EPS)
                fy += uy * CONFIG["FARM_W_FOOD"] / (d ** CONFIG["FARM_FF"] + EPS)
            if CONFIG["FARM_EDGE"] != 0:
                ux, uy, _d = unit(cx - ARENA_SIZE / 2, cy - ARENA_SIZE / 2)
                fx += ux * CONFIG["FARM_EDGE"]
                fy += uy * CONFIG["FARM_EDGE"]

    return fx, fy, info


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


def should_cycle_split(game: Game, info: dict) -> bool:
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
    for _t, d in info["threats"]:
        if d < CONFIG["CYCLE_THREAT_CLEAR"]:
            return False  # threat in clearance -> veto cycle, regroup instead
    return True


# ----------------------------------------------------------------------------
# Main loop.
# ----------------------------------------------------------------------------
def main() -> None:
    game = Game()
    tracker = Tracker()

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

                        split = should_split(game, info, fx, fy) \
                            or should_cycle_split(game, info)
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
                    return MovePlayer(
                        player_id=game.state.me.player_id,
                        direction=DirectionModel(x=fx, y=fy),
                        split=split,
                    )
            raise RuntimeError(f"Unsupported query type: {type(query)}")

        game.send_move(choose_move(query))


if __name__ == "__main__":
    main()
