#!/usr/bin/env python3
"""shadow_grade.py — counterfactual grader for planner v3 (shadow evidence).

For each harvested replay (our own matches; full information):
  1. Reconstruct the full world at every round: blobs (pos/r/cd from
     player_moved snapshots), foods (spawn/eaten by id), viruses,
     eject velocities estimated from movement residuals.
  2. At sampled decision points, warm a Tracker over the prior 10 rounds,
     then run planner_v3.propose() for OUR seat.
  3. If the planner overrides the reactive baseline, simulate BOTH arms
     for H_GRADE rounds through the bit-exact sim (tools/sim_engine):
     our arm action first tick + production `_reactive_core` continuation;
     opponents replay their RECORDED moves (ground-truth behavior).
  4. Paired outcome: value(planner arm) - value(reactive arm), death flags.

Usage:
  python3 tools/shadow_grade.py <replay_dir> [out.jsonl] [max_replays]
Summary printed at the end; rows appended to out.jsonl.
"""
import gzip
import json
import math
import os
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import sim_engine as SE
import planner_v3 as PV

US_TEAM = int(os.environ.get("US_TEAM", 35))
H_PLAN = int(os.environ.get("PV3_H", 12))
H_GRADE = 30
WARMUP = 10
STRIDE_THREAT = 8
STRIDE_CALM = 50
MAX_POINTS = 25
DEATH_PEN = 25.0
# lite-mode knobs (env): PV3_CANDS, PV3_SCEN (csv), PV3_DIAL, PV3_RANGE
PV3_CANDS = int(os.environ.get("PV3_CANDS", 12))
PV3_SCEN = tuple(os.environ.get("PV3_SCEN", ",".join(PV.SCENARIOS)).split(","))
PV3_DIAL = float(os.environ.get("PV3_DIAL", 0.0))
PV3_RANGE = float(os.environ["PV3_RANGE"]) if "PV3_RANGE" in os.environ else None
X, Y, R, CD, EVX, EVY = range(6)


def parse_replay(path):
    ev = json.load(gzip.open(path, "rt"))
    gs = next(e for e in ev if e.get("event_type") == "event_game_started")
    team = {p["player_id"]: p["team_id"] for p in gs["players"]}
    food_pos = {}         # live foods
    all_food_pos = {}     # every food position ever spawned (by id)
    virus_state = {}
    rounds = []           # per round: {'moves': {pid:(dx,dy,sp)}, 'players': {...},
                          #             'foods': set(ids), 'viruses': dict copy}
    cur_moves = {}
    cur_snaps = {}
    snap_phase = False
    virus_hits = set()    # pids that consumed a virus this round

    def finalize():
        players = {}
        for pid, bl in cur_snaps.items():
            players[pid] = {bid: [x, y, r, cd, 0.0, 0.0]
                            for bid, x, y, r, cd in bl}
        rounds.append({'moves': dict(cur_moves), 'players': players,
                       'foods': set(food_pos), 'viruses': dict(virus_state),
                       'virus_hits': set(virus_hits)})

    for e in ev:
        et = e.get("event_type")
        if et == "move_player":
            if snap_phase:
                finalize()
                cur_moves = {}
                cur_snaps = {}
                virus_hits.clear()
                snap_phase = False
            d = e["direction"]
            if d.get("degrees") is not None:
                a = math.radians(d["degrees"])
                dx, dy = math.cos(a), math.sin(a)
            else:
                dx, dy = d.get("x") or 0.0, d.get("y") or 0.0
            cur_moves[e["player_id"]] = (dx, dy, bool(e.get("split")))
        elif et == "event_player_moved":
            snap_phase = True
            cur_snaps[e["player_id"]] = [
                (b["blob_id"], b["pos"][0], b["pos"][1], b["radius"],
                 b.get("merge_cooldown", 0)) for b in (e.get("blobs") or [])]
        elif et == "event_food_spawned":
            for f in e["foods"]:
                food_pos[f["food_id"]] = (f["pos"][0], f["pos"][1])
                all_food_pos[f["food_id"]] = (f["pos"][0], f["pos"][1])
        elif et == "event_food_eaten":
            for fid in e.get("food_ids", []):
                food_pos.pop(fid, None)
        elif et == "event_virus_spawned":
            for v in e["viruses"]:
                virus_state[v["virus_id"]] = (v["pos"][0], v["pos"][1], v["radius"])
        elif et == "event_virus_consumed":
            virus_state.pop(e.get("virus_id"), None)
            if e.get("player_id") is not None:
                virus_hits.add(e["player_id"])
    if snap_phase and cur_snaps:
        finalize()

    _estimate_ejects(rounds)
    return team, rounds, all_food_pos


def _estimate_ejects(rounds):
    """Eject velocity is hidden; recover it from movement residuals.
    residual = observed displacement - commanded move; eject after the round
    = residual * 0.82 (drag applies post-move). New blobs born with cd=17:
    split children carry dir*1.6*0.82 unless a virus pop made them."""
    for i in range(1, len(rounds)):
        prev, cur = rounds[i - 1], rounds[i]
        for pid, blobs in cur['players'].items():
            mv = cur['moves'].get(pid)
            ux = uy = 0.0
            if mv:
                n = max(abs(mv[0]), abs(mv[1]))
                if n and math.isfinite(n):
                    sx, sy = mv[0] / n, mv[1] / n
                    mag = math.hypot(sx, sy)
                    ux, uy = sx / mag, sy / mag
            pblobs = prev['players'].get(pid, {})
            for bid, b in blobs.items():
                pb = pblobs.get(bid)
                if pb is not None:
                    sp = SE.speed_of(pb[R]) if (ux or uy) else 0.0
                    rx = b[X] - pb[X] - ux * sp
                    ry = b[Y] - pb[Y] - uy * sp
                    if abs(rx) < 0.12:
                        rx = 0.0
                    if abs(ry) < 0.12:
                        ry = 0.0
                    b[EVX] = rx * 0.82 if abs(rx * 0.82) >= 1e-4 else 0.0
                    b[EVY] = ry * 0.82 if abs(ry * 0.82) >= 1e-4 else 0.0
                elif b[CD] >= 16 and pid not in cur['virus_hits'] and mv \
                        and mv[2] and (ux or uy):
                    b[EVX] = ux * 1.6 * 0.82
                    b[EVY] = uy * 1.6 * 0.82


def world_at(rounds, i):
    rd = rounds[i]
    foods = rd['foods']
    return {
        'size': 60.0,
        'players': {pid: {'blobs': {bid: b[:] for bid, b in bl.items()},
                          'next_bid': (max(bl) + 1) if bl else 0}
                    for pid, bl in rd['players'].items()},
        'foods': [[fid, x, y] for fid, (x, y) in _foods_of(rounds, i).items()],
        'viruses': [[vid, x, y, r] for vid, (x, y, r) in rd['viruses'].items()],
    }


def _foods_of(rounds, i):
    # food positions are global by id; rounds[i]['foods'] is the live id set.
    # sorted by id = spawn order = engine map.foods list order (matters:
    # foods resolve in list order)
    return {fid: FOOD_POS[fid] for fid in sorted(rounds[i]['foods'])
            if fid in FOOD_POS}


FOOD_POS = {}


def warm_tracker(m, rounds, i, pid):
    tr = m.Tracker()
    hunt = PV.HuntClone()
    for k in range(max(0, i - WARMUP), i + 1):
        if not rounds[k]['players'].get(pid):
            continue
        w = world_at(rounds, k)
        view = PV.make_view(w, pid, rounds[k]['moves'])
        try:
            m._reactive_core(view, tr, hunt)
        except Exception:
            pass
    return tr, hunt


def run_arm(m, rounds, i, pid, action0, tracker, hunt):
    world = world_at(rounds, i)
    tr = PV.clone_tracker(tracker)
    h = PV.HuntClone(hunt)
    m0 = SE.total_mass(world['players'][pid])
    died = False
    last_moves = {}
    last_known = {}
    for step_i in range(H_GRADE):
        ri = i + 1 + step_i
        rec = rounds[ri]['moves'] if ri < len(rounds) else {}
        moves = {}
        for opid in world['players']:
            if opid == pid or not world['players'][opid]['blobs']:
                continue
            if opid in rec:
                moves[opid] = rec[opid]
                last_known[opid] = rec[opid]
            elif opid in last_known:
                dx, dy, _ = last_known[opid]
                moves[opid] = (dx, dy, False)
            else:
                moves[opid] = (0.0, 0.0, False)
        if world['players'][pid]['blobs']:
            if step_i == 0:
                moves[pid] = action0
            else:
                view = PV.make_view(world, pid, last_moves)
                fx, fy, sp = m._reactive_core(view, tr, h)[:3]
                moves[pid] = (fx, fy, sp)
        events = SE.step(world, moves)
        last_moves = moves
        for evt in events:
            if evt[0] == 'death' and evt[1] == pid:
                died = True
        if died:
            break
    mf = SE.total_mass(world['players'][pid])
    val = (mf - m0) if not died else (mf - m0) - DEATH_PEN
    return {'delta': mf - m0, 'died': died, 'value': val}


def grade_replay(path, out_f):
    global FOOD_POS
    m = PV.body()
    team, rounds, all_food = parse_replay(path)
    FOOD_POS = all_food
    # all food positions ever seen (spawned) — keep the union
    us = next((p for p, t in team.items() if t == US_TEAM), None)
    if us is None:
        return []
    results = []
    n_points = 0
    last_t = -999
    for i in range(30, min(len(rounds) - H_GRADE - 1, 1330)):
        if n_points >= MAX_POINTS:
            break
        bl = rounds[i]['players'].get(us)
        if not bl:
            continue
        mym = sum(b[R] * b[R] for b in bl.values())
        small = min(b[R] * b[R] for b in bl.values())
        cx = sum(b[X] * (b[R] * b[R]) for b in bl.values()) / mym
        cy = sum(b[Y] * (b[R] * b[R]) for b in bl.values()) / mym
        threat_near = False
        for opid, obl in rounds[i]['players'].items():
            if opid == us:
                continue
            for b in obl.values():
                if b[R] * b[R] >= small * 1.2 and \
                        math.hypot(b[X] - cx, b[Y] - cy) < 12.0:
                    threat_near = True
                    break
            if threat_near:
                break
        stride = STRIDE_THREAT if threat_near else STRIDE_CALM
        if i - last_t < stride:
            continue
        last_t = i
        n_points += 1
        world = world_at(rounds, i)
        tr, hunt = warm_tracker(m, rounds, i, us)
        t0 = time.perf_counter()
        try:
            if os.environ.get("USE_PL4"):
                import planner4 as P4
                action, rep = P4.propose4(world, us, tr, hunt,
                                          dial=float(os.environ.get("PL4_DIAL", 1.0)))
                rep.setdefault("baseline", {"action": None, "mean": 0.0})
                if rep.get("override"):
                    rep["chosen_stats"] = rep.get("rows", {}).get(rep.get("chosen"), {})
            else:
                action, rep = PV.propose(world, us, tr, hunt, H=H_PLAN,
                                         max_cands=PV3_CANDS, scenarios=PV3_SCEN,
                                         dial=PV3_DIAL, fire_range=PV3_RANGE)
        except Exception as ex:
            results.append({'m': Path(path).stem.split('.')[0], 't': i,
                            'err': repr(ex)[:120]})
            continue
        dt_prop = time.perf_counter() - t0
        base_action = rep['baseline'].get('action') if isinstance(rep.get('baseline'), dict) else None
        if base_action is None:
            _bv = PV.make_view(world, us, {})
            _btr = PV.clone_tracker(tr); _bh = PV.HuntClone(hunt)
            _r = PV.body()._reactive_core(_bv, _btr, _bh)[:3]
            base_action = (_r[0], _r[1], _r[2])
        row = {'m': Path(path).stem.split('.')[0], 't': i,
               'threat': threat_near, 'mass': round(mym, 2),
               'override': rep['override'], 'prop_ms': int(dt_prop * 1000)}
        if rep['override']:
            base_out = run_arm(m, rounds, i, us, base_action, tr, hunt)
            plan_out = run_arm(m, rounds, i, us, action, tr, hunt)
            row.update({
                'adv': round(plan_out['value'] - base_out['value'], 3),
                'base': round(base_out['value'], 3),
                'plan': round(plan_out['value'], 3),
                'base_died': base_out['died'], 'plan_died': plan_out['died'],
                'pred_adv': round(rep.get('pred_adv',
                    (rep['chosen']['mean'] - rep['baseline']['mean'])
                    if isinstance(rep.get('chosen'), dict) else 0.0), 3),
            })
        results.append(row)
        out_f.write(json.dumps(row) + "\n")
        out_f.flush()
    return results


def main():
    rdir = sys.argv[1] if len(sys.argv) > 1 else "."
    out_path = sys.argv[2] if len(sys.argv) > 2 else "shadow_grade.jsonl"
    max_rep = int(sys.argv[3]) if len(sys.argv) > 3 else 999
    paths = sorted(Path(rdir).glob("*.json.gz"))[:max_rep]
    allrows = []
    with open(out_path, "a") as out_f:
        for k, p in enumerate(paths):
            t0 = time.time()
            rows = grade_replay(p, out_f)
            ov = [r for r in rows if r.get('override')]
            print(f"[{k+1}/{len(paths)}] {p.name}: {len(rows)} pts, "
                  f"{len(ov)} overrides, {time.time()-t0:.0f}s", flush=True)
            allrows += rows
    _summary(allrows)


def _summary(rows):
    import random
    ov = [r for r in rows if r.get('override') and 'adv' in r]
    n = len([r for r in rows if 'err' not in r])
    errs = len([r for r in rows if 'err' in r])
    print(f"\n=== SHADOW EVIDENCE ===")
    print(f"decision points: {n} (errors {errs}), overrides {len(ov)} "
          f"({100.0*len(ov)/max(n,1):.0f}%)")
    if not ov:
        return
    advs = [r['adv'] for r in ov]
    mean = sum(advs) / len(advs)
    advs_s = sorted(advs)
    med = advs_s[len(advs) // 2]
    wins = sum(a > 0 for a in advs)
    bd = sum(r['base_died'] for r in ov)
    pd = sum(r['plan_died'] for r in ov)
    rnd = random.Random(7)
    boots = []
    for _ in range(2000):
        s = [advs[rnd.randrange(len(advs))] for _ in advs]
        boots.append(sum(s) / len(s))
    boots.sort()
    lo, hi = boots[50], boots[1949]
    # prediction calibration: corr(pred_adv, adv)
    preds = [r['pred_adv'] for r in ov]
    mp = sum(preds) / len(preds)
    ma = mean
    cov = sum((p - mp) * (a - ma) for p, a in zip(preds, advs))
    vp = math.sqrt(sum((p - mp) ** 2 for p in preds)) or 1e-9
    va = math.sqrt(sum((a - ma) ** 2 for a in advs)) or 1e-9
    print(f"paired advantage: mean {mean:+.2f}  median {med:+.2f}  "
          f"bootstrap95 [{lo:+.2f}, {hi:+.2f}]")
    print(f"win rate {100.0*wins/len(advs):.0f}%  "
          f"deaths base {bd} vs planner {pd}")
    print(f"prediction correlation r = {cov/(vp*va):+.2f}")


if __name__ == '__main__':
    main()
