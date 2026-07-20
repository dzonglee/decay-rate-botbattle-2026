"""
SYNCS Bot Battle 2026 — predator bot ("v2").

Architecture:
  GEOMETRY   Kill envelopes from differential-game theory: a threat projects
             (a) a chase region — dangerous only if it can outrun us — and
             (b) a split-disc (~9u lunge) gated on its live split cooldown,
             which we track exactly from the broadcast move_player intents.
  SCORING    Each tick, 16 candidate directions are scored:
             hard VETO if the direction enters any envelope within the horizon;
             otherwise utility = gain(food, viruses, prey) - risk - wall cost.
  MODES      FLEE  — inside/near an envelope: pick the widest safe opening.
             HUNT  — committed single-target pursuit: proportional-navigation
                     intercept using the target's broadcast heading, herding
                     toward walls, split-lunge under strict bank rules.
             FARM  — viruses (engine grants +1.5 mass each; ~3x pellet economy)
                     when safe and consumable, else food clusters.
  BANK       Risk appetite scales with (mass x lateness): dying big and late
             is catastrophic under avg-final-weight scoring; dying fresh is free.

Engine facts baked in (verified in 2026.1.8 source):
  60x60, 8 players, 1400 rounds; eat needs 1.2x radius; speed 1.1-0.08r (min .25)
  decay 0.2%/tick floored at 0.81 mass; split: mass>=2, cooldown 18, reach ~8.9
  virus: consume if mass>1.8 (units bug, reported), grants +1.5, up to 16 pieces
  that re-merge on overlap; move_player events broadcast every player's
  direction+split to everyone (exploit while it lasts; velocity fallback built in).
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

# ---------------------------------------------------------------------------
# CONFIG — every tunable lives here (numeric values are evolvable genes).
# ---------------------------------------------------------------------------
CONFIG = {
    # --- envelopes / safety ---
    "SPLIT_REACH": 9.0,          # engine lunge distance (1.6 / (1-0.82))
    "ENVELOPE_MARGIN": 1.0,      # extra padding on every kill envelope
    "CHASE_HORIZON": 12.0,       # ticks ahead we must stay out of chase envelopes
    "PANIC_ENTER": 1.5,          # FLEE if any envelope boundary within this margin
    "SAFETY_RATIO": 1.12,        # near-edible counts as threat

    # --- bank / risk appetite ---
    "BANK_REF_MASS": 25.0,       # risk aversion doubles around this bank size
    "LATE_GAME_FRAC": 0.85,      # after this fraction of rounds, defence hardens
    "LATE_MARGIN_MULT": 1.8,     # envelope padding multiplier late game
    "FRESH_MASS": 2.0,           # below this we are expendable: be bold
    "FRESH_BOLD": 0.5,           # risk multiplier while fresh (<1 = braver)

    # --- hunting ---
    "HUNT_VALUE_MIN": 1.5,       # ignore prey worth less mass than this
    "HUNT_FEAS_SPEED_EDGE": 0.02,  # our speed must exceed theirs by this to chase
    "HUNT_MAX_INTERCEPT": 25.0,  # give up if intercept further than this
    "HUNT_COMMIT_TICKS": 40,     # keep a locked target at least this long
    "HERD_WALL_BIAS": 0.25,      # aim offset pushing prey toward nearest wall
    "SPLIT_KILL_RANGE": 7.5,     # lunge only inside this predicted distance
    "SPLIT_SAFETY_RATIO": 1.30,  # halves must be this x prey radius
    "SPLIT_MAX_MASS": 30.0,      # never lunge above this bank (protect the score)
    "SPLIT_CLEARANCE": 10.0,     # no non-prey threat within this when lunging
    "SPLIT_MIN_MASS": 2.0,

    # --- farming ---
    "W_FOOD": 1.0,
    "FOOD_FALLOFF": 1.0,         # cluster-seeking
    "W_VIRUS_FOOD": 20.0,        # virus = 67 pellets; dominant safe income
    "VIRUS_FEAST_CLEAR": 11.0,   # need no threat within this to feast
    "VIRUS_CONSUME_MASS": 1.81,  # engine (buggy) threshold; re-derive on updates!
    "W_PREY_FARM": 6.0,          # opportunistic prey pull while farming

    # --- movement scoring ---
    "N_DIRS": 16,
    "W_OPENNESS": 3.0,           # prefer directions with clearance from all threats
    "WALL_MARGIN": 3.0,
    "W_WALL": 4.0,
    "LEAD_TICKS": 4,
}

ARENA = 60.0
VIRUS_GRANT = 1.5
EAT = 1.2
SPLIT_COOLDOWN = 18
EPS = 1e-9


def mass(r: float) -> float:
    return r * r


def speed(r: float) -> float:
    return max(1.1 - 0.08 * r, 0.25)


def unit(dx: float, dy: float):
    d = math.hypot(dx, dy)
    if d < EPS:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


DIRS = [(math.cos(2 * math.pi * k / CONFIG["N_DIRS"]),
         math.sin(2 * math.pi * k / CONFIG["N_DIRS"])) for k in range(CONFIG["N_DIRS"])]


# ---------------------------------------------------------------------------
# Tracker: velocities, broadcast intents, and per-player split cooldown clocks.
# ---------------------------------------------------------------------------
class Tracker:
    def __init__(self) -> None:
        self._last: dict[tuple[int, int], tuple[float, float]] = {}
        self.velocity: dict[tuple[int, int], tuple[float, float]] = {}
        self.intent_dir: dict[int, tuple[float, float]] = {}
        self.intent_split: dict[int, bool] = {}
        self.split_clock: dict[int, int] = {}   # rounds since player last split

    def read_intents(self, game: Game) -> None:
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
                    ux, uy, d = unit(dx, dy)
                    if d > EPS:
                        self.intent_dir[pid] = (ux, uy)
                except Exception:
                    pass
                if getattr(e, "split", False):
                    self.intent_split[pid] = True
                    self.split_clock[pid] = 0

    def can_split_now(self, pid: int) -> bool:
        # unknown clock -> assume ready (worst case)
        return self.split_clock.get(pid, SPLIT_COOLDOWN + 1) > SPLIT_COOLDOWN

    def update(self, blobs, my_id: int) -> None:
        seen = set()
        for b in blobs:
            if b.player_id == my_id:
                continue
            k = (b.player_id, b.blob_id)
            seen.add(k)
            if k in self._last:
                lx, ly = self._last[k]
                self.velocity[k] = (b.pos[0] - lx, b.pos[1] - ly)
            self._last[k] = b.pos
        for k in list(self._last):
            if k not in seen:
                self._last.pop(k, None)
                self.velocity.pop(k, None)

    def heading(self, b) -> tuple[float, float]:
        d = self.intent_dir.get(b.player_id)
        if d is not None:
            return d
        vx, vy = self.velocity.get((b.player_id, b.blob_id), (0.0, 0.0))
        ux, uy, dd = unit(vx, vy)
        return (ux, uy) if dd > EPS else (0.0, 0.0)

    def predict(self, b, ticks: float) -> tuple[float, float]:
        hx, hy = self.heading(b)
        st = speed(b.radius)
        return (b.pos[0] + hx * st * ticks, b.pos[1] + hy * st * ticks)


# ---------------------------------------------------------------------------
# Kill-envelope geometry.
# ---------------------------------------------------------------------------
def envelope_radius(threat, my_r: float, tr: Tracker, margin_mult: float, fresh: bool) -> float:
    """Distance inside which this threat can plausibly kill our blob of radius my_r.
    Closing-speed based: a bigger blob is a SLOWER blob — it cannot run us down,
    only lunge (if cooldown ready) or touch us. Only near-our-size threats chase."""
    pad = CONFIG["ENVELOPE_MARGIN"] * margin_mult
    r = 0.0
    if threat.radius >= my_r * EAT:
        r = threat.radius + my_r + 1.0  # contact kill is always live
        closing = speed(threat.radius) - speed(my_r)
        if closing > 0:  # it genuinely outruns us (near-size threat)
            r = max(r, threat.radius + my_r + closing * CONFIG["CHASE_HORIZON"] * 2)
    # split-lunge disc: halves must eat us, cooldown must be ready
    if (threat.radius / math.sqrt(2)) >= my_r * EAT and mass(threat.radius) >= 2 * CONFIG["SPLIT_MIN_MASS"]:
        if tr.can_split_now(threat.player_id) and not fresh:
            # while fresh we are expendable: lunges cost us ~nothing, don't paralyse
            r = max(r, CONFIG["SPLIT_REACH"] + my_r + threat.radius / math.sqrt(2))
    return (r + pad) if r > 0 else 0.0


def classify(game: Game, tr: Tracker):
    st = game.state
    me = st.me
    my_blobs = list(me.blobs.values())
    my_small = min((b.radius for b in my_blobs), default=me.radius)
    my_large = max((b.radius for b in my_blobs), default=me.radius)
    threats, prey = [], []
    for b in st.visible_blobs:
        if b.player_id == me.player_id:
            continue
        if b.radius >= my_small * CONFIG["SAFETY_RATIO"]:
            threats.append(b)
        elif my_large >= b.radius * EAT:
            prey.append(b)
    return my_blobs, my_small, my_large, threats, prey


# ---------------------------------------------------------------------------
# Direction scoring.
# ---------------------------------------------------------------------------
def score_directions(game: Game, tr: Tracker, threats, my_small, my_large,
                     margin_mult: float, risk_mult: float,
                     goal: tuple[float, float] | None, fleeing: bool = False):
    """Return list of (score, dirx, diry, vetoed). goal biases toward a point."""
    st = game.state
    cx, cy = st.me.x, st.me.y
    my_speed = speed(my_large)
    horizon = CONFIG["CHASE_HORIZON"]

    # precompute threat predicted positions + envelope radii
    env = []
    fresh = mass(my_large) < CONFIG["FRESH_MASS"]
    for t in threats:
        er = envelope_radius(t, my_small, tr, margin_mult, fresh)
        if er > 0:
            px, py = tr.predict(t, CONFIG["LEAD_TICKS"])
            env.append((px, py, er, t))

    results = []
    for dx, dy in DIRS:
        # our position now and at horizon along this direction
        hx, hy = cx + dx * my_speed * horizon, cy + dy * my_speed * horizon
        hx = min(max(hx, my_large), ARENA - my_large)
        hy = min(max(hy, my_large), ARENA - my_large)

        vetoed = False
        min_clear = 1e9
        for px, py, er, _t in env:
            for (qx, qy) in ((cx + dx * my_speed * 4, cy + dy * my_speed * 4), (hx, hy)):
                d = math.hypot(qx - px, qy - py)
                if d < er:
                    vetoed = True
                min_clear = min(min_clear, d - er)
        score = 0.0
        # openness: dominant when fleeing, whisper-level tiebreak otherwise
        if env:
            w_open = CONFIG["W_OPENNESS"] * risk_mult if fleeing else 0.35
            score += w_open * max(min(min_clear, 15.0), -5.0)
        # gain: food + viruses + loose prey in this direction (angular window)
        for f in st.visible_food:
            ux, uy, d = unit(f.pos[0] - cx, f.pos[1] - cy)
            if d > EPS and (ux * dx + uy * dy) > 0.8:
                score += CONFIG["W_FOOD"] / (d ** CONFIG["FOOD_FALLOFF"] + 0.5)
        can_eat_virus = mass(my_large) > CONFIG["VIRUS_CONSUME_MASS"]
        hunter_near = any(math.hypot(t.pos[0]-cx, t.pos[1]-cy) < CONFIG["VIRUS_FEAST_CLEAR"] for t in threats)
        if can_eat_virus and not hunter_near:
            for v in st.visible_viruses:
                ux, uy, d = unit(v.pos[0] - cx, v.pos[1] - cy)
                if d > EPS and (ux * dx + uy * dy) > 0.85:
                    score += CONFIG["W_VIRUS_FOOD"] / (d + 0.5)
        # wall cost
        wm = CONFIG["WALL_MARGIN"]
        wall_pen = 0.0
        for coord, dcomp in ((hx, None), (hy, None)):
            pass
        if hx < wm or ARENA - hx < wm:
            wall_pen += CONFIG["W_WALL"]
        if hy < wm or ARENA - hy < wm:
            wall_pen += CONFIG["W_WALL"]
        score -= wall_pen
        # goal bias (HUNT intercept point)
        if goal is not None:
            gx, gy, gd = unit(goal[0] - cx, goal[1] - cy)
            score += 14.0 * (gx * dx + gy * dy)
        results.append([score, dx, dy, vetoed])
    return results


def pick(results):
    safe = [r for r in results if not r[3]]
    pool = safe if safe else results  # all vetoed: least-bad anyway
    if not safe:
        pool = sorted(results, key=lambda r: -r[0])
    best = max(pool, key=lambda r: r[0])
    return best[1], best[2]


# ---------------------------------------------------------------------------
# HUNT: target selection, PN intercept, herding, lunge decision.
# ---------------------------------------------------------------------------
class Hunt:
    def __init__(self) -> None:
        self.target_key = None
        self.lock_ticks = 0

    def select(self, game, tr, prey, threats, my_large, total_mass):
        st = game.state
        cx, cy = st.me.x, st.me.y
        my_v = speed(my_large)
        best, best_score = None, 0.0
        for p in prey:
            val = mass(p.radius)
            if val < CONFIG["HUNT_VALUE_MIN"]:
                continue
            their_v = speed(p.radius)
            if my_v <= their_v + CONFIG["HUNT_FEAS_SPEED_EDGE"]:
                continue  # cannot close: infeasible chase, ignore
            d = math.hypot(p.pos[0] - cx, p.pos[1] - cy)
            t_int = d / max(my_v - their_v, 0.05)
            if t_int * my_v > CONFIG["HUNT_MAX_INTERCEPT"] * 3:
                continue
            s = val / (1.0 + t_int * 0.05)
            if s > best_score:
                best, best_score = p, s
        return best

    def intercept_point(self, game, tr, target, my_large):
        cx, cy = game.state.me.x, game.state.me.y
        hx, hy = tr.heading(target)
        tv = speed(target.radius)
        mv = speed(my_large)
        d = math.hypot(target.pos[0] - cx, target.pos[1] - cy)
        t_lead = d / max(mv, 0.05)
        ix = target.pos[0] + hx * tv * t_lead
        iy = target.pos[1] + hy * tv * t_lead
        # herding: bias aim to press target toward its nearest wall
        wx = 0.0 if target.pos[0] < ARENA / 2 else ARENA
        wy = 0.0 if target.pos[1] < ARENA / 2 else ARENA
        hbx, hby, _ = unit(wx - target.pos[0], wy - target.pos[1])
        ix -= hbx * CONFIG["HERD_WALL_BIAS"] * d
        iy -= hby * CONFIG["HERD_WALL_BIAS"] * d
        return (min(max(ix, 0.5), ARENA - 0.5), min(max(iy, 0.5), ARENA - 0.5))

    def should_lunge(self, game, tr, target, threats, my_blobs, my_large, total_mass, risk_mult):
        if total_mass > CONFIG["SPLIT_MAX_MASS"] * (2.0 - risk_mult):
            return False
        largest = my_large
        if mass(largest) < CONFIG["SPLIT_MIN_MASS"] * 2:
            return False
        if len(my_blobs) >= 4:
            return False
        half = largest / math.sqrt(2)
        if half < target.radius * CONFIG["SPLIT_SAFETY_RATIO"]:
            return False
        px, py = tr.predict(target, 6)
        d = math.hypot(px - game.state.me.x, py - game.state.me.y)
        if d > CONFIG["SPLIT_KILL_RANGE"]:
            return False
        for t in threats:
            if math.hypot(t.pos[0] - game.state.me.x, t.pos[1] - game.state.me.y) < CONFIG["SPLIT_CLEARANCE"]:
                return False
        return True


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------
def main() -> None:
    game = Game()
    tr = Tracker()
    hunt = Hunt()

    while True:
        query: QueryType = game.get_next_query()

        def choose(query: QueryType) -> MoveType:
            st = game.state
            me = st.me
            tr.read_intents(game)
            tr.update(st.visible_blobs, me.player_id)
            my_blobs, my_small, my_large, threats, prey = classify(game, tr)
            total_mass = sum(mass(b.radius) for b in my_blobs) or mass(me.radius)
            frac = st.round / max(st.max_rounds, 1)

            # risk appetite: >1 = more cautious
            risk_mult = 1.0 + total_mass / CONFIG["BANK_REF_MASS"]
            if frac > CONFIG["LATE_GAME_FRAC"]:
                risk_mult *= CONFIG["LATE_MARGIN_MULT"]
            if total_mass < CONFIG["FRESH_MASS"]:
                risk_mult *= CONFIG["FRESH_BOLD"]
            margin_mult = risk_mult

            # --- mode: FLEE only on GENUINE emergencies. A slower pursuer is
            # not an emergency — we outrun it and farm; the vetoes route us.
            fleeing = False
            cx, cy = me.x, me.y
            fresh_now = total_mass < CONFIG["FRESH_MASS"]
            for t in threats:
                d = math.hypot(t.pos[0] - cx, t.pos[1] - cy)
                # (a) contact-imminent
                if t.radius >= my_small * EAT and d < t.radius + my_small + CONFIG["PANIC_ENTER"]:
                    fleeing = True
                    break
                # (b) a threat that genuinely outruns us, inside its chase envelope
                if t.radius >= my_small * EAT and speed(t.radius) > speed(my_small) and \
                        d < envelope_radius(t, my_small, tr, margin_mult, fresh_now) + CONFIG["PANIC_ENTER"]:
                    fleeing = True
                    break
                # (c) lunge-ready split-killer standing inside its reach
                if not fresh_now and (t.radius / math.sqrt(2)) >= my_small * EAT \
                        and tr.can_split_now(t.player_id) and d < CONFIG["SPLIT_REACH"] + my_small:
                    fleeing = True
                    break
            # imminent hostile lunge aimed at us -> FLEE regardless of distance band
            for t in threats:
                if tr.intent_split.get(t.player_id) and (t.radius / math.sqrt(2)) >= my_small * EAT:
                    hx, hy = tr.heading(t)
                    ux, uy, d = unit(cx - t.pos[0], cy - t.pos[1])
                    if d < CONFIG["SPLIT_REACH"] * 1.3 and (hx * ux + hy * uy) > 0.5:
                        fleeing = True
                        break

            goal = None
            split = False
            if not fleeing:
                # --- HUNT: keep or acquire a committed target
                target = None
                if hunt.target_key is not None:
                    for p in prey:
                        if (p.player_id, p.blob_id) == hunt.target_key:
                            target = p
                            break
                if target is None or hunt.lock_ticks > CONFIG["HUNT_COMMIT_TICKS"] * 4:
                    target = hunt.select(game, tr, prey, threats, my_large, total_mass)
                    hunt.target_key = (target.player_id, target.blob_id) if target else None
                    hunt.lock_ticks = 0
                if target is not None:
                    hunt.lock_ticks += 1
                    goal = hunt.intercept_point(game, tr, target, my_large)
                    split = hunt.should_lunge(game, tr, target, threats, my_blobs,
                                              my_large, total_mass, risk_mult)
                else:
                    # FARM with commitment: beeline the best meal; vetoes keep it safe.
                    can_virus = mass(my_large) > CONFIG["VIRUS_CONSUME_MASS"]
                    clear = not any(math.hypot(t.pos[0]-cx, t.pos[1]-cy) < CONFIG["VIRUS_FEAST_CLEAR"]
                                    for t in threats)
                    if can_virus and clear and st.visible_viruses:
                        v = min(st.visible_viruses,
                                key=lambda v: (v.pos[0]-cx)**2 + (v.pos[1]-cy)**2)
                        goal = v.pos
                    elif st.visible_food:
                        f = min(st.visible_food,
                                key=lambda f: (f.pos[0]-cx)**2 + (f.pos[1]-cy)**2)
                        goal = f.pos

            results = score_directions(game, tr, threats, my_small, my_large,
                                       margin_mult, risk_mult, goal, fleeing)
            # ENCIRCLEMENT: if most directions are lethal, this IS an emergency —
            # rescore with openness dominant and no goal: find the gap in the ring.
            if not fleeing and sum(1 for r in results if r[3]) >= CONFIG["N_DIRS"] // 2:
                results = score_directions(game, tr, threats, my_small, my_large,
                                           margin_mult, risk_mult, None, True)
            dx, dy = pick(results)
            if abs(dx) < EPS and abs(dy) < EPS:
                dx, dy = ARENA / 2 - cx, ARENA / 2 - cy
                if abs(dx) < EPS and abs(dy) < EPS:
                    dx = 1.0
            return MovePlayer(player_id=me.player_id,
                              direction=DirectionModel(x=dx, y=dy),
                              split=split)

        try:
            move = choose(query)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            move = MovePlayer(player_id=game.state.me.player_id,
                              direction=DirectionModel(x=1.0, y=0.0), split=False)
        game.send_move(move)


if __name__ == "__main__":
    main()
