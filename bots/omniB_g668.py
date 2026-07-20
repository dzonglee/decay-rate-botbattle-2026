"""
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
    "W_FOOD": 0.000454246,
    "W_PREY": 0.890818,
    "W_THREAT": 1,
    "W_VIRUS_BIG": 0.00340284,
    "W_WALL": 6.49268e-07,
    "W_REGROUP": 1.78911e-08,
    "FOOD_FALLOFF": 2.22504,
    "PREY_FALLOFF": 0.0848779,
    "THREAT_FALLOFF": 1.77771e-07,
    "THREAT_PANIC_DIST": 0.201797,
    "THREAT_PANIC_MULT": 6.01217e-05,
    "THREAT_IGNORE_DIST": 26.0599,
    "SPLIT_REACH": 51.3259,
    "W_SPLIT_ZONE": 0.000107126,
    "WALL_MARGIN": 1.68838e-07,
    "FRESH_MASS": 0.839139,
    "FRESH_CAUTION": 0.000281039,
    "VETO_ENABLED": False,
    "VETO_MARGIN": 9.98059e-06,
    "VETO_HORIZON": 2.06213,
    "VETO_SOFT_MASS": 0.951781,
    "LOCK_ENABLED": False,
    "LOCK_MIN_VALUE": 0.0012988,
    "LOCK_TICKS_MAX": 24.4869,
    "LOCK_ABANDON_T": 15.4954,
    "W_LOCK": 0.000331911,
    "LOCK_THREAT_BREAK": 2.77437e-05,
    "LUNGE_DISC_PANIC": 0.795288,
    "SPLIT_RUN_ENABLED": False,
    "SPLIT_RUN_MAX_MASS": 2.65496e-08,
    "SPLIT_RUN_TRIGGER": 0.00151275,
    "EAT_RATIO": 1.2,
    "SAFETY_RATIO": 1.16348,
    "LEAD_TICKS": 1.93471,
    "LUNGE_ALARM_DIST": 8.45915e-05,
    "W_LUNGE_ALARM": 0.0325766,
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 68.2738,
    "SPLIT_SAFETY_RATIO": 1.90991e-07,
    "SPLIT_MAX_BLOBS": 1.36604,
    "SPLIT_THREAT_CLEARANCE": 3.80055e-06,
    "SPLIT_MIN_MASS": 2.0,
    "SPLIT_MAX_MASS": 609.943,
    "VIRUS_DANGER_MASS_RATIO": 1.2,
    "VIRUS_AVOID_DIST": 0.3,
    "VIRUS_FEAST_CLEAR": 8.09141,
    # (BOOT_* and W_VIRUS_FOOD amputated 07-09: dead code paths, wasted mutations)
    "FEAST_MIN_MASS": 15.6719,
    "FEAST_SLOT_SAT": 0.375999,
    "W_VIRUS_FEAST": 0.0374132,
    # --- SPLIT-FEAST CYCLE ORGAN (Team-15 virus economy; matches 1719/1721/1723) ---
    "SPLIT_CYCLE_ON": 8.22232e-05,        # vetoable master switch (>0.5 = on); bounds (0,1)
    "CYCLE_MIN_MASS": 4.47353,       # only cycle once BIG (don't fragment a small bank); bounds (4,40)
    "CYCLE_THREAT_CLEAR": 17.9662,   # only cycle when threats are FAR (avoid deaths-while-fragmented); bounds (2,30)
    # --- OMNI SWEEP (2026-07-09): every organ zeroable; magic numbers freed ---
    # promoted magic numbers (were hardcoded; evolution could never reach them)
    "HUNTER_AVOID_MULT": 0.849689,     # virus-avoid radius mult when hunter near (was 1.5)
    "HUNTER_REPEL_MULT": 1.04484,     # virus repulsion mult when hunter near (was 2.0)
    "WALL_ESC_MARGIN_MULT": 1.63689,  # wall-escape activation margin (was 1.2)
    "WALL_ESC_NUDGE": 0.1,        # outward nudge strength (was 0.2)
    "LUNGE_DISC_FRAC": 0.635785,       # deep-disc panic fraction (was 0.9)
    "SPLIT_ALIGN_MIN": 0.893408,       # prey-lunge alignment gate (was 0.7)
    "DEATH_COST_SCALE": 25.8345,     # bank-size fear scaling divisor (was 25)
    "VIRUS_FEAST_FALLOFF": 0.592494,   # feast attraction falloff exponent (was 1/d)
    "CYCLE_TARGET_BLOBS": 7.05301,   # cycle split ceiling (was 16)
    # ORGAN: corner-siege fix (uncatchable corner-tucked prey -> zero force)
    "CORNER_SKIP_ON": 0.0886401,        # >0.5 on; bounds (0,1)
    "CORNER_TUCK": 0.5,
    "CORNER_MARGIN": 1.2334e-05,
    # ORGAN: sized threat gate (only count watchers that can actually eat us)
    "THREAT_SIZE_GATE": 0.000530533,      # 0=all threats count (legacy); >0: hunter_near only if threat mass >= ours*gate
    # ORGAN: virus shield (hide behind viruses; big pursuers pop crossing them)
    "W_VIRUS_SHIELD": 0.00549027,        # 0=off; attraction to viruses when fleeing while small
    "SHIELD_MAX_MASS": 4.52645,       # only shield when total below this (we pass under gate)
    # ORGAN: fragment hunting (counter the split-feast meta: eat cyclers mid-cycle)
    "W_FRAG_HUNT": 0.000134024,           # 0=off; prey-force mult vs players at high blob count
    "FRAG_HUNT_MIN_BLOBS": 16,   # enemy blob count to trigger
    # ORGAN: piece guard (post-consumption regroup surge; heals the loss30 wound)
    "W_PIECE_GUARD": 0.000815112,         # 0=off; extra regroup for GUARD_TICKS after our shatter
    "PIECE_GUARD_TICKS": 2.90894,
    # ORGAN: idle merge drive (cycle regroup half: pull together when no virus work)
    "W_MERGE_IDLE": 1.12479e-07,          # 0=off; regroup when fragmented + no viruses visible
    # ORGAN: map positioning (center vs edge preference; evolution picks sign)
    "W_CENTER": 1.44757e-05,              # 0=off; + seeks center, - seeks edges
    # ORGAN: hunger-scaled food greed (small bots chase pellets harder)
    "FOOD_HUNGER_EXP": 2.38375e-05,       # 0=off; food force *= (1/total_mass)^exp
    # ORGAN: stall kick (anti-deadlock: displacement ~0 while mass decays -> kick)
    "STALL_KICK_ON": 0.00028217,         # >0.5 on
    "STALL_TICKS": 42.841,
    "STALL_DIST": 0.757881,
    "W_STALL_KICK": 0.038603,
    # ORGAN: endgame posture (protect the bank late; final mass IS the score)
    "ENDGAME_START": 0.807938,         # fraction of EXPECTED_ROUNDS after which endgame fear applies; 1.0=off
    "ENDGAME_FEAR_MULT": 0.5,     # threat-force mult in endgame; 1.0=neutral
    "EXPECTED_ROUNDS": 1400.0,
    # ORGAN: speed-aware threat pricing (slow giants can't catch us outside envelope)
    "W_ENVELOPE_SCALE": 0.0884402,      # 0=off; scales threat force by kill-envelope proximity
    # ORGAN: per-player aggression memory (avoid players who hunt US specifically)
    "AGGRO_ON": 9.45468e-07,              # >0.5 on
    "W_AGGRO": 9.14927e-06,               # extra threat weight vs measured aggressors
    "AGGRO_DECAY": 0.999,
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
            fx -= ux * f
            fy -= uy * f
        elif mass(my_largest) >= mass(b.radius) * CONFIG["EAT_RATIO"]:
            # ORGAN corner-skip: geometrically uncatchable corner-tucked prey
            if CONFIG["CORNER_SKIP_ON"] > 0.5:
                wdx = min(b.pos[0], ARENA_SIZE - b.pos[0])
                wdy = min(b.pos[1], ARENA_SIZE - b.pos[1])
                if wdx < CONFIG["CORNER_TUCK"] and wdy < CONFIG["CORNER_TUCK"]:
                    closest = math.hypot(max(my_largest - wdx, 0.0), max(my_largest - wdy, 0.0))
                    if closest - (my_largest + b.radius) + CONFIG["CORNER_MARGIN"] > 0:
                        continue
            f = (CONFIG["W_PREY"] / caution) * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)
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
    if CONFIG["STALL_KICK_ON"] > 0.5:
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
