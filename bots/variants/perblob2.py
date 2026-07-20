"""
SYNCS Bot Battle 2026 — potential-field bot, PER-BLOB FORCES variant.

Same architecture as my_bot.py, but forces are computed from each of our own
blobs individually (each blob classifies threats/prey against ITS OWN radius
and position). Food/prey/virus/wall forces combine weighted by blob mass, but
THREAT forces combine with equal per-blob weight: a small vulnerable blob gets
a full-strength vote to flee even though its mass share is tiny (the mass-
weighted version — perblob.py — farmed fatter but died more: muted fear).

Split-gate distances also improve: threat clearance uses the closest approach
to ANY of our blobs; prey range is measured from the largest blob (the lunger).

Engine facts baked in (verified in agario-public src, v2026.1.7):
  arena 60x60, 8 players, 1400 rounds @ 0.1s, eat ratio 1.2x (radius),
  speed = 1.1 - 0.08*r (min 0.25), mass decay 0.2%/tick, mass ~ radius^2,
  split needs mass >= 2.0 and splits EVERY qualifying blob, merge cd 18 ticks,
  max 16 blobs, viruses r=1.5 static, pop blobs with mass > 1.8 (+1.5 mass).
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
    "LEAD_TICKS": 4,         # extrapolate enemy velocity this many ticks ahead

    # --- split attack ---
    "SPLIT_ENABLED": True,
    "SPLIT_MAX_RANGE": 6.0,      # only lunge if predicted prey within this distance
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
# 3. Force computation (per own blob, combined mass-weighted).
# ----------------------------------------------------------------------------
def unit(dx: float, dy: float) -> tuple[float, float, float]:
    d = math.hypot(dx, dy)
    if d < EPS:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


def compute_forces(game: Game, tracker: Tracker) -> tuple[float, float, dict]:
    st = game.state
    me = st.me
    my_blobs = list(me.blobs.values())
    if not my_blobs:
        return 0.0, 0.0, {"threats": [], "prey": []}
    largest_blob = max(my_blobs, key=lambda b: b.radius)
    my_largest = largest_blob.radius
    total_mass = sum(mass(b.radius) for b in my_blobs)

    # predict every enemy once, reuse for each of our blobs
    enemies: list[tuple[object, float, float]] = []
    for b in st.visible_blobs:
        if b.player_id == me.player_id:
            continue
        px, py = tracker.predict(b, CONFIG["LEAD_TICKS"])
        enemies.append((b, px, py))

    fx, fy = 0.0, 0.0
    # info for the split gate: threat distance = closest approach to any of our
    # blobs; prey distance = from the largest blob (the one whose halves lunge)
    threat_min: dict[tuple[int, int], tuple[object, float]] = {}
    prey_info: list[tuple[object, float]] = []

    for e, px, py in enemies:
        if my_largest >= e.radius * CONFIG["EAT_RATIO"]:
            _, _, d = unit(px - largest_blob.pos[0], py - largest_blob.pos[1])
            prey_info.append((e, max(d, EPS)))

    n_blobs = len(my_blobs)
    for myb in my_blobs:
        bx, by = myb.pos
        br = myb.radius
        weight = mass(br) / total_mass
        gx, gy = 0.0, 0.0  # mass-weighted forces (food/prey/virus/wall)
        tx, ty = 0.0, 0.0  # threat forces: equal per-blob weight (see docstring)

        # --- food ---
        for food in st.visible_food:
            ux, uy, d = unit(food.pos[0] - bx, food.pos[1] - by)
            if d < EPS:
                continue
            f = CONFIG["W_FOOD"] / (d ** CONFIG["FOOD_FALLOFF"] + EPS)
            gx += ux * f
            gy += uy * f

        # --- enemy blobs, classified against THIS blob's radius ---
        for e, px, py in enemies:
            ux, uy, d = unit(px - bx, py - by)
            if d < EPS:
                d = EPS

            if e.radius >= br * CONFIG["SAFETY_RATIO"]:
                key = (e.player_id, e.blob_id)
                prev = threat_min.get(key)
                if prev is None or d < prev[1]:
                    threat_min[key] = (e, d)
                if d > CONFIG["THREAT_IGNORE_DIST"]:
                    continue  # big means slow: distant threats can't catch us
                f = CONFIG["W_THREAT"] * mass(e.radius) / (d ** CONFIG["THREAT_FALLOFF"] + EPS)
                if d < CONFIG["THREAT_PANIC_DIST"]:
                    f *= CONFIG["THREAT_PANIC_MULT"]
                tx -= ux * f
                ty -= uy * f
            elif br >= e.radius * CONFIG["EAT_RATIO"]:
                f = CONFIG["W_PREY"] * mass(e.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)
                gx += ux * f
                gy += uy * f

        # --- viruses: only blobs heavy enough to pop need to care ---
        if mass(br) >= VIRUS_MASS * CONFIG["VIRUS_DANGER_MASS_RATIO"]:
            for v in st.visible_viruses:
                ux, uy, d = unit(v.pos[0] - bx, v.pos[1] - by)
                if d < CONFIG["VIRUS_AVOID_DIST"] and d > EPS:
                    f = CONFIG["W_VIRUS_BIG"] / (d * d + EPS)
                    gx -= ux * f
                    gy -= uy * f

        # --- walls ---
        m = CONFIG["WALL_MARGIN"]
        if bx < m:
            gx += CONFIG["W_WALL"] * (m - bx) / m
        if ARENA_SIZE - bx < m:
            gx -= CONFIG["W_WALL"] * (m - (ARENA_SIZE - bx)) / m
        if by < m:
            gy += CONFIG["W_WALL"] * (m - by) / m
        if ARENA_SIZE - by < m:
            gy -= CONFIG["W_WALL"] * (m - (ARENA_SIZE - by)) / m

        fx += gx * weight + tx / n_blobs
        fy += gy * weight + ty / n_blobs

    info = {"threats": list(threat_min.values()), "prey": prey_info}

    # --- regroup our own blobs under threat (per blob toward centroid) ---
    if len(my_blobs) > 1 and info["threats"]:
        gx_c = sum(b.pos[0] * mass(b.radius) for b in my_blobs) / total_mass
        gy_c = sum(b.pos[1] * mass(b.radius) for b in my_blobs) / total_mass
        for myb in my_blobs:
            weight = mass(myb.radius) / total_mass
            ux, uy, d = unit(gx_c - myb.pos[0], gy_c - myb.pos[1])
            fx += ux * CONFIG["W_REGROUP"] * d * weight
            fy += uy * CONFIG["W_REGROUP"] * d * weight

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
