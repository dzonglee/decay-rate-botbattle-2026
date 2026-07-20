"""feastgym-3 milestone parser: mirrored battery (LAW 1) + ban-void (LAW 2).

Usage:
    gym3_batteryparse.py <ELITE_LABEL> <CHAMPION_LABEL> \
        "l0,...,l7::globA"  "l0,...,l7::globB"

Prints per-half + pooled wins/mean_mass, pooled MASS DELTA (elite - champion),
the >+4 law flag, mimic_t1 kill concentration, and voided-game count.
"""
import json, sys, glob, os, statistics, collections

elite, champ = sys.argv[1], sys.argv[2]
pairs = [(a.split("::")[0].split(","), a.split("::")[1]) for a in sys.argv[3:]]

pooled_mass = collections.defaultdict(list)
pooled_wins = collections.Counter()
pooled_mimic = collections.Counter()
voids = []
halves = []
pooled_games = 0

for hi, (labels, pat) in enumerate(pairs):
    h_mass = collections.defaultdict(list); h_wins = collections.Counter(); h_games = 0
    for ws in sorted(glob.glob(pat)):
        rj = os.path.join(ws, "output", "results.json"); gj = os.path.join(ws, "output", "game.json")
        if not os.path.exists(rj):
            continue
        try:
            r = json.load(open(rj))
        except Exception:
            voids.append((ws, "UNREADABLE")); continue
        if r.get("result_type") != "SUCCESS" or "ranking" not in r or "final_masses" not in r:
            voids.append((ws, r.get("result_type", "MALFORMED"))); continue
        h_games += 1; pooled_games += 1
        w = labels[r["ranking"][0]]; h_wins[w] += 1; pooled_wins[w] += 1
        for s in range(8):
            m = r["final_masses"].get(str(s), 0.0)
            h_mass[labels[s]].append(m); pooled_mass[labels[s]].append(m)
        if os.path.exists(gj):
            try:
                for e in json.load(open(gj)):
                    if isinstance(e, dict) and e.get("event_type") == "event_player_eaten" \
                            and labels[e["eater_player_id"]] == "mimic_t1":
                        pooled_mimic[labels[e["eaten_player_id"]]] += 1
            except Exception:
                pass
    halves.append((hi, h_games, h_wins, h_mass))

def table(wins, mass, games):
    for b in sorted(mass, key=lambda b: -statistics.mean(mass[b])):
        print(f"    {b:14} wins={wins[b]:>3}  mean_mass={statistics.mean(mass[b]):>7.2f}")
    print(f"    Sigma wins = {sum(wins.values())}   games = {games}")

for hi, hg, hw, hm in halves:
    tag = f"A (elite@0-1)" if hi == 0 else f"B (champion@0-1)"
    print(f"\n=== MIRROR-HALF {tag} ==="); table(hw, hm, hg)

print(f"\n=== POOLED (n={pooled_games}) ==="); table(pooled_wins, pooled_mass, pooled_games)
me = statistics.mean(pooled_mass[elite]) if pooled_mass[elite] else 0.0
mc = statistics.mean(pooled_mass[champ]) if pooled_mass[champ] else 0.0
delta = me - mc
print(f"\nMASS DELTA ({elite} - {champ}) = {delta:+.2f}")
print(f"LAW FLAG (>+4 pooled): {'FLAGGED' if delta > 4 else 'not flagged'}")
print(f"mimic_t1 kill concentration: {dict(pooled_mimic.most_common())}")
print(f"VOIDED games (ban-void): {len(voids)} -> {voids if voids else 'none'}")
