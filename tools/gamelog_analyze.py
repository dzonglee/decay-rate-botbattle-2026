#!/usr/bin/env python3
"""GYM GAMELOG BATCH FORENSIC (Chris's strategy 2026-07-10): every 250 logged
matches, analyze exactly like the real-replay forensics — per-body performance,
virus economy, kill matrix, census tiers, anomalies.

Usage: gamelog_analyze.py <gamelog_dir> <batch_no> <n_latest> > report.md
Reads the newest <n_latest> .json.gz (each = {"meta":{gen,match,seats},"events":[...]}).
"""
import gzip, glob, json, os, sys, statistics, collections

def body_name(spec):
    # "1:/path/variants/gen012_i07.py" -> candidate ; "1:bots/x.py" -> x
    p = spec.split(":", 1)[1]
    b = os.path.basename(p).replace(".py", "")
    return "CANDIDATE" if "/variants/" in p or b.startswith("gen") and "_i" in b else b

def main(d, batch, n):
    files = sorted(glob.glob(f"{d}/*.json.gz"), key=os.path.getmtime)[-n:]
    per = collections.defaultdict(lambda: {"m": [], "peak": [], "cons": 0, "kills": 0, "deaths": 0, "wins": 0, "seats": 0})
    kmatrix = collections.Counter()
    vspawn = []; frames_l = []; bad = 0
    for f in files:
        try:
            d0 = json.load(gzip.open(f, "rt"))
        except Exception:
            bad += 1; continue
        seats = [body_name(s) for s in d0["meta"]["seats"]]
        ev = d0["events"]
        if not isinstance(ev, list): ev = ev.get("events", [])
        fm = {i: 0.0 for i in range(len(seats))}; pk = dict(fm)
        kl = collections.Counter(); dth = collections.Counter(); win = None
        vsp = 0; cons = collections.Counter(); frames = 0
        for e in ev:
            if not isinstance(e, dict): continue
            t = e.get("event_type")
            if t == "move_player" and e.get("player_id") == 0: frames += 1
            elif t == "event_player_moved":
                b = e.get("blobs") or []
                if b:
                    m = sum(x["radius"] ** 2 for x in b)
                    fm[e["player_id"]] = m; pk[e["player_id"]] = max(pk[e["player_id"]], m)
            elif t == "event_player_eaten":
                kl[e.get("eater_player_id")] += 1; dth[e.get("eaten_player_id")] += 1
                ei, vi = e.get("eater_player_id"), e.get("eaten_player_id")
                if ei is not None and vi is not None and ei < len(seats) and vi < len(seats):
                    kmatrix[(seats[ei], seats[vi])] += 1
            elif t == "event_virus_spawned": vsp += 1
            elif t == "event_virus_consumed": cons[e.get("player_id")] += 1
            elif t == "event_player_won": win = e.get("player_id")
        vspawn.append(vsp); frames_l.append(frames)
        for i, nm in enumerate(seats):
            p = per[nm]
            p["m"].append(fm[i]); p["peak"].append(pk[i]); p["cons"] += cons[i]
            p["kills"] += kl[i]; p["deaths"] += dth[i]; p["seats"] += 1
            if win == i: p["wins"] += 1
    print(f"# GYM GAMELOG BATCH {batch} — {len(files)} matches ({bad} unreadable)")
    print(f"[{open('config/run_identity.txt').read().strip() if os.path.exists('config/run_identity.txt') else 'RUN'}]")
    print(f"match length: mean {statistics.mean(frames_l):.0f} frames | virus economy: mean {statistics.mean(vspawn):.1f} spawns/match")
    print(f"\n| body | seats | mean mass | peak | win% | cons/seat | kills/seat | deaths/seat | bank% (final/peak) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for nm, p in sorted(per.items(), key=lambda kv: -statistics.mean(kv[1]["m"])):
        mm = statistics.mean(p["m"]); pkm = statistics.mean(p["peak"])
        print(f"| {nm} | {p['seats']} | {mm:.2f} | {pkm:.2f} | {100*p['wins']/p['seats']:.0f}% | "
              f"{p['cons']/p['seats']:.1f} | {p['kills']/p['seats']:.1f} | {p['deaths']/p['seats']:.2f} | {100*mm/max(pkm,1e-9):.0f}% |")
    print("\ntop kill pairs (eater -> victim):")
    for (a, b), c in kmatrix.most_common(8):
        print(f"  {a} -> {b}: {c}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
