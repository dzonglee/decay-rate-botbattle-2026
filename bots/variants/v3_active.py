"""
v3_active: my_bot_v3 with the three dormant features ENABLED
(LUNGE_DISC_PANIC 3.0, SPLIT_RUN on, BOOT_VIRUS_MULT 2.0 / BOOT_VIRUS_CLEAR 7.0).

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
    "W_FOOD": 1.0,           # attraction per food pellet
    "W_PREY": 14.0,          # attraction toward edible enemy blobs (x their mass)
    "W_THREAT": 90.0,        # repulsion from blobs that can eat us (x their mass)
    "W_VIRUS_BIG": 25.0,     # repulsion from viruses when we are big/unsplit-averse
    "W_WALL": 8.0,           # repulsion from arena walls inside the margin
    "W_REGROUP": 2.0,        # pull our own blobs toward our centroid when split

    # --- distance shaping ---
    "FOOD_FALLOFF": 1.0,     # force ~ w / (d^falloff); 1 favours clusters over nearest
    "PREY_FALLOFF": 1.5,
    "THREAT_FALLOFF": 2.0,   # steep: distant threats barely matter, close ones dominate
    "THREAT_PANIC_DIST": 4.0,   # inside this, threat force is multiplied
    "THREAT_PANIC_MULT": 4.0,
    "THREAT_IGNORE_DIST": 7.0,  # beyond this, big-but-slow blobs are ignored (keep farming)
    "SPLIT_REACH": 9.0,         # engine: eject speed 1.6, drag 0.82 -> ~8.9 units max lunge
    "W_SPLIT_ZONE": 60.0,       # repulsion from being inside a split-capable threat's lunge radius
    "WALL_MARGIN": 4.0,      # start repelling this far from a wall
    "FRESH_MASS": 2.0,       # below this total mass we are in survival mode
    "FRESH_CAUTION": 2.5,    # fear multiplier (and greed divisor) while fresh
    # inside a lunge-ready killer's disc, its pull must outvote EVERYTHING:
    "LUNGE_DISC_PANIC": 3.0, # multiplier on split-zone force when inside 0.9x reach
    # SPLIT-RUN escape: split away to fire our halves at eject speed 1.6
    "SPLIT_RUN_ENABLED": True,
    "SPLIT_RUN_MAX_MASS": 14.0,  # only worth it while the bank is small
    "SPLIT_RUN_TRIGGER": 7.5,    # pursuer inside this and closing -> consider it

    # --- eat/threat classification ---
    "EAT_RATIO": 1.2,        # engine rule: must be >= 20% larger (by radius)
    "SAFETY_RATIO": 1.12,    # treat anything within 12% of edible-us as a threat too

    # --- prediction ---
    "LEAD_TICKS": 4,         # extrapolate enemy velocity this many ticks ahead
    "LUNGE_ALARM_DIST": 10.0,   # react to hostile split intent within this range
    "W_LUNGE_ALARM": 40.0,      # extra flee force when a bigger blob splits at us

    # --- split attack ---
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 6.0,      # only lunge if predicted prey within this distance
    "SPLIT_SAFETY_RATIO": 1.35,  # each half must be >= this x prey radius (buffer over 1.2)
    "SPLIT_MAX_BLOBS": 4,        # never split if we'd exceed this many blobs
    "SPLIT_THREAT_CLEARANCE": 9.0,  # no threat within this distance when we split
    "SPLIT_MIN_MASS": 2.0,       # engine minimum
    "SPLIT_MAX_MASS": 30.0,      # above this total mass, never lunge: protect the bank

    # --- virus handling ---
    "VIRUS_DANGER_MASS_RATIO": 1.2,  # engine: consume needs blob.mass > 1.5*1.2 = 1.8
    "VIRUS_AVOID_DIST": 3.5,
    # VIRUS ECONOMY (engine: consuming grants +1.5 mass = ~67 pellets; 6 respawning
    # viruses make this ~3x the entire pellet economy). Feast when safe, fear when hunted.
    "W_VIRUS_FOOD": 25.0,       # attraction to consumable viruses when no hunter is near
    "VIRUS_FEAST_CLEAR": 11.0,  # no threat within this distance -> virus is food, not hazard
    # OPENING BOOK: below BOOT_MASS a virus is +60-83% and our pieces are
    # worthless confetti -> feast harder, demand less clearance.
    "BOOT_MASS": 6.0,
    "BOOT_VIRUS_MULT": 2.0,
    "BOOT_VIRUS_CLEAR": 7.0,
}

ARENA_SIZE = 60.0
# Engine fact (state_mutator._can_consume_virus): a blob pops on a virus when
# blob.mass > virus.radius * EAT_SIZE_RATIO — the engine uses the RADIUS (1.5)
# as the virus's "mass", not radius^2. Danger starts at blob radius ~1.342.
VIRUS_MASS = 1.5
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

    def read_intents(self, game: Game) -> None:
        """Engine currently forwards every player's move_player event unchanged.
        Harvest direction + split flag; degrade gracefully if this gets patched."""
        self.intent_split = {}
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

    # --- viruses: PRIMARY FOOD SOURCE when safe, fragmentation hazard when hunted ---
    can_consume = mass(my_largest) > VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]
    booting = total_mass < CONFIG["BOOT_MASS"]
    clear_need = CONFIG["BOOT_VIRUS_CLEAR"] if booting else CONFIG["VIRUS_FEAST_CLEAR"]
    hunter_near = any(d < clear_need for _, d in info["threats"])
    for v in st.visible_viruses:
        if not can_consume:
            continue  # engine: sub-threshold blobs don't interact with viruses at all
        ux, uy, d = unit(v.pos[0] - cx, v.pos[1] - cy)
        if d < EPS:
            continue
        if hunter_near:
            # splitting with a predator nearby is how everyone dies: hazard mode
            if d < CONFIG["VIRUS_AVOID_DIST"]:
                f = CONFIG["W_VIRUS_BIG"] / (d * d + EPS)
                fx -= ux * f
                fy -= uy * f
        else:
            # +1.5 mass per virus: feast. Fragmentation self-heals in ~2s
            # (18-frame merge cooldown), and more blobs -> FEWER new pieces.
            f = CONFIG["W_VIRUS_FOOD"] * (CONFIG["BOOT_VIRUS_MULT"] if booting else 1.0) \
                / (d ** CONFIG["FOOD_FALLOFF"] + EPS)
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
