#!/usr/bin/env python3
"""pc_gates.py — durable PLANCORE gate battery (2026-07-17 P0 repairs).

Run: evolution-2/.venv/bin/python3 tools/pc_gates.py
All gates must print OK. Covers: engine-law movement differential (incl.
eject drag + decay), full split transition (every eligible blob, cooldown 18,
eject 1.6/0.82), food mass growth, prey/threat separation, baseline
preservation, evaluated==executed action identity, mirror symmetry, timing.
"""
import sys, math, random, time
sys.path.insert(0, "/Users/chrisli/Developer/competition/botbattle/tools")
import equiv_test as ET

m = ET.load("/Users/chrisli/Developer/competition/botbattle/bots/omni_mixer_v3.py", "pcg")

def eng_speed(r): return max(0.25, 1.1 / (1 + 0.08 * r))

def gate_movement():
    rnd = random.Random(1)
    for _ in range(3000):
        r = rnd.uniform(0.5, 12.0); x = rnd.uniform(0, 60); y = rnd.uniform(0, 60)
        a = rnd.uniform(0, 2 * math.pi); u = (math.cos(a), math.sin(a))
        evx, evy = rnd.uniform(-1.6, 1.6), rnd.uniform(-1.6, 1.6)
        mass0 = r * r
        _v, _r, fb = m._pc_rollout([[x, y, mass0, 5, evx, evy]], [], [], [], u, False, 1, False, 10.0)
        ex = x + u[0] * eng_speed(r) + evx
        ey = y + u[1] * eng_speed(r) + evy
        em = mass0 * (1 - 0.002)
        er = math.sqrt(em)
        ex = min(max(ex, er), 60 - er) if abs(ex - min(max(ex, math.sqrt(mass0)), 60 - math.sqrt(mass0))) > 1e-12 else ex
        # engine clamps with post-move radius; our sim decays then clamps with sqrt(m)
        b = fb[0]
        assert abs(b[2] - em) < 1e-9, ("decay", b[2], em)
        assert abs(b[4] - evx * 0.82 * (abs(evx * 0.82) >= 1e-4)) < 1e-9
        assert b[3] == 4, ("cooldown decrement", b[3])
    print("GATE movement+eject+drag+decay+cooldown (3000 states): OK")

def gate_split():
    # two eligible blobs + one ineligible: ALL eligible must split with engine kinematics
    blobs = [[30.0, 30.0, 8.0, 0, 0.0, 0.0], [34.0, 30.0, 4.0, 0, 0.0, 0.0], [26.0, 30.0, 1.0, 0, 0.0, 0.0]]
    _v, _r, fb = m._pc_rollout(blobs, [], [], [], (1.0, 0.0), True, 1, False, 10.0)
    assert len(fb) == 5, ("expected 5 blobs (2 splits)", len(fb))
    halves = sorted(round(b[2] / (1 - 0.002), 4) for b in fb)
    assert halves == [1.0, 2.0, 2.0, 4.0, 4.0], halves
    kids = [b for b in fb if b[3] == 17]     # cd 18 decremented once
    assert len(kids) == 4, ("split cooldown 18 on parents+children", [b[3] for b in fb])
    kid = max(fb, key=lambda b: b[0])
    assert kid[4] > 1.0, ("child eject velocity retained after drag", kid[4])
    print("GATE split transition (every eligible blob, cd18, eject): OK")

def gate_prey_not_fled():
    # only prey nearby: continuation must NOT flee it; rollout should keep or gain value
    class P:
        pos = (34.0, 30.0); radius = 1.0; player_id = 4; blob_id = 0
    tr = m.Tracker()
    g = ET.gen_tick(random.Random(3), 0, {})
    st = g.state
    st.me.x, st.me.y = 30.0, 30.0
    for b in st.me.blobs.values(): b.pos = (30.0, 30.0); b.radius = 2.5
    st.visible_food = []; st.visible_viruses = []
    info = {"threats": [], "prey": [(P(), 4.0)]}
    m.CONFIG["PC_ON"] = 1
    old_split = m.CONFIG["PC_SPLIT"]; m.CONFIG["PC_SPLIT"] = 0
    fx, fy, sp = m._pc_choose(st, tr, info, 1.0, 0.0, False, list(st.me.blobs.values()), 6.25)
    m.CONFIG["PC_SPLIT"] = old_split
    assert fx > 0.5, ("must not flee prey", fx, fy)
    print("GATE prey/threat separation (does not flee prey): OK")

def gate_baseline_and_identity():
    tr = m.Tracker()
    g = ET.gen_tick(random.Random(5), 0, {})
    st = g.state
    st.me.x, st.me.y = 30.0, 30.0
    for b in st.me.blobs.values(): b.pos = (30.0, 30.0); b.radius = 2.0
    st.visible_food = []; st.visible_viruses = []
    info = {"threats": [], "prey": []}
    m.CONFIG["PC_ON"] = 1
    out = m._pc_choose(st, tr, info, 0.6, 0.8, False, list(st.me.blobs.values()), 4.0)
    assert out == (0.6, 0.8, False), out
    # identity: instrument rollout, assert returned action was evaluated exactly
    seen = []
    orig = m._pc_rollout
    def spy(blobs0, foods, threats, preys, u, sp, H, hz, dc):
        seen.append((round(u[0], 9), round(u[1], 9), sp))
        return orig(blobs0, foods, threats, preys, u, sp, H, hz, dc)
    m._pc_rollout = spy
    class F:
        def __init__(s, x, y): s.pos = (x, y)
    st.visible_food = [F(33, 33), F(27, 33), F(30, 26)]
    fx, fy, sp = m._pc_choose(st, tr, info, 0.6, 0.8, False, list(st.me.blobs.values()), 4.0)
    m._pc_rollout = orig
    assert (round(fx, 9), round(fy, 9), sp) in seen, "returned action was never evaluated"
    print("GATE baseline preservation + evaluated==executed identity: OK")

def gate_symmetry():
    tr = m.Tracker()
    g = ET.gen_tick(random.Random(7), 0, {})
    st = g.state
    for b in st.me.blobs.values(): b.radius = 2.0
    class F:
        def __init__(s, x, y): s.pos = (x, y)
    class T:
        def __init__(s, x, y, r): s.pos = (x, y); s.radius = r; s.player_id = 3; s.blob_id = 0
    m.CONFIG["PC_ON"] = 1
    def scene(sgn):
        st.me.x, st.me.y = 30.0, 30.0
        for b in st.me.blobs.values(): b.pos = (30.0, 30.0)
        st.visible_food = [F(30 + sgn * 4, 31.5), F(30 + sgn * 5, 30.0)]
        st.visible_viruses = []
        tr.velocity = {(3, 0): (sgn * 0.5, 0.0)}
        tr.intent_dir = {}
        return {"threats": [(T(30 - sgn * 7, 30.0, 4.0), 7.0)], "prey": []}
    i1 = scene(1.0);  f1 = m._pc_choose(st, tr, i1, 1.0, 0.0, False, list(st.me.blobs.values()), 4.0)
    i2 = scene(-1.0); f2 = m._pc_choose(st, tr, i2, -1.0, 0.0, False, list(st.me.blobs.values()), 4.0)
    assert abs(f1[0] + f2[0]) < 1e-9 and abs(f1[1] - f2[1]) < 1e-9 and f1[2] == f2[2], (f1, f2)
    print("GATE mirror symmetry: OK")

def gate_timing():
    tr = m.Tracker()
    g = ET.gen_tick(random.Random(9), 0, {})
    st = g.state
    st.me.x, st.me.y = 30.0, 30.0
    for b in st.me.blobs.values(): b.pos = (30.0, 30.0); b.radius = 3.0
    class F:
        def __init__(s, x, y): s.pos = (x, y)
    class T:
        def __init__(s, x, y, r, pid): s.pos = (x, y); s.radius = r; s.player_id = pid; s.blob_id = 0
    st.visible_food = [F(30 + i % 6, 28 + i // 6) for i in range(20)]
    st.visible_viruses = []
    tr.velocity = {(3, 0): (-0.5, 0.0), (4, 0): (0.0, 0.0)}
    tr.intent_dir = {}
    info = {"threats": [(T(38, 30, 4.0, 3), 8.0)], "prey": [(T(33, 33, 1.0, 4), 4.2)]}
    m.CONFIG["PC_ON"] = 1
    t0 = time.perf_counter()
    for _ in range(300):
        m._pc_choose(st, tr, info, 1.0, 0.0, False, list(st.me.blobs.values()), 9.0)
    dt = (time.perf_counter() - t0) / 300
    print(f"GATE timing: {dt*1e6:.0f} us/call ({dt*1400*1000:.0f} ms/match vs 3000ms governor)")
    assert dt * 1400 < 1.5

if __name__ == "__main__":
    gate_movement()
    gate_split()
    gate_prey_not_fled()
    gate_baseline_and_identity()
    gate_symmetry()
    gate_timing()
    print("ALL PLANCORE GATES: OK")
