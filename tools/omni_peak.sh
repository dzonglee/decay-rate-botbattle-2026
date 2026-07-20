#!/bin/bash
# OMNI peak archiver (per machine). LIGHTWEIGHT — NO pause: reads state.json and
# materializes the current best genome every 5 gens to OMNI-evo/peaks/ + one
# FINDINGS.md line (best mass + notable gene drift). Safe to run every ~10 min.
set -uo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
OMNI=/Users/chrisli/Developer/competition/OMNI-evo
if [ -x /Users/chrisli/Developer/competition/evolution-2/.venv/bin/simulation ]; then
  VENV=/Users/chrisli/Developer/competition/evolution-2/.venv
else
  VENV=$REPO/.venv
fi
cd "$REPO" || exit 0
source "$VENV/bin/activate"
STATE=evolution_v2/state.json
[ -f "$STATE" ] || exit 0
G=$(python3 -c "import json;print(json.load(open('$STATE'))['generation'])" 2>/dev/null) || exit 0
LP=$(cat mining/omni_last_peak 2>/dev/null || echo 0)
[ "$G" -ge $((LP + 5)) ] || exit 0
mkdir -p "$OMNI/peaks"
python3 - "$G" <<'PY'
import sys, json; sys.path.insert(0,"tools")
from pathlib import Path; import evolve_v2 as E
import re as _re
_cmd=open("/Users/chrisli/Developer/competition/OMNI-evo/omni_resume.cmd").read()
E.BASE_BOT=Path(_re.search(r"--base (\S+)", _cmd).group(1))   # machine-agnostic: matches the running body
G=int(sys.argv[1])
s=json.load(open("evolution_v2/state.json")); b=s["best"]; bm=s.get("best_mass",0.0); br=s.get("best_rank",0.0)
OMNI="/Users/chrisli/Developer/competition/OMNI-evo"
E.write_variant(b, Path(f"{OMNI}/peaks/peak_g{G:03d}.py"))
KEY=["SPLIT_CYCLE_ON","CYCLE_MIN_MASS","CYCLE_TARGET_BLOBS","W_PREY","W_VIRUS_FEAST","W_FRAG_HUNT","W_PIECE_GUARD","STALL_KICK_ON"]
genes=" ".join(f"{k}={b[k]:.2f}" for k in KEY if k in b)
def onoff(b):
    cyc="cycle-ON" if b.get("SPLIT_CYCLE_ON",0)>0.5 else "cycle-OFF"
    hunt="hunter" if b.get("W_PREY",0)>20 else ("feaster" if b.get("W_VIRUS_FEAST",0)>1 else "mixed")
    return f"{cyc}/{hunt}"
open(f"{OMNI}/FINDINGS.md","a").write(f"\n## peak gen {G} — best_mass {bm:.1f} rank {br:.2f} | {onoff(b)} | {genes}\n")
print(f"archived peaks/peak_g{G:03d}.py (best_mass {bm:.1f}, {onoff(b)})")
PY
echo "$G" > mining/omni_last_peak
