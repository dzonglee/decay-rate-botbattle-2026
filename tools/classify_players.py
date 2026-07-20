#!/usr/bin/env python3
"""DUMB-vs-INTELLIGENT player classifier (deliverable 2, Chris's build order 2026-07-10).

Reads a replay (visualiser_forwards_differential.json — list of events) and scores
every player 0..1 on behavioral intelligence. Pure stdlib, no sklearn.

Features per player (computed from event_player_moved streams + eat events):
  f1 threat_evasion   — fraction of sampled ticks moving AWAY from a bigger blob within 15u
  f2 prey_pursuit     — fraction of sampled ticks moving TOWARD a smaller blob within 15u
  f3 straightness     — 1 - mean(|heading change|)/pi  (dumb wanderers turn incoherently
                        OR move in perfect lines; intelligent play sits mid-band)
  f4 kills_per_ktick  — event_player_eaten credited as eater, per 1000 ticks
  f5 virus_economy    — event_virus_consumed count, per 1000 ticks
  f6 mass_conversion  — final_mass / (peak_mass + eps): banking discipline

Score = logistic(w . f + b). Default weights hand-calibrated on gym ground truth
(simple_bot/naive_splitter = dumb; gen576/omniB_elite/v3 = intelligent). Recalibrate
with --calibrate <gym_ws_glob> which fits weights by per-feature class-mean separation
(robust one-shot linear discriminant — no iterative training needed).

Usage:
  classify_players.py replay.json [replay2.json ...]          # per-player scores
  classify_players.py --calibrate ".agario_tourney/ws*"       # refit weights from gym
Output: JSON lines {file, player_id, features, score, label}
"""
import json, math, glob, sys

SAMPLE_EVERY = 5          # sample the tick stream to keep it fast
NEAR = 15.0
# hand-calibrated defaults (gym ground truth 2026-07-10)
WEIGHTS = {"f1": 2.4, "f2": 1.8, "f3": 0.6, "f4": 1.2, "f5": 0.8, "f6": 1.5}
BIAS = -2.8
THRESH = 0.5

def load_events(path):
    d = json.load(open(path))
    return d if isinstance(d, list) else d.get("events", d)

def features(path):
    ev = load_events(path)
    # per-player position/mass timeline (centroid of blobs), sampled
    tick = 0
    pos = {}      # pid -> list[(tick, x, y, mass, n_blobs)]
    kills = {}
    cons = {}
    for e in ev:
        if not isinstance(e, dict):
            continue
        t = e.get("event_type")
        if t == "move_player" and e.get("player_id") == 0:
            tick += 1
        elif t == "event_player_moved":
            b = e.get("blobs") or []
            if b and tick % SAMPLE_EVERY == 0:
                x = sum(q["pos"][0] for q in b) / len(b)
                y = sum(q["pos"][1] for q in b) / len(b)
                m = sum(q["radius"] ** 2 for q in b)
                pos.setdefault(e["player_id"], []).append((tick, x, y, m, len(b)))
        elif t == "event_player_eaten":
            kills[e.get("eater_player_id")] = kills.get(e.get("eater_player_id"), 0) + 1
        elif t == "event_virus_consumed":
            cons[e.get("player_id")] = cons.get(e.get("player_id"), 0) + 1
    out = {}
    pids = list(pos)
    for pid in pids:
        tl = pos[pid]
        if len(tl) < 8:
            continue
        evade = pursue = evade_n = pursue_n = 0
        turns = []
        prev_h = None
        peak = max(p[3] for p in tl)
        final = tl[-1][3]
        for i in range(1, len(tl)):
            t0, x0, y0, m0, _ = tl[i - 1]
            t1, x1, y1, m1, _ = tl[i]
            dx, dy = x1 - x0, y1 - y0
            if abs(dx) + abs(dy) < 1e-6:
                continue
            h = math.atan2(dy, dx)
            if prev_h is not None:
                dh = abs((h - prev_h + math.pi) % (2 * math.pi) - math.pi)
                turns.append(dh)
            prev_h = h
            # nearest other player at same sampled tick
            for q in pids:
                if q == pid:
                    continue
                ql = pos[q]
                # find sample at (approx) same tick
                s = min(ql, key=lambda r: abs(r[0] - t0))
                if abs(s[0] - t0) > SAMPLE_EVERY * 2:
                    continue
                d = math.hypot(s[1] - x0, s[2] - y0)
                if d > NEAR or d < 1e-6:
                    continue
                ux, uy = (s[1] - x0) / d, (s[2] - y0) / d
                dot = (dx * ux + dy * uy) / (math.hypot(dx, dy) + 1e-9)
                if s[3] > m0 * 1.3:
                    evade_n += 1
                    if dot < -0.3:
                        evade += 1
                elif s[3] < m0 * 0.7:
                    pursue_n += 1
                    if dot > 0.3:
                        pursue += 1
        ticks = tl[-1][0] - tl[0][0] + 1
        f = {
            "f1": evade / evade_n if evade_n else 0.0,
            "f2": pursue / pursue_n if pursue_n else 0.0,
            "f3": 1.0 - (sum(turns) / len(turns)) / math.pi if turns else 0.0,
            "f4": min(1.0, 1000.0 * kills.get(pid, 0) / ticks / 10.0),
            "f5": min(1.0, 1000.0 * cons.get(pid, 0) / ticks / 30.0),
            "f6": final / (peak + 1e-9),
        }
        out[pid] = f
    return out

def score(f):
    z = BIAS + sum(WEIGHTS[k] * f[k] for k in WEIGHTS)
    return 1.0 / (1.0 + math.exp(-z))

def calibrate(ws_glob):
    """One-shot LDA-style refit from gym workspaces where slot->bot is known.
    Convention: reads <ws>/seatmap.json {"0":"dumb","1":"intelligent",...} if present,
    else uses default gym layout (last 2 seats dumb)."""
    dumb, smart = [], []
    for ws in glob.glob(ws_glob):
        gj = f"{ws}/output/game.json"
        try:
            fs = features(gj)
        except Exception:
            continue
        try:
            seat = json.load(open(f"{ws}/seatmap.json"))
        except Exception:
            seat = {str(i): ("dumb" if i >= 6 else "intelligent") for i in range(8)}
        for pid, f in fs.items():
            (dumb if seat.get(str(pid)) == "dumb" else smart).append(f)
    if not dumb or not smart:
        print("calibration: insufficient data"); return
    global WEIGHTS, BIAS
    new_w = {}
    for k in WEIGHTS:
        md = sum(f[k] for f in dumb) / len(dumb)
        ms = sum(f[k] for f in smart) / len(smart)
        var = (sum((f[k] - md) ** 2 for f in dumb) + sum((f[k] - ms) ** 2 for f in smart)) / (len(dumb) + len(smart)) + 1e-6
        new_w[k] = (ms - md) / var
    # normalize scale
    mx = max(abs(v) for v in new_w.values()) or 1.0
    WEIGHTS = {k: 3.0 * v / mx for k, v in new_w.items()}
    mid = lambda fs: sum(score(f) for f in fs) / len(fs)
    BIAS_SEARCH = [b / 10.0 for b in range(-60, 20)]
    global BIAS
    best = max(BIAS_SEARCH, key=lambda b: _acc(dumb, smart, b))
    BIAS = best
    print(json.dumps({"weights": WEIGHTS, "bias": BIAS,
                      "dumb_mean": mid(dumb), "smart_mean": mid(smart)}))

def _acc(dumb, smart, b):
    global BIAS
    old = BIAS; BIAS = b
    a = sum(1 for f in dumb if score(f) < THRESH) + sum(1 for f in smart if score(f) >= THRESH)
    BIAS = old
    return a

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--calibrate":
        calibrate(args[1]); sys.exit(0)
    for path in args:
        for pid, f in sorted(features(path).items()):
            s = score(f)
            print(json.dumps({"file": path, "player_id": pid,
                              "features": {k: round(v, 3) for k, v in f.items()},
                              "score": round(s, 3),
                              "label": "intelligent" if s >= THRESH else "dumb"}))
