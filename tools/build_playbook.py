#!/usr/bin/env python3
"""build_playbook.py — offline Tier-1 playbook sweep (Chris 2026-07-16).

Solves two recurring set-pieces EXACTLY with the engine-faithful physics and
embeds packed tables into bots/omni_mixer_v3.py between PB_TABLE markers:

  SPLIT-KILL table: (our largest-blob mass M, target mass tm, distance d)
    -> minimum horizon (ticks, 1..15) at which a split-lunge LANDS on a
    dead-away-fleeing target, or 0 = never within 15. Same dynamics as
    _la_attack_lands (eject 1.6, drag 0.82, eat ratio 1.2, engine speed law).

  VIRUS-GUARD table: (our mass M, rival mass rm) -> minimum safe arrival-gap
    (ticks) such that popping a virus (scatter to pieces) before the rival
    arrives loses at most PB_MAX_PIECE_LOSS pieces. From a scatter-vacuum sim:
    pieces ring-scatter at eject speed, rival vacuums nearest pieces at its
    speed, pieces flee outward.

Usage: python3 tools/build_playbook.py [--check-only]
Regenerate any time; deterministic. Verifies 200 random cells vs direct sim.
"""
import base64, math, random, re, sys
from pathlib import Path

BODY = Path(__file__).resolve().parent.parent / "bots" / "omni_mixer_v3.py"

# engine-faithful constants (mirror _LA_* in the body — checked at insert time)
EJECT = 1.6; DRAG = 0.82; EAT = 1.2
BASE_SPEED = 1.1; SPD_FACTOR = 0.08; MIN_SPEED = 0.25

def speed(r):
    return max(MIN_SPEED, BASE_SPEED / (1.0 + SPD_FACTOR * r))   # ENGINE law (2026-07-16 fix)

def unit(dx, dy):
    m = math.hypot(dx, dy)
    return (dx / m, dy / m) if m > 1e-9 else (0.0, 0.0)

# ---- split-kill: exact 1D pursuit -------------------------------------------
# bucket edges (embedded verbatim into the body — MUST match runtime)
M_EDGES = [3 * (500 / 3) ** (i / 23) for i in range(24)]        # our mass, log
T_EDGES = [1 * (250 / 1) ** (i / 23) for i in range(24)]        # target mass, log
D_EDGES = [0.25 + 0.5 * i for i in range(28)]                    # distance

def split_lands(M, tm, d, horizon=15):
    cm = M / 2.0
    if cm <= tm * EAT:
        return 0
    cr = math.sqrt(cm)
    bx = by = 0.0; sx, sy = 1.0, 0.0
    tx, ty = d, 0.0
    cx, cy = bx + sx * (cr + cr), by + sy * (cr + cr)
    vx, vy = sx * EJECT, sy * EJECT
    tr = math.sqrt(tm); ts = speed(tr)
    for h in range(1, horizon + 1):
        fx, fy = unit(tx - bx, ty - by)
        tx += fx * ts; ty += fy * ts
        base = speed(cr)
        vx = vx * DRAG + sx * base * (1 - DRAG)
        vy = vy * DRAG + sy * base * (1 - DRAG)
        cx += vx; cy += vy
        if (cx - tx) ** 2 + (cy - ty) ** 2 <= cr * cr:
            return h
    return 0

# ---- virus-guard: scatter-vacuum sim -----------------------------------------
def pieces_lost(M, rm, gap, pieces=12, horizon=25):
    total = M + 2.25
    pm = total / pieces; pr = math.sqrt(pm)
    if rm < pm * EAT:
        return 0                       # rival cannot eat our pieces at all
    ps = speed(pr); rs = speed(math.sqrt(rm))
    pts = []
    for i in range(pieces):
        a = 2 * math.pi * i / pieces
        pts.append([math.cos(a) * 1.0, math.sin(a) * 1.0, math.cos(a), math.sin(a)])
    rx, ry = 12.0, 0.0                 # rival approaches from fixed range
    lost = 0
    for t in range(horizon):
        if t >= gap:                   # rival arrives 'gap' ticks after the pop
            alive = [p for p in pts if p is not None]
            if not alive:
                break
            tgt = min(alive, key=lambda p: (p[0]-rx)**2 + (p[1]-ry)**2)
            ux, uy = unit(tgt[0]-rx, tgt[1]-ry)
            rx += ux * rs; ry += uy * rs
            if (tgt[0]-rx)**2 + (tgt[1]-ry)**2 <= rm:   # ~ within rival radius^2
                pts[pts.index(tgt)] = None
                lost += 1
        for p in pts:
            if p is None: continue
            ax, ay = unit(p[0]-rx, p[1]-ry) if t >= gap else (p[2], p[3])
            p[0] += ax * ps; p[1] += ay * ps
    return lost

PB_MAX_PIECE_LOSS = 2

def build():
    # split table: 4 bits per cell (min horizon 1..15, 0 = never)
    cells = []
    for M in M_EDGES:
        for tm in T_EDGES:
            for d in D_EDGES:
                cells.append(min(15, split_lands(M, tm, d)))
    packed = bytearray()
    for i in range(0, len(cells), 2):
        lo = cells[i]
        hi = cells[i + 1] if i + 1 < len(cells) else 0
        packed.append(lo | (hi << 4))
    split_b64 = base64.b85encode(bytes(packed)).decode()

    # virus-guard: min gap (0..30, 31=never-safe) per (M, rm) bucket
    guard = []
    for M in M_EDGES:
        for rm in T_EDGES:
            g = 31
            for gap in range(0, 31):
                if pieces_lost(M, rm, gap) <= PB_MAX_PIECE_LOSS:
                    g = gap
                    break
            guard.append(g)
    guard_b64 = base64.b85encode(bytes(guard)).decode()
    return cells, split_b64, guard, guard_b64

def main():
    cells, split_b64, guard, guard_b64 = build()
    go = sum(1 for c in cells if c) / len(cells)
    print(f"split table: {len(cells)} cells, GO fraction {go:.2f}, packed {len(split_b64)} chars")
    print(f"guard table: {len(guard)} cells, packed {len(guard_b64)} chars")

    # self-check: 200 random cells decode-and-agree with direct sim
    rnd = random.Random(1)
    for _ in range(200):
        i, j, k = rnd.randrange(24), rnd.randrange(24), rnd.randrange(28)
        assert cells[(i * 24 + j) * 28 + k] == min(15, split_lands(M_EDGES[i], T_EDGES[j], D_EDGES[k]))
    print("self-check: 200 cells OK")
    if "--check-only" in sys.argv:
        return

    src = BODY.read_text()
    assert "_LA_EJECT = 1.6" in src and "_LA_DRAG = 0.82" in src, "LA constants moved — re-verify physics mirror"
    block = (
        "# PB_TABLE_BEGIN (auto-generated by tools/build_playbook.py — do not edit)\n"
        f"_PB_M_EDGES = {[round(x, 4) for x in M_EDGES]}\n"
        f"_PB_T_EDGES = {[round(x, 4) for x in T_EDGES]}\n"
        f"_PB_D_EDGES = {[round(x, 4) for x in D_EDGES]}\n"
        f'_PB_SPLIT_B85 = "{split_b64}"\n'
        f'_PB_GUARD_B85 = "{guard_b64}"\n'
        "import base64 as _pb_b64\n"
        "_PB_SPLIT = _pb_b64.b85decode(_PB_SPLIT_B85)\n"
        "_PB_GUARD = _pb_b64.b85decode(_PB_GUARD_B85)\n"
        "def _pb_bucket(v, edges):\n"
        "    lo, hi = 0, len(edges) - 1\n"
        "    if v <= edges[0]: return 0\n"
        "    if v >= edges[hi]: return hi\n"
        "    while hi - lo > 1:\n"
        "        mid = (lo + hi) // 2\n"
        "        if edges[mid] <= v: lo = mid\n"
        "        else: hi = mid\n"
        "    return lo\n"
        "def _pb_split_h(M, tm, d):\n"
        "    idx = (_pb_bucket(M, _PB_M_EDGES) * 24 + _pb_bucket(tm, _PB_T_EDGES)) * 28 + _pb_bucket(d, _PB_D_EDGES)\n"
        "    b = _PB_SPLIT[idx >> 1]\n"
        "    return (b >> 4) if (idx & 1) else (b & 15)\n"
        "def _pb_virus_guard(M, rm):\n"
        "    return _PB_GUARD[_pb_bucket(M, _PB_M_EDGES) * 24 + _pb_bucket(rm, _PB_T_EDGES)]\n"
        "# PB_TABLE_END\n"
    )
    if "# PB_TABLE_BEGIN" in src:
        src = re.sub(r"# PB_TABLE_BEGIN.*?# PB_TABLE_END\n", block, src, flags=re.S)
    else:
        src = src.replace("# ============ ROLLOUT PLANNER", block + "\n# ============ ROLLOUT PLANNER", 1)
    BODY.write_text(src)
    print(f"embedded into {BODY.name} ({len(block)} chars)")

if __name__ == "__main__":
    main()
