#!/bin/bash
# GYM-ENVIRONMENT COMPARISON (Chris's order 2026-07-10 — replaces adversarial screens).
# Non-adversarial: candidate and champion are graded SEPARATELY in the IDENTICAL
# gym room (3 focal + anchor + v3 + rotating bench + 1 fodder + 1 LATE-PREDATOR) on ABSOLUTE
# room config changed: naive_splitter -> A_phase3_g140 predator seat, on CHRIS ORDER 2026-07-11 ("go for it";
# rationale: gym had no Banana-grade predator, blinding it to retention value; threat share now 12.5% ~ census 15%)
# mean mass — the live leaderboard's own metric. Comparison delta = candidate - champion.
# Bench rotation balanced: N split evenly across the 4 bench bots, same for both sides.
# Args: $1=candidate $2=tag [$3=N total default 40] [$4=parallel default 6]
set -uo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/simulation ]; then VENV=/Users/chrisli/Developer/competition/evolution-2/.venv; else VENV=$REPO/.venv; fi
cd "$REPO"; source "$VENV/bin/activate"
CAND="$1"; TAG="$2"; N=${3:-40}; PAR=${4:-6}
CHAMP=${5:-$(cat "$REPO/config/current_development_champion.txt")}   # optional $5 = champion override (focus milestones compare vs chassis)
ANCHOR="$CHAMP"   # gym anchor = champion pointer (single source of truth)
BENCH=($(grep -v '^#' "$REPO/config/gym_room.txt"))
PER=$((N / (${#BENCH[@]} * 2)))   # games per (side, bench-bot)
REPORT="mining/gc_${TAG}_report.txt"
PRES=".agario_tourney/gymcmp_${TAG}"; rm -rf "$PRES"; mkdir -p "$PRES"
h(){ shasum -a 256 "$1" 2>/dev/null | cut -c1-16; }
{
echo "[$(cat "$REPO/config/run_identity.txt" 2>/dev/null || echo RUN) / candidate=$(basename "$CAND" .py)]"
echo "=============== GYM-ENVIRONMENT COMPARISON (non-adversarial) ==============="
echo "TEST DOCTRINE  : Chris's order 2026-07-10 — absolute accumulation in the census gym"
echo "                 room, candidate vs champion graded separately in IDENTICAL rooms."
echo "                 Replaces the adversarial 2+2+2+2 courtroom for milestones."
echo "candidate      : $CAND   sha256=$(h "$CAND")"
echo "champion       : $CHAMP   sha256=$(h "$CHAMP")"
echo "ROOM (both sides, 8 seats): 3x FOCAL + anchor($(basename $ANCHOR .py)) + split_feaster_v3 + 1 bench + simple_bot + PREDATOR(A_phase3_g140)"
echo "bench rotation : ${BENCH[*]} — $PER games per (side, bench bot); total $N"
echo "scoring        : ABSOLUTE mean mass of the 3 focal seats (live-leaderboard metric)"
echo "                 comparison delta = candidate mean - champion mean, bootstrap 95% CI"
echo "void rule      : non-SUCCESS voided (LAW 2); wins informational (event_player_won)"
echo "============================================================================="
} | tee "$REPORT"
run_side(){ # $1=bot $2=side-label
  for B in "${BENCH[@]}"; do
    rm -rf .agario_tourney/ws*
    python3 tools/tournament.py --games "$PER" --parallel "$PAR" \
      3:"$1" 1:"$ANCHOR" 1:bots/split_feaster_v3.py 1:"$B" 1:bots/simple_bot.py 1:bots/A_phase3_g140.py \
      > "mining/gc_${TAG}_$2_$(basename $B .py).log" 2>&1
    for w in .agario_tourney/ws*; do b=$(basename "$w")
      mkdir -p "$PRES/$2_$(basename $B .py)_$b/output"
      cp -p "$w/output/results.json" "$w/output/game.json" "$PRES/$2_$(basename $B .py)_$b/output/" 2>/dev/null || true
    done
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
print(f"  GYM COMPARISON DELTA = {d:+.2f}  95%CI[{lo:+.2f},{hi:+.2f}]")
print(f"  GATE (delta>=+2.5 AND CI lower>0 at n>=100): {'ELIGIBLE' if d>=2.5 and lo>0 else 'not eligible'}  [delta={d:+.2f}]")
PY
} >> "$REPORT" 2>&1
tail -5 "$REPORT"
echo DONE > "mining/gc_${TAG}.done"
echo "[gym-compare $TAG] report -> $REPORT"
