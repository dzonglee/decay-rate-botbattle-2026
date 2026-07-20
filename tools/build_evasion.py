#!/usr/bin/env python3
"""build_evasion.py — SOLVED two-sided pursuit/evasion vs walls (Tier-1 v2).

Minimax value iteration (we move, then the pursuer replies ADVERSARIALLY)
over a corner-quadrant frame. This is what runtime cannot compute: the
opponent here plays optimally — including adversarially-timed split strikes —
not the dead-away flee assumed by the runtime lookahead.

State (quadrant frame, walls at x=0 and y=0):
  wx, wy   our distance to each wall      7 buckets each
  dx, dy   pursuer offset from us         9 buckets each (can be negative)
  cls      threat class: 0 = body can eat us, piece cannot (mid)
                         1 = body AND split-piece can eat us (big)
  sp       pursuer still holds a split    0/1
Actions: 8 compass headings (frame-absolute). Pursuer reply: 8 headings,
minimising our value; if sp=1, cls=1 and distance <= SPLIT_REACH the strike
captures immediately (worst case). Value = expected survival ticks over
horizon H. Policy table = argmax action per state, 4 bits each.

Output: packed table + frame-mapping helpers embedded into the body between
EV_TABLE markers. Deterministic; self-checks sampled states.
"""
import base64, math, re, sys
from pathlib import Path

BODY = Path(__file__).resolve().parent.parent / "bots" / "omni_mixer_v3.py"

WX = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0]
DX = [-8.0, -5.0, -3.0, -1.5, 0.0, 1.5, 3.0, 5.0, 8.0]
H = 25
OUR_SPEED = 0.948           # engine law 1.1/(1+0.08r), r=2
PUR_SPEED = {0: 0.887, 1: 0.743} # engine law: r~3 mid, r~6 big (2026-07-16 fix)
CAP_R = {0: 2.2, 1: 3.5}    # capture radius (pursuer body)
SPLIT_REACH = 6.0           # adversarial split-strike kill ring (cls=1 only)
DIRS = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]]

def bucket(v, edges):
    lo, hi = 0, len(edges) - 1
    if v <= edges[0]: return 0
    if v >= edges[hi]: return hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if edges[mid] <= v: lo = mid
        else: hi = mid
    return lo

NW, ND = len(WX), len(DX)
NSTATE = NW * NW * ND * ND * 2 * 2

def sidx(iwx, iwy, idx, idy, cls, sp):
    return ((((iwx * NW + iwy) * ND + idx) * ND + idy) * 2 + cls) * 2 + sp

def step_state(iwx, iwy, idx, idy, cls, sp, a, p):
    """our action a, pursuer reply p -> next state or None if captured."""
    wx, wy = WX[iwx], WX[iwy]
    dx, dy = DX[idx], DX[idy]
    ax, ay = DIRS[a]
    nwx = max(0.0, wx + ax * OUR_SPEED)
    nwy = max(0.0, wy + ay * OUR_SPEED)
    ps = PUR_SPEED[cls]
    px, py = DIRS[p]
    # pursuer absolute delta relative to our new position
    ndx = dx + px * ps - ax * OUR_SPEED
    ndy = dy + py * ps - ay * OUR_SPEED
    d = math.hypot(ndx, ndy)
    if d <= CAP_R[cls]:
        return None
    if sp and cls == 1 and d <= SPLIT_REACH:
        return None                     # adversarial split strike lands
    return (bucket(nwx, WX), bucket(nwy, WX), bucket(ndx, DX), bucket(ndy, DX), cls, sp)

def solve():
    V = [0.0] * NSTATE
    pol = [0] * NSTATE
    for it in range(H):
        NV = [0.0] * NSTATE
        for iwx in range(NW):
            for iwy in range(NW):
                for idx in range(ND):
                    for idy in range(ND):
                        for cls in (0, 1):
                            for sp in (0, 1):
                                # tie-break prior: flee the pursuer (prevents the
                                # a=0 '+x' bias in hopeless/tied regions that made
                                # the v1 table LOSE to dead-away in the harness)
                                dx0, dy0 = DX[idx], DX[idy]
                                def _prior(k):
                                    s = -(DIRS[k][0]*dx0 + DIRS[k][1]*dy0)
                                    if WX[iwx] < 1.5 and DIRS[k][0] < -0.3: s -= 50.0
                                    if WX[iwy] < 1.5 and DIRS[k][1] < -0.3: s -= 50.0
                                    return s
                                fa = max(range(8), key=_prior)
                                best, barg = -1.0, fa
                                for a in [fa] + [k for k in range(8) if k != fa]:
                                    worst = 1e18
                                    for p in range(8):
                                        ns = step_state(iwx, iwy, idx, idy, cls, sp, a, p)
                                        val = 0.0 if ns is None else 1.0 + V[sidx(*ns)]
                                        if val < worst:
                                            worst = val
                                            if worst <= best:
                                                break
                                    if worst > best + 1e-9:
                                        best, barg = worst, a
                                i = sidx(iwx, iwy, idx, idy, cls, sp)
                                NV[i] = best
                                pol[i] = barg
        V = NV
        print(f"  VI iter {it+1}/{H}  mean survival {sum(V)/len(V):.2f}", flush=True)
    return V, pol

def main():
    print(f"solving {NSTATE} states x 8x8 actions, horizon {H} ...")
    V, pol = solve()
    packed = bytearray()
    for i in range(0, len(pol), 2):
        packed.append(pol[i] | ((pol[i + 1] if i + 1 < len(pol) else 0) << 4))
    b85 = base64.b85encode(bytes(packed)).decode()
    print(f"policy table: {NSTATE} states -> {len(b85)} chars packed")

    # sanity: cornered against x-wall with big pursuer inland must NOT run into the wall
    i = sidx(0, 3, bucket(3.0, DX), bucket(0.0, DX), 1, 0)   # wall left, pursuer inland-right
    a = pol[i]
    print(f"sanity: wall-left, pursuer-right -> heading {a} ({DIRS[a][0]:+.2f},{DIRS[a][1]:+.2f})")
    assert DIRS[a][0] >= -0.01, "policy runs into the wall"
    if "--check-only" in sys.argv:
        return

    block = (
        "# EV_TABLE_BEGIN (auto-generated by tools/build_evasion.py — do not edit)\n"
        "# Solved minimax pursuit/evasion vs walls (adversarial pursuer incl. split\n"
        "# strikes). States: (wall_dx, wall_dy, pursuer dx, dy, class, split) ->\n"
        "# optimal escape heading (frame-absolute, 8 compass dirs).\n"
        f"_EV_WX = {WX}\n"
        f"_EV_DX = {DX}\n"
        f'_EV_B85 = "{b85}"\n'
        "import base64 as _ev_b64\n"
        "_EV_POL = _ev_b64.b85decode(_EV_B85)\n"
        "_EV_DIRS = [(math.cos(_a), math.sin(_a)) for _a in [_i * math.pi / 4 for _i in range(8)]]\n"
        "def _ev_bucket(v, edges):\n"
        "    lo, hi = 0, len(edges) - 1\n"
        "    if v <= edges[0]: return 0\n"
        "    if v >= edges[hi]: return hi\n"
        "    while hi - lo > 1:\n"
        "        mid = (lo + hi) // 2\n"
        "        if edges[mid] <= v: lo = mid\n"
        "        else: hi = mid\n"
        "    return lo\n"
        "def _ev_lookup(wx, wy, dx, dy, cls, sp):\n"
        "    i = ((((_ev_bucket(wx, _EV_WX) * 7 + _ev_bucket(wy, _EV_WX)) * 9 + _ev_bucket(dx, _EV_DX)) * 9\n"
        "          + _ev_bucket(dy, _EV_DX)) * 2 + cls) * 2 + sp\n"
        "    b = _EV_POL[i >> 1]\n"
        "    return (b >> 4) if (i & 1) else (b & 7)\n"
        "# EV_TABLE_END\n"
    )
    src = BODY.read_text()
    if "# EV_TABLE_BEGIN" in src:
        src = re.sub(r"# EV_TABLE_BEGIN.*?# EV_TABLE_END\n", block, src, flags=re.S)
    else:
        src = src.replace("# PB_TABLE_BEGIN", block + "\n# PB_TABLE_BEGIN", 1)
    BODY.write_text(src)
    print(f"embedded EV table into {BODY.name}")

if __name__ == "__main__":
    main()
