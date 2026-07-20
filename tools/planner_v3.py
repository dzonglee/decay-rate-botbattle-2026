#!/usr/bin/env python3
"""planner_v3.py — receding-horizon planner per PLANNER_REDESIGN.md (2026-07-17).

SHADOW-ONLY: this module never ships in the body. It plans OVER the production
policy itself:

  * continuation = the body's real `_reactive_core` (not a toy surrogate)
  * transition   = tools/sim_engine.step (differential-tested bit-exact vs
                   engine 2026.1.13: 7200/7200 rounds, 0 mismatches)
  * opponents    = 4-member scenario ensemble (continue / pursue+flee /
                   intercept+flee / split-strike+flee)
  * acceptance   = worst-case (CVaR over ensemble) must not degrade AND
                   advantage LCB > 0; then argmax mean among qualifiers;
                   selected action returned STRUCTURALLY UNCHANGED

Smoke: evolution-2/.venv/bin/python3 tools/planner_v3.py  (or system py3)
"""
import math
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import equiv_test as ET
import sim_engine as SE

BODY = str(TOOLS.parent / "bots" / "omni_mixer_v3.py")
_m = None


def body():
    global _m
    if _m is None:
        _m = ET.load(BODY, "pv3body")
    return _m


# ---------------------------------------------------------------------------
# View adapter: sim world -> duck-typed game the body accepts
# (engine vision law: box of size 20*max(sum_radii/12,1)^0.4 around the
#  player centroid, view center clamped to arena; food by point,
#  blobs/viruses by circle-overlap)
# ---------------------------------------------------------------------------

def _vision(world, pid):
    p = world['players'][pid]
    sr = sum(b[SE.R] for b in p['blobs'].values())
    if sr <= 0:
        vs = 20.0
    else:
        vs = 20.0 * math.pow(max(sr / 12.0, 1.0), 0.4)
    tm = SE.total_mass(p)
    if tm > 0:
        cx = sum(b[SE.X] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / tm
        cy = sum(b[SE.Y] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / tm
    else:
        cx = cy = world['size'] / 2
    vsz = min(vs, world['size'])
    hv = vsz / 2
    vx = min(max(cx, hv), world['size'] - hv)
    vy = min(max(cy, hv), world['size'] - hv)
    return vx, vy, vs, (cx, cy), tm


def _sees_point(vx, vy, vs, x, y):
    h = vs / 2
    return abs(x - vx) <= h and abs(y - vy) <= h


def _sees_circle(vx, vy, vs, x, y, r):
    h = vs / 2
    dxo = max(abs(x - vx) - h, 0.0)
    dyo = max(abs(y - vy) - h, 0.0)
    return dxo * dxo + dyo * dyo <= r * r


def make_view(world, pid, last_moves=None):
    """Duck-typed game object for `_reactive_core`, censored per engine vision."""
    p = world['players'][pid]
    vx, vy, vs, (cx, cy), tm = _vision(world, pid)
    myblobs = {bid: ET.MMyBlob(b[SE.R], bid, (b[SE.X], b[SE.Y]))
               for bid, b in p['blobs'].items()}
    st = ET.MState()
    st.me = ET.MMe(pid, cx, cy, myblobs) if myblobs else ET.MMe(pid, cx, cy, {
        0: ET.MMyBlob(0.9, 0, (cx, cy))})
    st.me.radius = math.sqrt(tm) if tm > 0 else 0.9
    vis = []
    for opid, op in world['players'].items():
        if opid == pid:
            continue
        for bid in sorted(op['blobs']):
            b = op['blobs'][bid]
            if _sees_circle(vx, vy, vs, b[SE.X], b[SE.Y], b[SE.R]):
                mb = ET.MBlob(opid, bid, (b[SE.X], b[SE.Y]), b[SE.R], cd=b[SE.CD])
                vis.append(mb)
    st.visible_blobs = vis
    st.visible_food = [ET.MFood((f[1], f[2])) for f in world['foods']
                       if _sees_point(vx, vy, vs, f[1], f[2])]
    st.visible_viruses = [ET.MVirus((v[1], v[2]), v[3]) for v in world['viruses']
                          if _sees_circle(vx, vy, vs, v[1], v[2], v[3])]
    st.rankings = sorted(world['players'],
                         key=lambda q: -SE.total_mass(world['players'][q]))
    evs = []
    if last_moves:
        for opid, (dx, dy, sp) in last_moves.items():
            if opid == pid:
                continue
            evs.append(ET.MEvent("move_player", pid=opid,
                                 direction=ET.MDir(dx, dy), split=sp))
    st.event_history = evs
    st.new_events = 0
    return ET.MGame(st)


def clone_tracker(tr):
    m = body()
    c = m.Tracker()
    for k, v in vars(tr).items():
        if isinstance(v, dict):
            setattr(c, k, dict(v))
        elif isinstance(v, list):
            setattr(c, k, list(v))
        else:
            setattr(c, k, v)
    return c


class HuntClone:
    __slots__ = ("key", "ticks")

    def __init__(self, src=None):
        self.key = getattr(src, "key", None)
        self.ticks = getattr(src, "ticks", 0)


# ---------------------------------------------------------------------------
# Opponent scenario ensemble
# ---------------------------------------------------------------------------
SCENARIOS = ("continue", "pursue", "intercept", "split_strike")


def _opp_move(world, opid, pid, scenario, tracker, t):
    """Cheap opponent policy. Threat = heavier than us; prey = lighter."""
    op = world['players'][opid]
    if not op['blobs']:
        return (0.0, 0.0, False)
    p = world['players'][pid]
    om = SE.total_mass(op)
    mm = SE.total_mass(p)
    ox = sum(b[SE.X] * (b[SE.R] * b[SE.R]) for b in op['blobs'].values()) / om
    oy = sum(b[SE.Y] * (b[SE.R] * b[SE.R]) for b in op['blobs'].values()) / om
    if mm <= 0:
        return _cont_dir(tracker, opid)
    ux = sum(b[SE.X] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / mm
    uy = sum(b[SE.Y] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / mm
    dx, dy = ux - ox, uy - oy
    d = math.hypot(dx, dy) or 1e-9
    threat = om > mm * 1.1
    if scenario == "continue":
        return _cont_dir(tracker, opid)
    if threat:
        if scenario == "pursue":
            return (dx / d, dy / d, False)
        if scenario == "intercept":
            # aim at our projected position ~4 ticks ahead
            v = tracker.velocity.get((pid, 0), (0.0, 0.0)) if tracker else (0.0, 0.0)
            tx, ty = ux + v[0] * 4, uy + v[1] * 4
            idx, idy = tx - ox, ty - oy
            idd = math.hypot(idx, idy) or 1e-9
            return (idx / idd, idy / idd, False)
        # split_strike: pursue; split the moment a half can still kill and reach
        big = max(b[SE.R] * b[SE.R] for b in op['blobs'].values())
        small = min((b[SE.R] * b[SE.R] for b in p['blobs'].values()), default=0.0)
        can_kill = big / 2.0 >= small * 1.2
        reach = math.sqrt(big / 2.0) + 4.5
        return (dx / d, dy / d, bool(can_kill and d < reach and big >= 2.0))
    # prey: flee in every non-continue scenario
    return (-dx / d, -dy / d, False)


def _cont_dir(tracker, opid):
    if tracker is not None:
        v = tracker.intent_dir.get(opid)
        if v:
            return (v[0], v[1], False)
    return (0.0, 0.0, False)


# ---------------------------------------------------------------------------
# Rollout: candidate at t=0, production policy continuation after
# ---------------------------------------------------------------------------

def rollout(world0, pid, action0, scenario, tracker0, hunt0, H=12):
    world = SE.clone(world0)
    tr = clone_tracker(tracker0)
    hunt = HuntClone(hunt0)
    m = body()
    m0 = SE.total_mass(world['players'][pid])
    died_at = None
    ate = 0.0
    last_moves = {}
    for t in range(H):
        if not world['players'][pid]['blobs']:
            died_at = died_at if died_at is not None else t
            break
        moves = {}
        for opid in world['players']:
            if opid == pid or not world['players'][opid]['blobs']:
                continue
            moves[opid] = _opp_move(world, opid, pid, scenario, tr, t)
        if t == 0:
            moves[pid] = action0
        else:
            view = make_view(world, pid, last_moves)
            fx, fy, sp = m._reactive_core(view, tr, hunt)[:3]
            moves[pid] = (fx, fy, sp)
        events = SE.step(world, moves)
        last_moves = moves
        for ev in events:
            if ev[0] == 'death' and ev[1] == pid and died_at is None:
                died_at = t
            elif ev[0] == 'eat' and ev[1] == pid:
                ate += ev[3]
    mf = SE.total_mass(world['players'][pid])
    return {'final': mf, 'delta': mf - m0, 'died': died_at is not None,
            'died_at': died_at, 'ate': ate}


def _value(res):
    # death dominates: delta already carries the full bank loss (final=0);
    # the extra constant makes death strictly worse than any mere loss
    return res['delta'] if not res['died'] else res['delta'] - 25.0


# ---------------------------------------------------------------------------
# Propose: candidates x ensemble, CVaR + LCB acceptance
# ---------------------------------------------------------------------------
_COMPASS = [(math.cos(a), math.sin(a))
            for a in [i * math.pi / 4 for i in range(8)]]


def propose(world, pid, tracker, hunt, H=12, k_lcb=1.0, max_cands=12,
            scenarios=SCENARIOS, dial=0.0, fire_range=None):
    """Returns (action, report). action is the EXACT tuple evaluated (identity).
    Lite knobs (live-budget compression): max_cands, scenarios subset,
    dial = min PREDICTED advantage to accept an override (authority dial),
    fire_range = only plan if an eater-threat is within this distance of our
    centroid (None = always plan)."""
    m = body()
    # baseline action from the production policy on the true (censored) view
    bview = make_view(world, pid, {})
    btr = clone_tracker(tracker)
    bhunt = HuntClone(hunt)
    bfx, bfy, bsp = m._reactive_core(bview, btr, bhunt)[:3]
    baseline = (bfx, bfy, bsp)

    if fire_range is not None:
        p0 = world['players'][pid]
        tm0 = SE.total_mass(p0)
        if tm0 > 0:
            c0x = sum(b[SE.X] * (b[SE.R] * b[SE.R])
                      for b in p0['blobs'].values()) / tm0
            c0y = sum(b[SE.Y] * (b[SE.R] * b[SE.R])
                      for b in p0['blobs'].values()) / tm0
            small0 = min(b[SE.R] * b[SE.R] for b in p0['blobs'].values())
            hot = False
            for opid, op in world['players'].items():
                if opid == pid:
                    continue
                for b in op['blobs'].values():
                    if b[SE.R] * b[SE.R] >= small0 * 1.2 and \
                            math.hypot(b[SE.X] - c0x, b[SE.Y] - c0y) < fire_range:
                        hot = True
                        break
                if hot:
                    break
            if not hot:
                return baseline, {'baseline': {'action': baseline, 'mean': 0.0,
                                               'worst': 0.0, 'std': 0.0, 'res': []},
                                  'chosen': None, 'override': False,
                                  'rows': [{'action': baseline}],
                                  'skipped': 'no-threat'}

    cands = [baseline]
    seen = {(round(bfx, 3), round(bfy, 3), bsp)}

    def add(fx, fy, sp):
        n = math.hypot(fx, fy)
        if n < 1e-9:
            return
        key = (round(fx / n, 3), round(fy / n, 3), sp)
        if key in seen:
            return
        seen.add(key)
        cands.append((fx / n, fy / n, sp))

    # priority candidates first (so lite truncation keeps the ones that matter):
    # flee-worst-threat, escape perpendiculars, chase-prey, split variant,
    # then compass fill.
    p = world['players'][pid]
    mym = SE.total_mass(p)
    if mym > 0:
        cx = sum(b[SE.X] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / mym
        cy = sum(b[SE.Y] * (b[SE.R] * b[SE.R]) for b in p['blobs'].values()) / mym
        vb = bview.state.visible_blobs
        thr = [b for b in vb if b.radius * b.radius > mym * 1.1]
        if thr:
            wt = min(thr, key=lambda b: (b.pos[0] - cx) ** 2 + (b.pos[1] - cy) ** 2)
            ax, ay = cx - wt.pos[0], cy - wt.pos[1]
            add(ax, ay, False)
            add(-ay, ax, False)      # escape perpendiculars: the juke headings
            add(ay, -ax, False)
        small = min((b[SE.R] * b[SE.R] for b in p['blobs'].values()), default=0.0)
        prey = [b for b in vb if small >= b.radius * b.radius * 1.2]
        if prey:
            bp = min(prey, key=lambda b: (b.pos[0] - cx) ** 2 + (b.pos[1] - cy) ** 2)
            add(bp.pos[0] - cx, bp.pos[1] - cy, False)
    # split variant of the baseline heading (if any blob can split)
    if any(b[SE.R] * b[SE.R] >= 2.0 for b in p['blobs'].values()) \
            and math.hypot(bfx, bfy) > 1e-9 and not bsp:
        add(bfx, bfy, True)
    for ux, uy in _COMPASS:
        add(ux, uy, False)
    cands = cands[:max_cands]

    rows = []
    for a in cands:
        res = [rollout(world, pid, a, sc, tracker, hunt, H) for sc in scenarios]
        vals = [_value(r) for r in res]
        n = len(vals)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        rows.append({'action': a, 'mean': mean, 'worst': min(vals),
                     'std': math.sqrt(var), 'res': res})
    base_row = rows[0]
    best = base_row
    for row in rows[1:]:
        adv = [v - b for v, b in
               zip([_value(r) for r in row['res']],
                   [_value(r) for r in base_row['res']])]
        madv = sum(adv) / len(adv)
        vadv = sum((a - madv) ** 2 for a in adv) / len(adv)
        lcb = madv - k_lcb * math.sqrt(vadv / len(adv))
        row['lcb'] = lcb
        if row['worst'] >= base_row['worst'] and lcb > 0 and madv >= dial \
                and row['mean'] > best['mean']:
            best = row
    return best['action'], {'baseline': base_row, 'chosen': best,
                            'override': best is not base_row, 'rows': rows}


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke():
    import random, time
    rnd = random.Random(42)
    m = body()
    n_ok = 0
    t_prop = []
    n_override = 0
    for trial in range(20):
        world = {'size': 60.0, 'players': {}, 'foods': [], 'viruses': []}
        for pid in range(8):
            nb = rnd.choice([1, 1, 2, 3])
            cxy = (rnd.uniform(5, 55), rnd.uniform(5, 55))
            blobs = {}
            for bid in range(nb):
                r = rnd.uniform(0.9, 6.0)
                x = min(max(cxy[0] + rnd.uniform(-3, 3), r), 60 - r)
                y = min(max(cxy[1] + rnd.uniform(-3, 3), r), 60 - r)
                blobs[bid] = [x, y, r, 0, 0.0, 0.0]
            world['players'][pid] = {'blobs': blobs, 'next_bid': nb}
        for fid in range(160):
            world['foods'].append([fid, rnd.uniform(0, 60), rnd.uniform(0, 60)])
        for vid in range(6):
            world['viruses'].append([vid, rnd.uniform(2, 58), rnd.uniform(2, 58), 1.5])
        tr = m.Tracker()
        hunt = HuntClone()
        # warm the tracker with one real call
        m._reactive_core(make_view(world, 0, {}), tr, hunt)
        t0 = time.perf_counter()
        a1, rep1 = propose(world, 0, tr, hunt)
        t_prop.append(time.perf_counter() - t0)
        a2, rep2 = propose(world, 0, tr, hunt)
        assert a1 == a2, ("nondeterministic propose", a1, a2)
        # structural identity: chosen action is exactly one of the evaluated ones
        assert any(a1 == r['action'] for r in rep1['rows'])
        n_ok += 1
        n_override += bool(rep1['override'])
    print(f"SMOKE: {n_ok}/20 worlds ok, deterministic, "
          f"{n_override} overrides, propose avg {sum(t_prop)/len(t_prop)*1000:.0f} ms "
          f"(max {max(t_prop)*1000:.0f} ms)")


if __name__ == '__main__':
    _smoke()
