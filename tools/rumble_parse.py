#!/usr/bin/env python3
# ROYAL-RUMBLE parser: 8 distinct seats, halves A (canonical) + B (reversed order).
# Laws: win = event_player_won only; non-SUCCESS voided; report room composition.
import json, glob, sys, statistics, random

PRES = sys.argv[1] if len(sys.argv) > 1 else ".agario_tourney/rumble200"
NAMES = ["omniB_apex_g627", "omniB_gen576", "omniA_best1_g348", "omniA_best2_g348",
         "v3_legacy", "elite_g30_legacy", "simple_bot", "naive_splitter"]
SLOT = {"A": {s: NAMES[s] for s in range(8)},
        "B": {s: NAMES[7 - s] for s in range(8)}}

def load(p):
    try: return json.load(open(p))
    except Exception: return None

def outcome(ws):
    r = load(f"{ws}/output/results.json")
    return (r.get("result_type") or r.get("result") or "UNKNOWN") if isinstance(r, dict) else "NO_RESULTS"

per_bot = {n: {"mass": [], "wins": 0, "bust": 0, "kills": 0, "games": 0} for n in NAMES}
per_game = []   # {name: mass} per valid game, for paired deltas
voids = timeouts = valid = 0
for half in ("A", "B"):
    for ws in sorted(glob.glob(f"{PRES}/{half}/ws*")):
        gj = load(f"{ws}/output/game.json")
        oc = outcome(ws)
        if gj is None or oc != "SUCCESS":
            voids += 1
            if "TIMEOUT" in str(oc).upper(): timeouts += 1
            continue
        ev = gj if isinstance(gj, list) else gj.get("events", gj)
        fm = {s: 0.0 for s in range(8)}; kills = {s: 0 for s in range(8)}; winner = None
        for e in ev:
            if not isinstance(e, dict): continue
            t = e.get("event_type")
            if t == "event_player_moved":
                b = e.get("blobs") or []
                if b: fm[e.get("player_id")] = sum(x["radius"]**2 for x in b)
            elif t == "event_player_eaten":
                p = e.get("eater_player_id")
                if p in kills: kills[p] += 1
            elif t == "event_player_won":
                winner = e.get("player_id")
        valid += 1
        g = {}
        for s in range(8):
            n = SLOT[half][s]; d = per_bot[n]
            d["mass"].append(fm[s]); d["kills"] += kills[s]; d["games"] += 1
            d["bust"] += fm[s] < 3
            if winner == s: d["wins"] += 1
            g[n] = fm[s]
        per_game.append(g)

def ci(deltas, it=2000):
    if len(deltas) < 3: return (0, 0)
    ms = sorted(sum(random.choice(deltas) for _ in deltas) / len(deltas) for _ in range(it))
    return ms[int(.025 * it)], ms[int(.975 * it)]

print("ROOM (8 seats, 2x100 reversed order): omniB_apex(g627) + omniB_gen576 + 2x omniA best(g348) + v3 + elite_g30 (legacies) + simple_bot + naive_splitter (dumb)")
print(f"valid n={valid}  VOID={voids} (timeout-typed={timeouts})\n")
print("%-18s %6s %6s %5s %5s %7s" % ("bot", "mean", "median", "win%", "bust%", "kills/m"))
for n in sorted(NAMES, key=lambda n: -statistics.mean(per_bot[n]["mass"])):
    d = per_bot[n]
    print("%-18s %6.2f %6.2f %4.0f%% %4.0f%% %7.2f" % (
        n, statistics.mean(d["mass"]), statistics.median(d["mass"]),
        100 * d["wins"] / d["games"], 100 * d["bust"] / d["games"], d["kills"] / d["games"]))

print("\nPAIRED per-game deltas (bootstrap 95% CI):")
for a, b in [("omniB_apex_g627", "omniB_gen576"), ("omniB_apex_g627", "omniA_best1_g348"),
             ("omniB_gen576", "omniA_best1_g348"), ("omniB_gen576", "elite_g30_legacy")]:
    ds = [g[a] - g[b] for g in per_game]
    lo, hi = ci(ds)
    print("  %-34s = %+6.2f  CI[%+.2f,%+.2f]" % (f"{a} - {b}", statistics.mean(ds), lo, hi))
