#!/usr/bin/env python3
"""ARCH v3 EQUIVALENCE GATE (Chris's order 2026-07-13):
given exactly the same engine inputs, the new body must output exactly what
the old body outputs. New expressions start at zero and must not change
behavior — only allow future exploration.

Drives both bodies' full decision pipeline (compute_forces ->
apply_architecture -> should_split/should_cycle_split -> VULN organ) over
N seeded, temporally-coherent mock ticks and compares every output exactly
(float ==, no tolerance). Tests the raw default bodies AND genome-overlaid
variant pairs (old numbering vs migrated numbering).

Usage: equiv_test.py old_body.py new_body.py [ticks] [genome_ids...]
"""
import importlib.util
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARENA = 60.0


# ---------------- mock engine ----------------
class MBlob:
    __slots__ = ("player_id", "blob_id", "pos", "radius", "merge_cooldown")
    def __init__(self, pid, bid, pos, radius, cd=0):
        self.player_id, self.blob_id, self.pos, self.radius = pid, bid, pos, radius
        self.merge_cooldown = cd


class MMyBlob:
    __slots__ = ("radius", "blob_id", "pos")
    def __init__(self, r, bid, pos=(30.0, 30.0)):
        self.radius, self.blob_id, self.pos = r, bid, pos


class MDir:
    def __init__(self, dx, dy): self.dx, self.dy = dx, dy
    def to_vector(self): return (self.dx, self.dy)


class MEvent:
    def __init__(self, et, pid=None, direction=None, split=False):
        self.event_type = et
        self.player_id = pid
        self.direction = direction
        self.split = split


class MFood:
    __slots__ = ("pos",)
    def __init__(self, pos): self.pos = pos


class MVirus:
    __slots__ = ("pos", "radius")
    def __init__(self, pos, r=1.5): self.pos, self.radius = pos, r


class MMe:
    def __init__(self, pid, x, y, blobs):
        self.player_id, self.x, self.y = pid, x, y
        self.blobs = blobs
        self.radius = max(b.radius for b in blobs.values())


class MState:
    pass


class MGame:
    def __init__(self, state): self.state = state


def gen_tick(rng, t, walkers):
    """Temporally-coherent random world. walkers = persistent positions."""
    st = MState()
    # our bot: 1-8 blobs around a drifting center
    if "me" not in walkers:
        walkers["me"] = [rng.uniform(5, 55), rng.uniform(5, 55)]
    mx, my = walkers["me"]
    mx = min(58.0, max(2.0, mx + rng.uniform(-0.8, 0.8)))
    my = min(58.0, max(2.0, my + rng.uniform(-0.8, 0.8)))
    walkers["me"] = [mx, my]
    nblobs = 1 + int(rng.random() * 8) if rng.random() < 0.4 else 1
    myblobs = {i: MMyBlob(rng.uniform(0.8, 6.0), i,
                          (min(59.4, max(0.6, mx + rng.uniform(-1.5, 1.5))),
                           min(59.4, max(0.6, my + rng.uniform(-1.5, 1.5)))))
               for i in range(nblobs)}
    st.me = MMe(0, mx, my, myblobs)
    # opponents: persistent walkers, multi-blob sometimes, corners sometimes
    vis = []
    for pid in range(1, 8):
        key = f"p{pid}"
        if key not in walkers:
            corner = rng.random() < 0.15
            walkers[key] = ([rng.choice([0.6, 59.4]), rng.choice([0.6, 59.4])]
                            if corner else [rng.uniform(1, 59), rng.uniform(1, 59)])
        px, py = walkers[key]
        px = min(59.6, max(0.4, px + rng.uniform(-0.6, 0.6)))
        py = min(59.6, max(0.4, py + rng.uniform(-0.6, 0.6)))
        walkers[key] = [px, py]
        if rng.random() < 0.85:  # visible this tick
            nb = 1 + int(rng.random() * 6) if rng.random() < 0.3 else 1
            for b in range(nb):
                vis.append(MBlob(pid, b,
                                 (min(59.6, max(0.4, px + rng.uniform(-2, 2))),
                                  min(59.6, max(0.4, py + rng.uniform(-2, 2)))),
                                 rng.uniform(0.4, 7.0),
                                 cd=rng.choice([0, 0, 0, 15, 40])))
    st.visible_blobs = vis
    st.visible_viruses = [MVirus((rng.uniform(1, 59), rng.uniform(1, 59)))
                          for _ in range(int(rng.random() * 5))]
    st.visible_food = [MFood((rng.uniform(1, 59), rng.uniform(1, 59)))
                       for _ in range(int(rng.random() * 8))]
    ranking = list(range(8)); rng.shuffle(ranking)
    st.rankings = ranking
    evs = []
    for _ in range(int(rng.random() * 4)):
        k = rng.random()
        if k < 0.5:
            evs.append(MEvent("move_player", pid=rng.randint(1, 7),
                              direction=MDir(rng.uniform(-1, 1), rng.uniform(-1, 1)),
                              split=rng.random() < 0.2))
        else:
            evs.append(MEvent("event_player_eaten", pid=rng.randint(1, 7)))
    st.event_history = evs
    st.new_events = 0
    return MGame(st)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_pipeline(m, game):
    """One tick of the decision pipeline; returns comparable output tuple."""
    tr = m._EQ_TRACKER
    tr.read_intents(game)
    tr.update(game.state.visible_blobs, game.state.me.player_id)
    fx, fy, info = m.compute_forces(game, tr)
    fx2, fy2, sb, cb = m.apply_architecture(game, tr, info, fx, fy)
    osp = m.should_split(game, info, fx2, fy2)
    try:
        csp = m.should_cycle_split(game, info, tr)
    except TypeError:
        csp = m.should_cycle_split(game, info)
    v = m.find_vulnerable_opportunity(game, tr, info)
    vsig = None if v is None else (round(v["direction"][0], 12), round(v["direction"][1], 12))
    return (fx, fy, fx2, fy2, sb, cb, osp, csp, vsig,
            len(info["prey"]), len(info["threats"]))


def run_module(path, name, ticks, seed):
    m = load(path, name)
    m._EQ_TRACKER = m.Tracker()
    m.HUNT.key, m.HUNT.ticks = None, 0
    rng = random.Random(seed)
    walkers = {}
    outs = []
    for t in range(ticks):
        game = gen_tick(rng, t, walkers)
        outs.append(run_pipeline(m, game))
    return outs


def overlay(body_src, genome, migrate):
    src = body_src
    g = dict(genome)
    if migrate:  # node-output refs >= 19 shift +3 (new sensors at 19-21)
        for k in list(g):
            if re.match(r"ARCH_N\d+_(A|B)$", k) and g[k] >= 19:
                g[k] = g[k] + 3
    for k, v in g.items():
        if k.startswith("_"):
            continue
        src = re.sub(rf'("{k}":\s*)-?[0-9.]+(?:[eE][+-]?[0-9]+)?',
                     rf"\g<1>{v:.6g}", src, count=1)
    return src


def main():
    old_p, new_p = sys.argv[1], sys.argv[2]
    ticks = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    gids = [int(x) for x in sys.argv[4:]]
    tmp = Path("/tmp/equiv")
    tmp.mkdir(exist_ok=True)
    state = json.loads((ROOT / "evolution_v3" / "state.json").read_text())
    pool = {g["_id"]: g for g in state["population"]}
    cases = [("default", None)] + [(f"genome#{i}", pool[i]) for i in gids if i in pool]
    old_src = Path(old_p).read_text()
    new_src = Path(new_p).read_text()
    fails = 0
    for label, genome in cases:
        if genome is None:
            pa, pb = old_p, new_p
        else:
            pa = tmp / f"old_{label.replace('#','')}.py"
            pb = tmp / f"new_{label.replace('#','')}.py"
            pa.write_text(overlay(old_src, genome, migrate=False))
            pb.write_text(overlay(new_src, genome, migrate=True))
        A = run_module(str(pa), f"a_{label.replace('#','_')}", ticks, seed=1234)
        B = run_module(str(pb), f"b_{label.replace('#','_')}", ticks, seed=1234)
        diff = [t for t, (x, y) in enumerate(zip(A, B)) if x != y]
        if diff:
            fails += 1
            t = diff[0]
            print(f"[{label}] FAIL — {len(diff)}/{ticks} ticks differ; first at tick {t}")
            print(f"   old: {A[t]}")
            print(f"   new: {B[t]}")
        else:
            print(f"[{label}] PASS — {ticks} ticks bit-identical")
    print("\nVERDICT:", "FAIL" if fails else "PASS — new architecture is behaviorally inert")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
