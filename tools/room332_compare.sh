#!/bin/bash
# ONE-OFF 3+3+2 battery (Chris's order 2026-07-11): 3x focal + 3 strong + 2 weak,
# candidate vs champion graded in IDENTICAL rooms (gym-comparison doctrine).
# Usage: room332_compare.sh <candidate.py> <champion.py> <TAG> <games-per-side> <parallel>
set -e
cd "$(dirname "$0")/.."
source /Users/chrisli/Developer/competition/evolution-2/.venv/bin/activate
CAND="$1"; CHAMP="$2"; TAG="$3"; PER="${4:-48}"; PAR="${5:-6}"
STRONG1=bots/omniB_gen576.py; STRONG2=bots/A_phase2_g80.py; STRONG3=bots/split_feaster_v3.py
WEAK1=bots/simple_bot.py; WEAK2=bots/naive_splitter.py
PRES="mining/r332_${TAG}_pres"; rm -rf "$PRES"; mkdir -p "$PRES"
REPORT="mining/r332_${TAG}_report.txt"
{
echo "[room332 / laptop / candidate=$(basename $CAND .py)]"
echo "ROOM (both sides, 8 seats): 3x FOCAL + 3 STRONG(gen576, A_phase2_g80, split_feaster_v3) + 2 WEAK(simple_bot, naive_splitter)"
echo "room config: one-off 3+3+2 on CHRIS ORDER 2026-07-11; engine agario-kit 2026.1.13"
echo "candidate : $CAND  sha256=$(shasum -a 256 $CAND | cut -c1-16)"
echo "champion  : $CHAMP  sha256=$(shasum -a 256 $CHAMP | cut -c1-16)"
echo "scoring   : ABSOLUTE mean mass of 3 focal seats; delta = cand - champ, bootstrap 95% CI"
} | tee "$REPORT"
run_side(){
  rm -rf .agario_tourney/ws*
  python3 tools/tournament.py --games "$PER" --parallel "$PAR" \
    3:"$1" 1:"$STRONG1" 1:"$STRONG2" 1:"$STRONG3" 1:"$WEAK1" 1:"$WEAK2" \
    > "mining/r332_${TAG}_$2.log" 2>&1
  for w in .agario_tourney/ws*; do b=$(basename "$w")
    mkdir -p "$PRES/$2_$b/output"
    cp -p "$w/output/results.json" "$w/output/game.json" "$PRES/$2_$b/output/" 2>/dev/null || true
  done
}
run_side "$CAND" CAND
run_side "$CHAMP" CHMP
{
python3 - "$PRES" <<'PY'
import json, glob, sys, statistics, random
P=sys.argv[1]
def side(prefix):
    vals=[]; wins=0; busts=0; cons=0; voids=0; games=0
    for ws in sorted(glob.glob(f"{P}/{prefix}_*")):
        try:
            r=json.load(open(f"{ws}/output/results.json"))
            if (r.get("result_type") or r.get("result"))!="SUCCESS": voids+=1; continue
            ev=json.load(open(f"{ws}/output/game.json"))
        except Exception: voids+=1; continue
        if not isinstance(ev,list): ev=ev.get("events",ev)
        fm={i:0.0 for i in range(8)}; win=None
        for e in ev:
            if not isinstance(e,dict): continue
            t=e.get("event_type")
            if t=="event_player_moved":
                b=e.get("blobs") or []
                if b: fm[e["player_id"]]=sum(x["radius"]**2 for x in b)
            elif t=="event_player_won": win=e.get("player_id")
            elif t=="event_virus_consumed" and e.get("player_id") in (0,1,2): cons+=1
        games+=1
        vals.append(statistics.mean(fm[s] for s in (0,1,2)))
        busts+=sum(1 for s in (0,1,2) if fm[s]<3)
        if win in (0,1,2): wins+=1
    return vals,wins,busts,cons,voids,games
cv,cw,cb,cc,cvo,cg=side("CAND"); mv,mw,mb,mc,mvo,mg=side("CHMP")
def rep(l,v,w,b,c,vo,g):
    print(f"  {l}: games={g} voids={vo} FOCAL mean_mass={statistics.mean(v):6.2f} median={statistics.median(v):6.2f} win={100*w/max(g,1):3.0f}% bust={100*b/(3*max(g,1)):3.0f}% cons/game={c/max(g,1):.1f}")
rep("CANDIDATE",cv,cw,cb,cc,cvo,cg); rep("CHAMPION ",mv,mw,mb,mc,mvo,mg)
d=statistics.mean(cv)-statistics.mean(mv)
boots=[]
for _ in range(2000):
    a=[random.choice(cv) for _ in cv]; b=[random.choice(mv) for _ in mv]
    boots.append(statistics.mean(a)-statistics.mean(b))
boots.sort(); lo,hi=boots[50],boots[1949]
print(f"  ROOM332 DELTA = {d:+.2f}  95%CI[{lo:+.2f},{hi:+.2f}]")
PY
} | tee -a "$REPORT"
touch "$REPORT.done"
