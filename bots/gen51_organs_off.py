"""
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
    # --- force weights ---
    "W_FOOD": 4.07936,           # attraction per food pellet
    "W_PREY": 20.6899,          # attraction toward edible enemy blobs (x their mass)
    "W_THREAT": 4.96803,        # repulsion from blobs that can eat us (x their mass)
    "W_VIRUS_BIG": 149.564,     # repulsion from viruses when we are big/unsplit-averse
    "W_WALL": 0.254707,           # repulsion from arena walls inside the margin
    "W_REGROUP": 0.00155097,        # pull our own blobs toward our centroid when split

    # --- distance shaping ---
    "FOOD_FALLOFF": 2.81826,     # force ~ w / (d^falloff); 1 favours clusters over nearest
    "PREY_FALLOFF": 0.246623,
    "THREAT_FALLOFF": 0.477109,   # steep: distant threats barely matter, close ones dominate
    "THREAT_PANIC_DIST": 0.299213,   # inside this, threat force is multiplied
    "THREAT_PANIC_MULT": 2.1801,
    "THREAT_IGNORE_DIST": 21.8739,  # beyond this, big-but-slow blobs are ignored (keep farming)
    "SPLIT_REACH": 51.3259,         # engine: eject speed 1.6, drag 0.82 -> ~8.9 units max lunge
    "W_SPLIT_ZONE": 0.239518,       # repulsion from being inside a split-capable threat's lunge radius
    "WALL_MARGIN": 2.25733,      # start repelling this far from a wall
    "FRESH_MASS": 0.81,       # below this total mass we are in survival mode
    "FRESH_CAUTION": 0.796333,    # fear multiplier (and greed divisor) while fresh
    # ===== GEOMETRY ORGANS (hybrid challenger) =====
    "VETO_ENABLED": False,       # constitutional veto: lethal directions cannot win
    "VETO_MARGIN": 1.45989,         # padding added to every kill envelope
    "VETO_HORIZON": 3.47174,        # ticks of our travel checked along each direction
    "VETO_SOFT_MASS": 7.07846,      # below this bank, no vetoes (fresh = expendable)
    "LOCK_ENABLED": False,       # commitment latch: hunt one target to conclusion
    "LOCK_MIN_VALUE": 0.377547,      # ignore prey worth less mass than this
    "LOCK_TICKS_MAX": 176.989,      # forced re-election after this many ticks
    "LOCK_ABANDON_T": 52.9932,     # abandon if intercept time exceeds this (ticks)
    "W_LOCK": 5.24842,             # goal-pull weight for the locked target
    "LOCK_THREAT_BREAK": 7.47491,   # drop the hunt if a threat closes within this
    # inside a lunge-ready killer's disc, its pull must outvote EVERYTHING:
    "LUNGE_DISC_PANIC": 0.795288, # multiplier on split-zone force when inside 0.9x reach
    # SPLIT-RUN escape: split away to fire our halves at eject speed 1.6
    "SPLIT_RUN_ENABLED": False,
    "SPLIT_RUN_MAX_MASS": 0.0350796,  # only worth it while the bank is small
    "SPLIT_RUN_TRIGGER": 1.22671,    # pursuer inside this and closing -> consider it

    # --- eat/threat classification ---
    "EAT_RATIO": 1.2,        # engine rule: must be >= 20% larger (by radius)
    "SAFETY_RATIO": 1.18,    # treat anything within 12% of edible-us as a threat too

    # --- prediction ---
    "LEAD_TICKS": 1.35433,         # extrapolate enemy velocity this many ticks ahead
    "LUNGE_ALARM_DIST": 0.0116355,   # react to hostile split intent within this range
    "W_LUNGE_ALARM": 4.96911,      # extra flee force when a bigger blob splits at us

    # --- split attack ---
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 30.7322,      # only lunge if predicted prey within this distance
    "SPLIT_SAFETY_RATIO": 0.0139102,  # each half must be >= this x prey radius (buffer over 1.2)
    "SPLIT_MAX_BLOBS": 1.43388,        # never split if we'd exceed this many blobs
    "SPLIT_THREAT_CLEARANCE": 0.853938,  # no threat within this distance when we split
    "SPLIT_MIN_MASS": 2.0,       # engine minimum
    "SPLIT_MAX_MASS": 73.7336,      # above this total mass, never lunge: protect the bank

    # --- virus handling ---
    "VIRUS_DANGER_MASS_RATIO": 1.2,  # engine: consume needs blob.mass > 1.5*1.2 = 1.8
    "VIRUS_AVOID_DIST": 5.47303,
    # VIRUS ECONOMY (engine: consuming grants +1.5 mass = ~67 pellets; 6 respawning
    # viruses make this ~3x the entire pellet economy). Feast when safe, fear when hunted.
    "W_VIRUS_FOOD": 0.0352581,       # attraction to consumable viruses when no hunter is near
    "VIRUS_FEAST_CLEAR": 2.04038,  # no threat within this distance -> virus is food, not hazard
    # OPENING BOOK: below BOOT_MASS a virus is +60-83% and our pieces are
    # worthless confetti -> feast harder, demand less clearance.
    "BOOT_MASS": 0.250671,
    "BOOT_VIRUS_MULT": 1.511,
    "BOOT_VIRUS_CLEAR": 4.7609,
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
    if threat.radius >= my_r * CONFIG["EAT_RATIO"]:
        r = threat.radius + my_r + 1.0
        closing = blob_speed_of(threat.radius) - blob_speed_of(my_r)
        if closing > 0:
            r = max(r, threat.radius + my_r + closing * CONFIG["VETO_HORIZON"] * 2)
    if (threat.radius / math.sqrt(2)) >= my_r * CONFIG["EAT_RATIO"] and mass(threat.radius) >= 4.0:
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

        if b.radius >= my_smallest * CONFIG["SAFETY_RATIO"]:
            # can eat (or nearly eat) at least one of our blobs -> threat
            info["threats"].append((b, d))
            can_split_kill = (b.radius / math.sqrt(2)) >= my_smallest * CONFIG["EAT_RATIO"] \
                and mass(b.radius) >= 2 * 2.0  # halves stay above engine split min
            # SPLIT-ZONE PROPHYLAXIS: never linger inside a split-capable
            # threat's lunge radius (~9u). "Big means slow" does NOT apply to
            # ejected halves; this overrides THREAT_IGNORE_DIST.
            if can_split_kill and d < CONFIG["SPLIT_REACH"] + my_smallest:
                f = caution * CONFIG["W_SPLIT_ZONE"] * mass(b.radius) / (d + EPS)
                if d < 0.9 * CONFIG["SPLIT_REACH"]:
                    f *= CONFIG["LUNGE_DISC_PANIC"]  # deep in the disc: this is law
                # the bigger we are, the more a death costs (avg-final-weight metric)
                f *= 1.0 + mass(my_largest) / 25.0
                fx -= ux * f
                fy -= uy * f
            # SPLIT-LUNGE ALARM: a threat just submitted split aimed our way.
            # Split halves travel ~8.9 units; react even beyond normal ignore range.
            if tracker.intent_split.get(b.player_id) and (b.radius / math.sqrt(2)) >= my_smallest * CONFIG["EAT_RATIO"]:
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
            fx -= ux * f
            fy -= uy * f
        elif my_largest >= b.radius * CONFIG["EAT_RATIO"]:
            f = (CONFIG["W_PREY"] / caution) * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)
            fx += ux * f
            fy += uy * f
            info["prey"].append((b, d))

    # --- viruses (2026.1.9): zero reward, pure fragmentation hazard. Avoid
    # whenever we are big enough to pop; harder while any hunter is around. ---
    can_pop = mass(my_largest) > VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]
    hunter_near = any(d < CONFIG["VIRUS_FEAST_CLEAR"] for _, d in info["threats"])
    for v in st.visible_viruses:
        if not can_pop:
            continue  # sub-threshold blobs pass through harmlessly
        ux, uy, d = unit(v.pos[0] - cx, v.pos[1] - cy)
        if d < EPS:
            continue
        if d < CONFIG["VIRUS_AVOID_DIST"] * (1.5 if hunter_near else 1.0):
            f = CONFIG["W_VIRUS_BIG"] * (2.0 if hunter_near else 1.0) / (d * d + EPS)
            fx -= ux * f
            fy -= uy * f

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
        wm = CONFIG["WALL_MARGIN"] * 1.2
        if cx < wm and fx < 0:
            fy += math.copysign(abs(fx), fy if abs(fy) > EPS else 1.0)
            fx = 0.2  # gentle outward nudge
        elif ARENA_SIZE - cx < wm and fx > 0:
            fy += math.copysign(abs(fx), fy if abs(fy) > EPS else 1.0)
            fx = -0.2
        if cy < wm and fy < 0:
            fx += math.copysign(abs(fy), fx if abs(fx) > EPS else 1.0)
            fy = 0.2
        elif ARENA_SIZE - cy < wm and fy > 0:
            fx += math.copysign(abs(fy), fx if abs(fx) > EPS else 1.0)
            fy = -0.2

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
            if fmag > EPS and (fx * ux + fy * uy) / fmag > 0.7:
                return True
    return False


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

                        split = should_split(game, info, fx, fy)
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
