#!/usr/bin/env python3
"""planner4.py — PL4-Tactical: option-based receding-horizon MPC (2026-07-18).

Amended spec (external review, Chris-approved):
  * incumbent = the FULLY GUARDED production action (PC-composed when PC_ON),
    evaluated first and never pruned; candidate zero.
  * <=9 conditionally generated closed-loop options (EV table = its validated
    discrete consumer at last); OptionState for true hysteresis.
  * tiered beam: ALL candidates symmetric at H8 across 5 scenarios ->
    top-3 + incumbent deepen to H12. Only complete tiers are comparable;
    deadline abort selects from the last COMPLETE tier (no ordering bias).
  * hard caps: 1,500 sim-steps and 300ms per fire (anytime).
  * opponents: primary threat adversarial (pursue/intercept/delayed-split,
    blob-to-blob split geometry), secondaries continue/pursue, prey flees
    independently. 5 composed scenarios.
  * leaf: lexicographic risk (death, bank loss, clearance) then conservative
    return; hazard terminal-only, support-weighted, capped, BASELINE-RELATIVE.
  * transition: tools/sim_engine (bit-exact vs engine .13-.16 physics).

Offline module; the in-body port mirrors this exactly. Smoke: __main__.
"""
import math
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import sim_engine as SE
import planner_v3 as PV

X, Y, R, CD, EVX, EVY = range(6)

STEP_CAP = 1500
DEADLINE_S = 0.30
H_SHALLOW = 8
H_DEEP = 12
BEAM = 3
K_CONS = 0.5          # conservative-return std multiplier
HZ_CAP = 0.20         # max |hazard leaf| as fraction of bank
UNCERT_PEN = 0.15     # flat penalty: continuation approximates PC with reactive

SCENARIOS = ("S1_continue", "S2_pursue", "S3_intercept", "S4_delaysplit", "S5_mixed")


def body():
    return PV.body()


# ---------------------------------------------------------------------------
# world helpers
# ---------------------------------------------------------------------------

def centroid(p):
    tm = SE.total_mass(p)
    if tm <= 0:
        return None
    cx = sum(b[X] * (b[R] * b[R]) for b in p['blobs'].values()) / tm
    cy = sum(b[Y] * (b[R] * b[R]) for b in p['blobs'].values()) / tm
    return cx, cy, tm


def rank_opponents(world, pid):
    """-> (primary_threat_pid|None, secondary_pids, prey_pids). Threat rank =
    biggest-eater-blob proximity-weighted; primary gets the adversarial set."""
    me = world['players'][pid]
    c = centroid(me)
    if c is None:
        return None, [], []
    cx, cy, mym = c
    small = min((b[R] * b[R] for b in me['blobs'].values()), default=0.0)
    scored = []
    prey = []
    for opid, op in world['players'].items():
        if opid == pid or not op['blobs']:
            continue
        om = SE.total_mass(op)
        oc = centroid(op)
        d = math.hypot(oc[0] - cx, oc[1] - cy)
        can_eat = any(b[R] * b[R] >= small * 1.2 for b in op['blobs'].values())
        if can_eat:
            scored.append((om / (d + 1.0), opid))
        elif mym >= om * 1.2:
            prey.append((d, opid))
    scored.sort(reverse=True)
    primary = scored[0][1] if scored else None
    secondary = [p for _, p in scored[1:3]]
    prey = [p for _, p in sorted(prey)[:2]]
    return primary, secondary, prey


def time_to_contact(world, pid):
    """Min ticks for any eater-blob to reach our nearest vulnerable blob,
    incl. split reach (blob-to-blob geometry, engine speeds)."""
    me = world['players'][pid]
    best = 999.0
    for opid, op in world['players'].items():
        if opid == pid:
            continue
        for ob in op['blobs'].values():
            om = ob[R] * ob[R]
            for mb in me['blobs'].values():
                if om < mb[R] * mb[R] * 1.2 * 0.5:      # can't eat even after split
                    continue
                d = math.hypot(ob[X] - mb[X], ob[Y] - mb[Y]) - ob[R]
                rel = SE.speed_of(ob[R]) + SE.speed_of(mb[R])
                t = max(0.0, d) / max(rel, 1e-6)
                if om >= 2.0 and ob[CD] == 0 and om / 2.0 >= mb[R] * mb[R] * 1.2:
                    t = min(t, max(0.0, d - 4.5) / max(rel, 1e-6))   # split lunge
                best = min(best, t)
    return best


# ---------------------------------------------------------------------------
# hazard leaf (features per tools mine_hazard; body table via _hz_lookup)
# ---------------------------------------------------------------------------
_CAP_E = [0.0, 1.5, 3.5, 6.0, 10.0]
_SPL_E = [0.0, 2.0, 5.0, 9.0]
_TTC_E = [4, 10, 25, 60]
_BANK_E = [8, 25, 60, 130]


def hz_terminal(world, pid):
    m = body()
    me = world['players'][pid]
    if not me['blobs']:
        return 1.0, 1.0          # dead: max hazard, full support
    c = centroid(me)
    cx, cy, mym = c
    small = min(b[R] * b[R] for b in me['blobs'].values())
    big_r = max(b[R] for b in me['blobs'].values())
    thr = []
    second = 0
    for opid, op in world['players'].items():
        if opid == pid:
            continue
        for b in op['blobs'].values():
            if b[R] * b[R] >= small * 1.2:
                d = math.hypot(b[X] - cx, b[Y] - cy)
                if d < 22:
                    thr.append((d, b))
    if not thr:
        return 0.0, 0.0
    thr.sort()
    d, tb = thr[0]
    second = 1 if len(thr) > 1 else 0
    tr = tb[R]
    cap = m._hz_band(d - tr, _CAP_E) if hasattr(m, "_hz_band") else 0
    half = tr * tr / 2.0
    spl = m._hz_band(d - (2 * math.sqrt(half) + 4.0), _SPL_E) if half >= small * 1.2 else len(_SPL_E)
    rel = SE.speed_of(tr) - SE.speed_of(big_r)
    ttc = m._hz_band(d / rel, _TTC_E) if rel > 0.01 else len(_TTC_E)
    wallx = min(cx, 60 - cx); wally = min(cy, 60 - cy)
    wcls = 2 if min(wallx, wally) < 3 else (1 if min(wallx, wally) < 8 else 0)
    frag = 1 if len(me['blobs']) > 1 else 0
    bank = m._hz_band(mym, _BANK_E)
    try:
        d20, sup = m._hz_lookup(cap, spl, wcls, frag, ttc, second, 0, bank)
        return d20, sup
    except Exception:
        return 0.0, 0.0


# ---------------------------------------------------------------------------
# options (closed-loop; OptionState = dict for hysteresis)
# ---------------------------------------------------------------------------

def _flee_vec(world, pid, primary):
    me = centroid(world['players'][pid])
    oc = centroid(world['players'][primary]) if primary is not None else None
    if me is None or oc is None:
        return None
    dx, dy = me[0] - oc[0], me[1] - oc[1]
    d = math.hypot(dx, dy) or 1e-9
    return dx / d, dy / d


def gen_options(world, pid, incumbent, primary, prey, commit):
    """-> list of dicts {name, act(world,t)->(dx,dy,split)|None-when-terminated}.
    Conditional generation keeps effective branching <= 9."""
    m = body()
    opts = []
    inc_fx, inc_fy, inc_sp = incumbent

    def mk(name, fn):
        opts.append({"name": name, "act": fn})

    # 0: exact incumbent action at t0, reactive after (candidate zero)
    mk("incumbent", ("INCUMBENT",))
    # 1: pure reactive from t0
    mk("reactive", ("REACTIVE",))
    fl = _flee_vec(world, pid, primary)
    if fl is not None:
        fx, fy = fl
        mk("dead_away", ("HOLD", fx, fy, commit, False))
        c60, s60 = math.cos(1.05), math.sin(1.05)
        mk("orbit_L", ("HOLD", fx * c60 - fy * s60, fx * s60 + fy * c60, commit, False))
        mk("orbit_R", ("HOLD", fx * c60 + fy * s60, -fx * s60 + fy * c60, commit, False))
        # wall-slide: only near a wall — move along the nearest wall, away side
        me = centroid(world['players'][pid])
        cx, cy = me[0], me[1]
        wd = min(cx, 60 - cx, cy, 60 - cy)
        if wd < 6.0:
            if min(cx, 60 - cx) < min(cy, 60 - cy):
                sl = (0.0, 1.0 if fy >= 0 else -1.0)
            else:
                sl = (1.0 if fx >= 0 else -1.0, 0.0)
            mk("wall_slide", ("HOLD", sl[0], sl[1], commit, False))
        # EV-table escape (the validated discrete consumer)
        p = world['players'][pid]
        small = min(b[R] * b[R] for b in p['blobs'].values())
        oc = centroid(world['players'][primary])
        td = math.hypot(oc[0] - cx, oc[1] - cy)
        tr = max(b[R] for b in world['players'][primary]['blobs'].values())
        if td < m.CONFIG.get("EV_RANGE", 9.0) + 2.0:
            cls = 1 if (tr * tr) / 2.0 > small * 1.2 else 0
            sgx = 1.0 if cx <= 30.0 else -1.0
            sgy = 1.0 if cy <= 30.0 else -1.0
            try:
                a = m._ev_lookup(cx if sgx > 0 else 60 - cx, cy if sgy > 0 else 60 - cy,
                                 (oc[0] - cx) * sgx, (oc[1] - cy) * sgy, cls,
                                 1 if cls == 1 else 0)
                hx, hy = m._EV_DIRS[a]
                mk("ev_escape", ("HOLD", hx * sgx, hy * sgy, commit, False))
            except Exception:
                pass
        # guarded split-escape: eligible + threat close + not already splitting
        can_split = any(b[R] * b[R] >= 2.0 and b[CD] == 0 for b in p['blobs'].values())
        if can_split and td < 7.0 and not inc_sp and len(p['blobs']) <= 8:
            mk("split_escape", ("SPLIT1", fx, fy))
    # prey intercept + guarded split-attack
    if prey:
        p = world['players'][pid]
        me = centroid(p)
        pc = centroid(world['players'][prey[0]])
        if me and pc:
            dx, dy = pc[0] - me[0], pc[1] - me[1]
            d = math.hypot(dx, dy) or 1e-9
            if d < 14.0:
                mk("intercept", ("HOLD", dx / d, dy / d, commit, False))
            big = max(b[R] * b[R] for b in p['blobs'].values())
            tgt_small = min(b[R] * b[R] for b in world['players'][prey[0]]['blobs'].values())
            eligible = any(b[R] * b[R] >= 2.0 and b[CD] == 0 for b in p['blobs'].values())
            if eligible and big / 2.0 >= tgt_small * 1.2 and d < math.sqrt(big / 2.0) + 5.5 \
                    and not inc_sp and len(p['blobs']) <= 8:
                mk("split_attack", ("SPLIT1", dx / d, dy / d))
    return opts[:9]


def option_action(opt, world, pid, t, incumbent, m, view, tr, hunt):
    """Resolve the option's action at simulated tick t."""
    kind = opt["act"][0]
    if kind == "INCUMBENT":
        if t == 0:
            return incumbent
        rfx, rfy, rsp = m._reactive_core(view, tr, hunt)[:3]
        return (rfx, rfy, rsp)
    if kind == "REACTIVE":
        rfx, rfy, rsp = m._reactive_core(view, tr, hunt)[:3]
        return (rfx, rfy, rsp)
    if kind == "HOLD":
        _, hx, hy, commit, sp = opt["act"]
        if t < commit:
            return (hx, hy, False)
        rfx, rfy, rsp = m._reactive_core(view, tr, hunt)[:3]
        return (rfx, rfy, rsp)
    if kind == "SPLIT1":
        _, hx, hy = opt["act"]
        if t == 0:
            return (hx, hy, True)
        rfx, rfy, rsp = m._reactive_core(view, tr, hunt)[:3]
        return (rfx, rfy, rsp)
    return incumbent


# ---------------------------------------------------------------------------
# opponent scenario roles
# ---------------------------------------------------------------------------

def opp_action(world, opid, pid, role, tracker, t):
    op = world['players'][opid]
    if not op['blobs']:
        return (0.0, 0.0, False)
    if role == "continue":
        v = tracker.intent_dir.get(opid) if tracker else None
        return (v[0], v[1], False) if v else (0.0, 0.0, False)
    me = centroid(world['players'][pid])
    oc = centroid(op)
    if me is None or oc is None:
        return (0.0, 0.0, False)
    dx, dy = me[0] - oc[0], me[1] - oc[1]
    d = math.hypot(dx, dy) or 1e-9
    if role == "pursue":
        return (dx / d, dy / d, False)
    if role == "intercept":
        v = tracker.velocity.get((pid, 0), (0.0, 0.0)) if tracker else (0.0, 0.0)
        tx, ty = me[0] + v[0] * 4 - oc[0], me[1] + v[1] * 4 - oc[1]
        td = math.hypot(tx, ty) or 1e-9
        return (tx / td, ty / td, False)
    if role == "delaysplit":
        # blob-to-blob: strike the first tick a half can capture our smallest
        small = min(b[R] * b[R] for b in world['players'][pid]['blobs'].values())
        for b in op['blobs'].values():
            bm = b[R] * b[R]
            if bm >= 2.0 and b[CD] == 0 and bm / 2.0 >= small * 1.2:
                for mb in world['players'][pid]['blobs'].values():
                    bd = math.hypot(b[X] - mb[X], b[Y] - mb[Y])
                    if bd < math.sqrt(bm / 2.0) + 4.5:
                        return (dx / d, dy / d, True)
        return (dx / d, dy / d, False)
    if role == "flee":
        return (-dx / d, -dy / d, False)
    if role == "juke":
        return (-dy / d if t % 4 < 2 else dy / d, dx / d if t % 4 < 2 else -dx / d, False)
    return (0.0, 0.0, False)


def scenario_roles(scenario, primary, secondary, prey):
    roles = {}
    for p in secondary:
        roles[p] = "continue"
    for p in prey:
        roles[p] = "flee"
    if primary is not None:
        roles[primary] = {"S1_continue": "continue", "S2_pursue": "pursue",
                          "S3_intercept": "intercept", "S4_delaysplit": "delaysplit",
                          "S5_mixed": "pursue"}[scenario]
    if scenario == "S5_mixed":
        for p in secondary:
            roles[p] = "intercept"
        for p in prey:
            roles[p] = "juke"
    return roles


# ---------------------------------------------------------------------------
# rollout
# ---------------------------------------------------------------------------

def rollout(world0, pid, opt, incumbent, scenario, roleset, H, tracker0, hunt0,
            budget):
    """budget = [steps_remaining]. Returns metrics dict or None if budget dry."""
    if budget[0] < H:
        return None
    m = body()
    world = SE.clone(world0)
    tr = PV.clone_tracker(tracker0)
    hunt = PV.HuntClone(hunt0)
    m0 = SE.total_mass(world['players'][pid])
    died_at = None
    min_clear = 99.0
    min_mass = m0
    last_moves = {}
    for t in range(H):
        me = world['players'][pid]
        if not me['blobs']:
            died_at = died_at if died_at is not None else t
            break
        view = PV.make_view(world, pid, last_moves)
        act = option_action(opt, world, pid, t, incumbent, m, view, tr, hunt)
        moves = {pid: act}
        for opid in world['players']:
            if opid == pid or not world['players'][opid]['blobs']:
                continue
            moves[opid] = opp_action(world, opid, pid, roleset.get(opid, "continue"), tr, t)
        events = SE.step(world, moves)
        budget[0] -= 1
        for ev in events:
            if ev[0] == 'death' and ev[1] == pid:
                died_at = t
        cur = SE.total_mass(world['players'][pid])
        min_mass = min(min_mass, cur)
        # clearance: nearest eater-blob surface distance
        me2 = world['players'][pid]
        if me2['blobs']:
            c = centroid(me2)
            small = min(b[R] * b[R] for b in me2['blobs'].values())
            for opid, op in world['players'].items():
                if opid == pid:
                    continue
                for b in op['blobs'].values():
                    if b[R] * b[R] >= small * 1.2:
                        min_clear = min(min_clear, math.hypot(b[X] - c[0], b[Y] - c[1]) - b[R])
        if died_at is not None:
            break
    mf = SE.total_mass(world['players'][pid])
    d20, sup = hz_terminal(world, pid)
    return {"delta": mf - m0, "died": died_at is not None,
            "bank_loss": m0 - min_mass, "min_clear": min_clear,
            "hz": d20, "hz_sup": sup, "final": mf}


def evaluate(world, pid, opt, incumbent, primary, secondary, prey, H,
             tracker, hunt, budget, t_start, deadline):
    """All 5 scenarios or nothing (symmetric coverage)."""
    res = []
    for sc in SCENARIOS:
        if time.perf_counter() - t_start > deadline or budget[0] < H:
            return None
        roleset = scenario_roles(sc, primary, secondary, prey)
        r = rollout(world, pid, opt, incumbent, sc, roleset, H, tracker, hunt, budget)
        if r is None:
            return None
        res.append(r)
    return res


def summarize(res, base_hz):
    deltas = [r["delta"] for r in res]
    mean = sum(deltas) / len(deltas)
    var = sum((d - mean) ** 2 for d in deltas) / len(deltas)
    died_worst = max(1 if r["died"] else 0 for r in res)
    bank_worst = max(r["bank_loss"] for r in res)
    clear_worst = min(r["min_clear"] for r in res)
    # hazard leaf: baseline-relative, support-weighted, capped
    hz_terms = []
    for r in res:
        rel = (r["hz"] - base_hz) * min(r["hz_sup"], 1.0)
        hz_terms.append(max(-HZ_CAP, min(HZ_CAP, rel)) * max(r["final"], 1.0))
    hz_adj = -sum(hz_terms) / len(hz_terms)
    ret = mean + hz_adj - K_CONS * math.sqrt(var)
    return {"died_worst": died_worst, "bank_worst": bank_worst,
            "clear_worst": clear_worst, "ret": ret, "mean": mean}


def risk_ok(cand, inc, eps=0.35):
    return (cand["died_worst"] <= inc["died_worst"]
            and cand["bank_worst"] <= inc["bank_worst"] + eps
            and cand["clear_worst"] >= inc["clear_worst"] - eps)


# ---------------------------------------------------------------------------
# propose4 — tiered beam, anytime, ordering-bias-free
# ---------------------------------------------------------------------------

def propose4(world, pid, tracker, hunt, dial=1.0, commit=3, prev_option=None,
             deadline=DEADLINE_S, step_cap=STEP_CAP):
    m = body()
    t0 = time.perf_counter()
    # incumbent = fully guarded production action (PC-composed when PC_ON)
    bview = PV.make_view(world, pid, {})
    btr = PV.clone_tracker(tracker)
    bhunt = PV.HuntClone(hunt)
    rfx, rfy, rsp, info = m._reactive_core(bview, btr, bhunt)[:4]
    incumbent = (rfx, rfy, rsp)
    if m.CONFIG.get("PC_ON", 0) > 0.5:
        try:
            my_blobs = list(bview.state.me.blobs.values())
            tot = sum(b.radius * b.radius for b in my_blobs)
            pfx, pfy, psp = m._pc_choose(bview.state, btr, info, rfx, rfy, rsp,
                                         my_blobs, tot)
            incumbent = (pfx, pfy, psp)
        except Exception:
            pass

    primary, secondary, prey = rank_opponents(world, pid)
    if primary is None and not prey:
        return incumbent, {"override": False, "why": "no-actors", "rows": []}
    opts = gen_options(world, pid, incumbent, primary, prey, commit)
    budget = [step_cap]

    # baseline hazard reference (t0 world)
    base_hz, _ = hz_terminal(world, pid)

    # TIER 1: everything at H_SHALLOW, symmetric
    tier1 = {}
    for opt in opts:
        res = evaluate(world, pid, opt, incumbent, primary, secondary, prey,
                       H_SHALLOW, tracker, hunt, budget, t0, deadline)
        if res is None:
            break
        tier1[opt["name"]] = (opt, summarize(res, base_hz))
    if "incumbent" not in tier1:
        return incumbent, {"override": False, "why": "deadline-pre-baseline", "rows": []}
    inc1 = tier1["incumbent"][1]

    # rank tier1 survivors (risk-first), pick beam
    ranked = []
    for name, (opt, s) in tier1.items():
        if name == "incumbent":
            continue
        if risk_ok(s, inc1):
            bonus = dial * 0.5 if prev_option == name else 0.0
            ranked.append((s["ret"] + bonus, name, opt))
    ranked.sort(reverse=True, key=lambda r: r[0])
    beam = ranked[:BEAM]

    # TIER 2: incumbent + beam at H_DEEP
    tier2 = {}
    res = evaluate(world, pid, tier1["incumbent"][0], incumbent, primary,
                   secondary, prey, H_DEEP, tracker, hunt, budget, t0, deadline)
    if res is not None:
        tier2["incumbent"] = summarize(res, base_hz)
        for _, name, opt in beam:
            r2 = evaluate(world, pid, opt, incumbent, primary, secondary, prey,
                          H_DEEP, tracker, hunt, budget, t0, deadline)
            if r2 is None:
                break
            tier2[name] = summarize(r2, base_hz)

    # select from the deepest COMPLETE tier
    use, inc_s = (tier2, tier2.get("incumbent")) if len(tier2) >= 2 else \
                 ({k: v for k, (o, v) in tier1.items()}, inc1)
    GREED = {"intercept", "split_attack"}   # return-seeking: higher bar
    best_name, best = "incumbent", inc_s
    for name, s in use.items():
        if name == "incumbent":
            continue
        adv = s["ret"] - inc_s["ret"] - UNCERT_PEN
        if prev_option == name:
            adv += dial * 0.5
        bar = dial * (1.75 if name in GREED else 1.0)
        if risk_ok(s, inc_s) and adv >= bar and s["ret"] > best["ret"]:
            best_name, best = name, s
    if best_name == "incumbent":
        return incumbent, {"override": False, "chosen": "incumbent",
                           "tier": 2 if len(tier2) >= 2 else 1,
                           "steps": step_cap - budget[0], "rows": use}
    opt = next(o for o in opts if o["name"] == best_name)
    view0 = PV.make_view(world, pid, {})
    tr0 = PV.clone_tracker(tracker)
    h0 = PV.HuntClone(hunt)
    act = option_action(opt, world, pid, 0, incumbent, m, view0, tr0, h0)
    return act, {"override": True, "chosen": best_name,
                 "tier": 2 if len(tier2) >= 2 else 1,
                 "steps": step_cap - budget[0],
                 "pred_adv": best["ret"] - inc_s["ret"], "rows": use}


# ---------------------------------------------------------------------------
# smoke
# ---------------------------------------------------------------------------

def _smoke():
    import random
    rnd = random.Random(7)
    m = body()
    times, overrides, choices = [], 0, {}
    for trial in range(30):
        world = {'size': 60.0, 'players': {}, 'foods': [], 'viruses': []}
        for p in range(8):
            nb = rnd.choice([1, 1, 2, 3])
            cx0, cy0 = rnd.uniform(6, 54), rnd.uniform(6, 54)
            blobs = {}
            for b in range(nb):
                r = rnd.uniform(0.9, 6.0)
                x = min(max(cx0 + rnd.uniform(-3, 3), r), 60 - r)
                y = min(max(cy0 + rnd.uniform(-3, 3), r), 60 - r)
                blobs[b] = [x, y, r, 0, 0.0, 0.0]
            world['players'][p] = {'blobs': blobs, 'next_bid': nb}
        # force a hot scene half the time
        if trial % 2 == 0:
            me = world['players'][0]
            for b in me['blobs'].values():
                b[R] = min(b[R], 2.0)
            t = world['players'][1]['blobs'][0]
            c = centroid(me)
            t[X], t[Y], t[R], t[CD] = c[0] + 5.5, c[1], 4.5, 0
        for fid in range(120):
            world['foods'].append([fid, rnd.uniform(0, 60), rnd.uniform(0, 60)])
        for vid in range(4):
            world['viruses'].append([vid, rnd.uniform(3, 57), rnd.uniform(3, 57), 1.5])
        tr = m.Tracker()
        hunt = PV.HuntClone()
        m._reactive_core(PV.make_view(world, 0, {}), tr, hunt)
        t0 = time.perf_counter()
        a1, rep1 = propose4(world, 0, tr, hunt)
        times.append(time.perf_counter() - t0)
        a2, rep2 = propose4(world, 0, tr, hunt)
        assert a1 == a2 and rep1.get("chosen") == rep2.get("chosen"), "nondeterministic"
        if rep1.get("override"):
            overrides += 1
            choices[rep1["chosen"]] = choices.get(rep1["chosen"], 0) + 1
    times.sort()
    print(f"SMOKE: 30 worlds ok, deterministic | overrides {overrides} by {choices}")
    print(f"timing p50 {times[15]*1000:.0f}ms p90 {times[27]*1000:.0f}ms max {times[-1]*1000:.0f}ms "
          f"(deadline {DEADLINE_S*1000:.0f}ms, cap {STEP_CAP} steps)")


if __name__ == "__main__":
    _smoke()
