"""
SYNCS Bot Battle 2026 — potential-field bot, INTERCEPT variant.

Same as my_bot.py except prey attraction uses true interception geometry
instead of a fixed LEAD_TICKS extrapolation: solve for the earliest time our
chase speed can meet the prey's projected path, steer at that point, and
abandon chases with no intercept inside CHASE_HORIZON ticks (uncatchable prey
no longer bends our path). Threat fleeing keeps the cheap LEAD_TICKS lead.

Engine facts baked in (verified in agario-public src, v2026.1.7):
  speed = max(0.25, 1.1 / (1 + 0.08*r)) per tick — hyperbolic, NOT linear;
  arena 60x60, eat ratio 1.2x radius, mass decay 0.2%/tick, mass ~ radius^2.
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
    "WALL_MARGIN": 4.0,      # start repelling this far from a wall

    # --- eat/threat classification ---
    "EAT_RATIO": 1.2,        # engine rule: must be >= 20% larger (by radius)
    "SAFETY_RATIO": 1.12,    # treat anything within 12% of edible-us as a threat too

    # --- prediction ---
    "LEAD_TICKS": 4,         # extrapolate THREAT velocity this many ticks ahead
    "CHASE_HORIZON": 60,     # abandon prey we cannot intercept within this many ticks

    # --- split attack ---
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 6.0,      # only lunge if intercept point within this distance
    "SPLIT_SAFETY_RATIO": 1.35,  # each half must be >= this x prey radius (buffer over 1.2)
    "SPLIT_MAX_BLOBS": 4,        # never split if we'd exceed this many blobs
    "SPLIT_THREAT_CLEARANCE": 9.0,  # no threat within this distance when we split
    "SPLIT_MIN_MASS": 2.0,       # engine minimum

    # --- virus handling ---
    "VIRUS_DANGER_MASS_RATIO": 1.2,  # engine: pops blobs with mass > VIRUS_MASS * this
    "VIRUS_AVOID_DIST": 3.5,
}

ARENA_SIZE = 60.0
# Engine fact (state_mutator._can_consume_virus): a blob pops on a virus when
# blob.mass > virus.radius * EAT_SIZE_RATIO — the engine uses the RADIUS (1.5)
# as the virus's "mass", not radius^2. Danger starts at blob radius ~1.342.
VIRUS_MASS = 1.5
EPS = 1e-9


def mass(radius: float) -> float:
    return radius * radius


def speed(radius: float) -> float:
    # engine: state_mutator._movement_speed
    return max(0.25, 1.1 / (1.0 + 0.08 * radius))


def intercept_time(
    rel_x: float, rel_y: float, vx: float, vy: float, s: float
) -> float | None:
    """Earliest t > 0 with |rel + v*t| = s*t, i.e. we can reach the target's
    projected position exactly as it gets there. None if uncatchable."""
    a = vx * vx + vy * vy - s * s
    b = 2.0 * (rel_x * vx + rel_y * vy)
    c = rel_x * rel_x + rel_y * rel_y
    if abs(a) < EPS:
        if abs(b) < EPS:
            return None
        t = -c / b
        return t if t > 0 else None
    disc = b * b - 4.0 * a * c
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t1 = (-b - sq) / (2.0 * a)
    t2 = (-b + sq) / (2.0 * a)
    best = None
    for t in (t1, t2):
        if t > 0 and (best is None or t < best):
            best = t
    return best


# ----------------------------------------------------------------------------
# 2. Velocity tracker for enemy blobs.
# ----------------------------------------------------------------------------
class Tracker:
    def __init__(self) -> None:
        self._last: dict[tuple[int, int], tuple[float, float]] = {}
        self.velocity: dict[tuple[int, int], tuple[float, float]] = {}

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
    chase_speed = speed(my_largest)  # the eater has to arrive, so its speed rules

    fx, fy = 0.0, 0.0
    info = {"threats": [], "prey": []}

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

        if b.radius >= my_smallest * CONFIG["SAFETY_RATIO"]:
            # can eat (or nearly eat) at least one of our blobs -> threat.
            # flee the short-lead prediction, as in the baseline.
            px, py = tracker.predict(b, CONFIG["LEAD_TICKS"])
            ux, uy, d = unit(px - cx, py - cy)
            if d < EPS:
                d = EPS
            info["threats"].append((b, d))
            if d > CONFIG["THREAT_IGNORE_DIST"]:
                continue  # big means slow(er): distant threats can't catch us
            f = CONFIG["W_THREAT"] * mass(b.radius) / (d ** CONFIG["THREAT_FALLOFF"] + EPS)
            if d < CONFIG["THREAT_PANIC_DIST"]:
                f *= CONFIG["THREAT_PANIC_MULT"]
            fx -= ux * f
            fy -= uy * f
        elif my_largest >= b.radius * CONFIG["EAT_RATIO"]:
            # prey: steer at the intercept point; skip uncatchable chases
            vx, vy = tracker.velocity.get((b.player_id, b.blob_id), (0.0, 0.0))
            t = intercept_time(b.pos[0] - cx, b.pos[1] - cy, vx, vy, chase_speed)
            if t is None or t > CONFIG["CHASE_HORIZON"]:
                continue  # can't catch it before it's gone: don't bend our path
            ix = min(max(b.pos[0] + vx * t, 0.0), ARENA_SIZE)  # walls stop them
            iy = min(max(b.pos[1] + vy * t, 0.0), ARENA_SIZE)
            ux, uy, d = unit(ix - cx, iy - cy)
            if d < EPS:
                d = EPS
            f = CONFIG["W_PREY"] * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)
            fx += ux * f
            fy += uy * f
            info["prey"].append((b, d))

    # --- viruses: avoid when big enough to pop on them ---
    for v in st.visible_viruses:
        if mass(my_largest) >= VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]:
            ux, uy, d = unit(v.pos[0] - cx, v.pos[1] - cy)
            if d < CONFIG["VIRUS_AVOID_DIST"] and d > EPS:
                f = CONFIG["W_VIRUS_BIG"] / (d * d + EPS)
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
                        tracker.update(game.state.visible_blobs, game.state.me.player_id)
                        fx, fy, info = compute_forces(game, tracker)
                        split = should_split(game, info, fx, fy)
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
