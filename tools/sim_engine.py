#!/usr/bin/env python3
"""sim_engine.py — the ONE authoritative transition function (planner v3).

Mirrors engine 2026.1.13 StateMutator.commit_round EXACTLY, verified against
the real mutator as oracle (run this file under the gym venv for the gate):

    ~/Developer/competition/evolution-2/.venv/bin/python3 tools/sim_engine.py

Engine order (state_mutator.py): commit events -> _apply_split per event ->
_move_blob per player blob -> _apply_mass_decay -> _stabilise -> _resolve_viruses
-> _stabilise -> _resolve_food -> _resolve_player_eating -> _stabilise ->
_respawn_dead_players -> food/virus respawn.

Known, deliberate divergences (documented, excluded from the gate):
  * dead players never respawn inside the sim (RESPAWN_DELAY_ROUNDS=30 >> H)
  * no food/virus respawn (random positions; entities only deplete)

World representation (plain dicts/lists, hand-cloned for speed):
  world = {
    'size': 60.0,
    'players': {pid: {'blobs': {bid: [x, y, r, cd, evx, evy]}, 'next_bid': int}},
    'foods':   [[fid, x, y], ...],
    'viruses': [[vid, x, y, r], ...],
  }
moves = {pid: (dx, dy, split_bool)}  (raw direction; we normalise like engine)
step() returns an events list for value accounting:
  ('eat', eater_pid, eaten_pid, mass_transferred)
  ('death', pid)
  ('virus', pid, mass_gain, pieces)
  ('food', pid, count)
"""
import math

EPS = 1e-4                      # SAME_PLAYER_OVERLAP_EPSILON
SPLIT_MIN_MASS = 2.0
SPLIT_CD = 18
EJECT_SPEED = 1.6
EJECT_DRAG = 0.82
DECAY = 0.002
MIN_MASS = 0.9 * 0.9            # STARTING_RADIUS*STARTING_RADIUS — NOT the
                                # literal 0.81: differs in the last bit and
                                # the engine compares at this exact boundary
EAT_RATIO = 1.2
FOOD_MASS = 0.15 * 0.15         # FOOD_RADIUS*FOOD_RADIUS (same: != 0.0225)
MERGE_ATTRACT = 0.08
MAX_BLOBS = 16
X, Y, R, CD, EVX, EVY = range(6)


def speed_of(r):
    return max(0.25, 1.1 / (1.0 + 0.08 * r))


def normalise(dx, dy):
    m = max(abs(dx), abs(dy))
    if not math.isfinite(m) or m == 0.0:
        return (0.0, 0.0)
    sx, sy = dx / m, dy / m
    mag = math.hypot(sx, sy)
    return (sx / mag, sy / mag)


def clone(world):
    return {
        'size': world['size'],
        'players': {
            pid: {'blobs': {bid: b[:] for bid, b in p['blobs'].items()},
                  'next_bid': p['next_bid']}
            for pid, p in world['players'].items()
        },
        'foods': [f[:] for f in world['foods']],
        'viruses': [v[:] for v in world['viruses']],
    }


def total_mass(player):
    return sum(b[R] * b[R] for b in player['blobs'].values())


def _clamp(b, size):
    b[X] = min(max(b[R], b[X]), size - b[R])
    b[Y] = min(max(b[R], b[Y]), size - b[R])


def _next_bid(player):
    bid = player['next_bid']
    while bid in player['blobs']:
        bid += 1
    player['next_bid'] = bid + 1
    return bid


def _apply_split(world, pid, dx, dy):
    p = world['players'][pid]
    if not p['blobs']:
        return
    ux, uy = normalise(dx, dy)
    if ux == 0.0 and uy == 0.0:
        sx, sy, launch = 1.0, 0.0, 0.0
    else:
        sx, sy, launch = ux, uy, 1.0
    size = world['size']
    for bid in sorted(p['blobs']):
        if len(p['blobs']) >= MAX_BLOBS:
            break
        b = p['blobs'].get(bid)
        if b is None or b[R] * b[R] < SPLIT_MIN_MASS:
            continue
        child_r = math.sqrt(b[R] * b[R] / 2.0)
        b[R] = child_r
        b[CD] = SPLIT_CD
        cid = _next_bid(p)
        child = [b[X] + sx * (child_r + child_r + EPS),
                 b[Y] + sy * (child_r + child_r + EPS),
                 child_r, SPLIT_CD,
                 sx * EJECT_SPEED * launch, sy * EJECT_SPEED * launch]
        _clamp(child, size)
        p['blobs'][cid] = child


def _move_all(world, pid, dx, dy):
    ux, uy = normalise(dx, dy)
    size = world['size']
    for b in world['players'][pid]['blobs'].values():
        if ux != 0.0 or uy != 0.0:
            s = speed_of(b[R])
            b[X] += ux * s
            b[Y] += uy * s
        b[X] += b[EVX]
        b[Y] += b[EVY]
        b[EVX] *= EJECT_DRAG
        b[EVY] *= EJECT_DRAG
        if abs(b[EVX]) < 1e-4:
            b[EVX] = 0.0
        if abs(b[EVY]) < 1e-4:
            b[EVY] = 0.0
        b[CD] = max(0, b[CD] - 1)
        _clamp(b, size)


def _decay(world):
    for p in world['players'].values():
        for b in p['blobs'].values():
            m = b[R] * b[R]
            if m <= MIN_MASS:
                continue
            m *= (1.0 - DECAY)
            if m < MIN_MASS:
                m = MIN_MASS
            b[R] = math.sqrt(m)


def _attract(world):
    size = world['size']
    for p in world['players'].values():
        if len(p['blobs']) <= 1:
            continue
        tm = total_mass(p)
        if tm == 0:
            continue
        # bit-exact: engine does blob.x * blob.mass, i.e. x * (r*r)
        cx = sum(b[X] * (b[R] * b[R]) for b in p['blobs'].values()) / tm
        cy = sum(b[Y] * (b[R] * b[R]) for b in p['blobs'].values()) / tm
        for b in p['blobs'].values():
            dx, dy = cx - b[X], cy - b[Y]
            d = math.hypot(dx, dy)
            if d == 0:
                continue
            step = min(MERGE_ATTRACT, d)
            b[X] += dx / d * step
            b[Y] += dy / d * step
            _clamp(b, size)


def _merge_once(world):
    size = world['size']
    for p in world['players'].values():
        blobs = p['blobs']
        ids = sorted(blobs)
        for i, ia in enumerate(ids):
            a = blobs[ia]
            for ib in ids[i + 1:]:
                bb = blobs[ib]
                if a[CD] > 0 or bb[CD] > 0:
                    continue
                d = math.hypot(bb[X] - a[X], bb[Y] - a[Y])
                if d > a[R] + bb[R] + EPS:
                    continue
                # survivor: bigger mass, tie -> lower blob_id
                (sid, s), (cid, c) = sorted(
                    ((ia, a), (ib, bb)),
                    key=lambda t: (-t[1][R] * t[1][R], t[0]))
                ms, mc = s[R] * s[R], c[R] * c[R]
                cm = ms + mc
                s[X] = (s[X] * ms + c[X] * mc) / cm
                s[Y] = (s[Y] * ms + c[Y] * mc) / cm
                s[EVX] = (s[EVX] * ms + c[EVX] * mc) / cm
                s[EVY] = (s[EVY] * ms + c[EVY] * mc) / cm
                s[R] = math.sqrt(cm)
                s[CD] = 0
                del blobs[cid]
                _clamp(s, size)
                return True
    return False


def _separate(world, iterations=4):
    size = world['size']
    for _ in range(iterations):
        changed = False
        for p in world['players'].values():
            blobs = p['blobs']
            ids = sorted(blobs)
            for i, ia in enumerate(ids):
                a = blobs.get(ia)
                if a is None:
                    continue
                for ib in ids[i + 1:]:
                    bb = blobs.get(ib)
                    if bb is None:
                        continue
                    dx, dy = bb[X] - a[X], bb[Y] - a[Y]
                    d = math.hypot(dx, dy)
                    mind = a[R] + bb[R] + EPS
                    if d >= mind:
                        continue
                    if d == 0:
                        nx, ny = (1.0, 0.0) if ia < ib else (0.0, 1.0)
                    else:
                        nx, ny = dx / d, dy / d
                    ov = mind - d
                    ma, mb = a[R] * a[R], bb[R] * bb[R]
                    tm = ma + mb
                    # bit-exact: engine precomputes move_a/move_b then nx*move
                    move_a = ov * (mb / tm)
                    move_b = ov * (ma / tm)
                    a[X] -= nx * move_a
                    a[Y] -= ny * move_a
                    bb[X] += nx * move_b
                    bb[Y] += ny * move_b
                    _clamp(a, size)
                    _clamp(bb, size)
                    changed = True
        if not changed:
            break


def _stabilise(world):
    _attract(world)
    while _merge_once(world):
        pass
    _separate(world)
    while _merge_once(world):
        pass
    _separate(world)


def _living_sorted(world):
    out = [(pid, bid, b)
           for pid, p in world['players'].items()
           for bid, b in p['blobs'].items()]
    out.sort(key=lambda t: (-t[2][R], t[0], t[1]))
    return out


def _resolve_viruses(world, events):
    size = world['size']
    remaining = []
    for v in world['viruses']:
        vid, vx, vy, vr = v
        cands = [(pid, bid, b) for pid, bid, b in _living_sorted(world)
                 if (b[X] - vx) ** 2 + (b[Y] - vy) ** 2 <= b[R] * b[R]
                 and b[R] * b[R] > vr * vr * EAT_RATIO]
        if not cands:
            remaining.append(v)
            continue
        pid, bid, b = min(cands, key=lambda t: (-t[2][R], t[0], t[1]))
        p = world['players'][pid]
        total = b[R] * b[R] + vr * vr
        pieces = max(1, MAX_BLOBS - len(p['blobs']) + 1)
        events.append(('virus', pid, vr * vr, pieces))
        if pieces <= 1:
            b[R] = math.sqrt(total)
            _clamp(b, size)
            continue
        pr = math.sqrt(total / pieces)
        cols = math.ceil(math.sqrt(pieces))
        spacing = pr * 2.0 + EPS
        x_off = (cols - 1) * spacing / 2.0
        y_off = (math.ceil(pieces / cols) - 1) * spacing / 2.0
        cx, cy = b[X], b[Y]
        for idx in range(pieces):
            px = cx + (idx % cols) * spacing - x_off
            py = cy + (idx // cols) * spacing - y_off
            if idx == 0:
                tb = b
            else:
                tb = [0.0, 0.0, 0.0, 0, 0.0, 0.0]
                p['blobs'][_next_bid(p)] = tb
            tb[X], tb[Y], tb[R] = px, py, pr
            tb[EVX] = tb[EVY] = 0.0
            tb[CD] = SPLIT_CD
            _clamp(tb, size)
    world['viruses'] = remaining


def _resolve_food(world, events):
    size = world['size']
    living = _living_sorted(world)   # built once; winner re-keyed on live radius
    remaining = []
    counts = {}
    for f in world['foods']:
        fid, fx, fy = f
        cands = [(pid, bid, b) for pid, bid, b in living
                 if (b[X] - fx) ** 2 + (b[Y] - fy) ** 2 <= b[R] * b[R]]
        if not cands:
            remaining.append(f)
            continue
        pid, bid, b = min(cands, key=lambda t: (-t[2][R], t[0], t[1]))
        b[R] = math.sqrt(b[R] * b[R] + FOOD_MASS)
        _clamp(b, size)
        counts[pid] = counts.get(pid, 0) + 1
    world['foods'] = remaining
    for pid, n in counts.items():
        events.append(('food', pid, n))


def _resolve_eating(world, events):
    size = world['size']
    changed = True
    while changed:
        changed = False
        living = _living_sorted(world)
        for epid, ebid, eb in living:
            if eb is not world['players'][epid]['blobs'].get(ebid):
                continue
            for tpid, tbid, tb in living:
                if epid == tpid:
                    continue
                cur = world['players'][tpid]['blobs'].get(tbid)
                if cur is None or cur is not tb:
                    continue
                if eb[R] * eb[R] < tb[R] * tb[R] * EAT_RATIO:
                    continue
                if (eb[X] - tb[X]) ** 2 + (eb[Y] - tb[Y]) ** 2 > eb[R] * eb[R]:
                    continue
                events.append(('eat', epid, tpid, tb[R] * tb[R]))
                eb[R] = math.sqrt(eb[R] * eb[R] + tb[R] * tb[R])
                _clamp(eb, size)
                del world['players'][tpid]['blobs'][tbid]
                if not world['players'][tpid]['blobs']:
                    events.append(('death', tpid))
                changed = True
                break
            if changed:
                break


def step(world, moves):
    """Advance world one round IN PLACE. moves={pid:(dx,dy,split)}. Returns events."""
    events = []
    order = list(moves.keys())
    for pid in order:
        dx, dy, split = moves[pid]
        if split and world['players'][pid]['blobs']:
            _apply_split(world, pid, dx, dy)
    for pid in order:
        if not world['players'][pid]['blobs']:
            continue
        dx, dy, _ = moves[pid]
        _move_all(world, pid, dx, dy)
    _decay(world)
    _stabilise(world)
    _resolve_viruses(world, events)
    _stabilise(world)
    _resolve_food(world, events)
    _resolve_eating(world, events)
    _stabilise(world)
    return events


# ---------------------------------------------------------------------------
# Differential gate vs the REAL engine mutator (oracle). Gym venv only.
# ---------------------------------------------------------------------------

def _gate(n_scenarios=300, rounds_each=12, seed=20260717):
    import random as _rnd
    from engine.state.game_state import GameState
    from engine.state.player_state import PlayerState
    from engine.state.blob_state import BlobState
    from engine.state.state_mutator import StateMutator
    from lib.interact.map import Map
    from lib.models.food_model import FoodModel
    from lib.models.virus_model import VirusModel
    from lib.interface.events.moves.move_player import MovePlayer
    from lib.models.penguin_model import DirectionModel

    rnd = _rnd.Random(seed)
    mismatches = 0
    checked = 0
    for sc in range(n_scenarios):
        # random initial world -----------------------------------------
        gs = GameState.__new__(GameState)
        gs.round = 0
        gs.max_rounds = 1400
        gs.players = {}
        gs.map = Map()
        gs.event_history = []
        gs.private_event_history = []
        gs.turn_order = []
        world = {'size': 60.0, 'players': {}, 'foods': [], 'viruses': []}
        for pid in range(8):
            ps = PlayerState.__new__(PlayerState)
            ps.id = pid
            ps.team_id = pid
            ps.blobs = {}
            ps._next_blob_id = 0
            ps.round_died = -1
            ps.respawn_at_round = None
            nb = rnd.choice([1, 1, 1, 2, 3, 5])
            cxy = (rnd.uniform(3, 57), rnd.uniform(3, 57))
            for bid in range(nb):
                r = rnd.uniform(0.9, 7.0) if nb == 1 else rnd.uniform(0.9, 4.0)
                x = min(max(cxy[0] + rnd.uniform(-4, 4), r), 60 - r)
                y = min(max(cxy[1] + rnd.uniform(-4, 4), r), 60 - r)
                cd = rnd.choice([0, 0, 0, 3, 10, 18])
                evx = rnd.choice([0.0, 0.0, rnd.uniform(-1.6, 1.6)])
                evy = rnd.choice([0.0, 0.0, rnd.uniform(-1.6, 1.6)])
                ps.blobs[bid] = BlobState(blob_id=bid, x=x, y=y, radius=r,
                                          merge_cooldown=cd,
                                          eject_vx=evx, eject_vy=evy)
                world['players'][pid] = world['players'].get(
                    pid, {'blobs': {}, 'next_bid': nb})
                world['players'][pid]['blobs'][bid] = [x, y, r, cd, evx, evy]
            ps._next_blob_id = nb
            gs.players[pid] = ps
        for fid in range(160):
            fx, fy = rnd.uniform(0, 60), rnd.uniform(0, 60)
            gs.map.foods.append(FoodModel(food_id=fid, pos=(fx, fy)))
            world['foods'].append([fid, fx, fy])
        gs.map._next_food_id = 160
        for vid in range(6):
            vx, vy = rnd.uniform(2, 58), rnd.uniform(2, 58)
            gs.map.viruses.append(VirusModel(virus_id=vid, pos=(vx, vy), radius=1.5))
            world['viruses'].append([vid, vx, vy, 1.5])
        gs.map._next_virus_id = 6

        mut = StateMutator(gs)
        # silence respawn + food/virus respawn randomness: monkeypatch
        mut._respawn_dead_players = lambda: None
        gs._ensure_food_count = lambda: []
        gs._ensure_virus_count = lambda: []

        for rd in range(rounds_each):
            moves = {}
            evs = []
            for pid in range(8):
                if not gs.players[pid].alive:
                    continue
                a = rnd.uniform(0, 2 * math.pi)
                dx, dy = math.cos(a), math.sin(a)
                if rnd.random() < 0.1:
                    dx = dy = 0.0
                split = rnd.random() < 0.15
                moves[pid] = (dx, dy, split)
                evs.append(MovePlayer(player_id=pid,
                                      direction=DirectionModel(x=dx, y=dy),
                                      split=split))
            gs.round = rd
            mut.commit_round(evs)
            step(world, moves)
            checked += 1
            # compare -------------------------------------------------
            bad = []
            for pid in range(8):
                eng = gs.players[pid].blobs
                sim = world['players'][pid]['blobs']
                if set(eng) != set(sim):
                    bad.append((pid, 'blobset', sorted(eng), sorted(sim)))
                    continue
                for bid, b in eng.items():
                    s = sim[bid]
                    if (abs(b.x - s[X]) > 1e-9 or abs(b.y - s[Y]) > 1e-9
                            or abs(b.radius - s[R]) > 1e-9
                            or b.merge_cooldown != s[CD]
                            or abs(b.eject_vx - s[EVX]) > 1e-9
                            or abs(b.eject_vy - s[EVY]) > 1e-9):
                        bad.append((pid, bid,
                                    (b.x, b.y, b.radius, b.merge_cooldown,
                                     b.eject_vx, b.eject_vy), tuple(s)))
            ef = {f.food_id for f in gs.map.foods}
            sf = {f[0] for f in world['foods']}
            if ef != sf:
                bad.append(('foods', sorted(ef ^ sf)[:8]))
            evv = {v.virus_id for v in gs.map.viruses}
            svv = {v[0] for v in world['viruses']}
            if evv != svv:
                bad.append(('viruses', sorted(evv ^ svv)))
            if bad:
                mismatches += 1
                if mismatches <= 5:
                    print(f"MISMATCH scenario {sc} round {rd}: {bad[:3]}")
    print(f"DIFFERENTIAL GATE: {checked} rounds checked, {mismatches} mismatches")
    return mismatches


if __name__ == '__main__':
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    bad = _gate(n_scenarios=n)
    sys.exit(1 if bad else 0)
