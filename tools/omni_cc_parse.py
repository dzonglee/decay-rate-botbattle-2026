#!/usr/bin/env python3
# Champion-challenge parser: candidate vs champion (2 focal each), 4 fixed fillers.
# Reads preserved {dir}/A/ws*/output/{game.json,results.json} (candidate@0-1, champ@2-3)
# and {dir}/B/... (champ@0-1, candidate@2-3). Emits the full promotion metric set.
import json, glob, sys, statistics, math, random
CHAL = sys.argv[1]
CAND_SLOTS = {"A":[0,1], "B":[2,3]}
CHMP_SLOTS = {"A":[2,3], "B":[0,1]}
FILL = [4,5,6,7]

def load(path):
    try: return json.load(open(path))
    except Exception: return None

def outcome(ws):
    r = load(f"{ws}/output/results.json")
    if isinstance(r, dict): return r.get("result_type") or r.get("result") or "UNKNOWN"
    return "NO_RESULTS"

def game_stats(ev):
    """per-slot final_mass, blob-count timeline, kills(by eater w/ victim), winner."""
    fm = {s:0.0 for s in range(8)}; bc = {s:1 for s in range(8)}
    kills = {s:0 for s in range(8)}; kmap = {s:{} for s in range(8)}; winner=None
    for e in ev:
        if not isinstance(e, dict): continue
        et = e.get("event_type")
        if et == "event_player_moved":
            p=e.get("player_id"); b=e.get("blobs") or []
            if b: fm[p]=sum(x["radius"]**2 for x in b); bc[p]=len(b)
        elif et == "event_player_eaten":
            ep=e.get("eater_player_id"); vp=e.get("eaten_player_id")
            if ep in kills: kills[ep]+=1; kmap[ep][vp]=kmap[ep].get(vp,0)+1
        elif et == "event_player_won":
            winner=e.get("player_id")
    return fm, kills, kmap, winner

def collect():
    per_game=[]  # each: dict with half, cand_masses, champ_masses, cand_win, champ_win, ...
    voids=0; timeouts=0; n=0
    for half in ("A","B"):
        cs=CAND_SLOTS[half]; ms=CHMP_SLOTS[half]
        for ws in sorted(glob.glob(f"{CHAL}/{half}/ws*")):
            gj=load(f"{ws}/output/game.json")
            if gj is None: voids+=1; continue
            ev = gj if isinstance(gj,list) else gj.get("events",gj)
            oc = outcome(ws)
            if oc != "SUCCESS":
                voids+=1
                if oc and "TIMEOUT" in str(oc).upper(): timeouts+=1
                continue
            fm,kills,kmap,winner = game_stats(ev)
            n+=1
            g={"half":half,
               "cand_mass":[fm[s] for s in cs], "champ_mass":[fm[s] for s in ms],
               "cand_kills":sum(kills[s] for s in cs), "champ_kills":sum(kills[s] for s in ms),
               "cand_win": 1 if winner in cs else 0, "champ_win": 1 if winner in ms else 0,
               "cand_bust": sum(1 for s in cs if fm[s]<3), "champ_bust": sum(1 for s in ms if fm[s]<3),
               # candidate-on-champion kills & vice-versa
               "c_on_m": sum(kmap[s].get(m,0) for s in cs for m in ms),
               "m_on_c": sum(kmap[s].get(c,0) for s in ms for c in cs)}
            per_game.append(g)
    return per_game, voids, timeouts, n

def boot_ci(deltas, iters=2000):
    if len(deltas)<3: return (0,0)
    means=[]
    for _ in range(iters):
        s=[deltas[int(random.random()*len(deltas))] for _ in deltas]
        means.append(sum(s)/len(s))
    means.sort(); return means[int(0.025*iters)], means[int(0.975*iters)]

def side(games, label):
    if not games:
        print(f"  [{label}] 0 VALID GAMES — HALF VOID (all games missing/non-SUCCESS or workspaces not preserved).")
        print(f"  [{label}] LAW 1 (mirrored halves) violated -> THIS REPORT IS VOID FOR PROMOTION; diagnose + rerun.")
        return None, (0, 0)
    cm=[m for g in games for m in g["cand_mass"]]; mm=[m for g in games for m in g["champ_mass"]]
    seats=2*len(games)
    cw=sum(g["cand_win"] for g in games); mw=sum(g["champ_win"] for g in games)
    cb=sum(g["cand_bust"] for g in games); mb=sum(g["champ_bust"] for g in games)
    ck=sum(g["cand_kills"] for g in games); mk=sum(g["champ_kills"] for g in games)
    com=sum(g["c_on_m"] for g in games); moc=sum(g["m_on_c"] for g in games)
    # paired per-game delta = mean(candidate 2 seats) - mean(champion 2 seats)
    deltas=[statistics.mean(g["cand_mass"])-statistics.mean(g["champ_mass"]) for g in games]
    lo,hi=boot_ci(deltas)
    print(f"  [{label}] games={len(games)} seats/side={seats}")
    print(f"    CANDIDATE  mean_mass={statistics.mean(cm):6.2f} median={statistics.median(cm):6.2f} win={100*cw/len(games):4.0f}% bust={100*cb/seats:3.0f}% kills/match={ck/len(games):5.2f}")
    print(f"    CHAMPION   mean_mass={statistics.mean(mm):6.2f} median={statistics.median(mm):6.2f} win={100*mw/len(games):4.0f}% bust={100*mb/seats:3.0f}% kills/match={mk/len(games):5.2f}")
    print(f"    PAIRED MASS DELTA (cand-champ) = {statistics.mean(deltas):+.2f}  95%CI[{lo:+.2f},{hi:+.2f}]")
    print(f"    head-to-head kills: candidate-on-champion={com}  champion-on-candidate={moc}")
    return statistics.mean(deltas), (lo,hi)

def main():
    games, voids, timeouts, n = collect()
    if not games:
        print("NO VALID GAMES"); return
    A=[g for g in games if g["half"]=="A"]; B=[g for g in games if g["half"]=="B"]
    print("--- SEAT-HALF A (candidate @ slots 0-1) ---"); ra=side(A,"half A")
    print("--- SEAT-HALF B (candidate @ slots 2-3) ---"); rb=side(B,"half B")
    if not A or not B:
        print(f"\n  VOID games={voids}  TIMEOUT-typed voids={timeouts}  valid n={n}")
        print("  REPORT VOID: one mirror half empty -> no pooled delta, no gate. Diagnose and rerun.")
        return
    print("--- POOLED ---"); d,ci=side(games,"pooled")
    print(f"\n  VOID games={voids}  TIMEOUT-typed voids={timeouts}  valid n={n}")
    ship = d>=2.5 and ci[0]>0
    print(f"  PROMOTION GATE (delta>=+2.5 AND CI lower bound>0 at this n): {'ELIGIBLE' if ship else 'not eligible'}  [delta={d:+.2f}]")

main()
