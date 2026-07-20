#!/usr/bin/env python3
"""FOCUS MILESTONE AUTO-REPORT: fitness stats, exposed-gene distributions with
floor/ceiling pressure, elite genotype, and an n=100 gym battery of the elite
vs the CHASSIS (gen576) — everything the bounds-adjustment review needs."""
import json, subprocess, sys, statistics, os

st = json.load(open("evolution_v2/state.json"))
pop, G = st["population"], st["generation"]
ident = open("config/run_identity.txt").read().strip() if os.path.exists("config/run_identity.txt") else "RUN"
reg_file = [f for f in ("config/exposed_genes_ACTIVE.json",) if os.path.exists(f)]
reg = {k: v for k, v in json.load(open(reg_file[0])).items() if not k.startswith("_")} if reg_file else {}
print(f"[{ident} / gen {G}] FOCUS MILESTONE")
print(f"best_mass(last gen)={st.get('best_mass', 0):.2f}  best_rank={st.get('best_rank', 0):.2f}\n")
print("## Exposed-gene population distributions (floor/ceiling pressure)")
print("| gene | lo | hi | min | median | max | @floor | @ceil |")
print("|---|---|---|---|---|---|---|---|")
for k, (lo, hi) in sorted(reg.items()):
    vals = sorted(g.get(k, 0.0) for g in pop)
    span = hi - lo
    at_lo = sum(1 for v in vals if v <= lo + 0.05 * span)
    at_hi = sum(1 for v in vals if v >= hi - 0.05 * span)
    print(f"| {k} | {lo:g} | {hi:g} | {vals[0]:.2f} | {vals[len(vals)//2]:.2f} | {vals[-1]:.2f} | {at_lo} | {at_hi} |")
print("\n## Elite genotype (exposed genes)")
for k in sorted(reg):
    print(f"  {k:20}= {pop[0].get(k, 0.0):.4g}")
# elite vs chassis battery
print("\n## Elite vs gen576 chassis (gym comparison, n=40)")
sys.stdout.flush()
import re as _re
from pathlib import Path
sys.path.insert(0, "tools")
import evolve_v2 as E
cmd = open(os.path.expanduser("~/Developer/competition/OMNI-evo/omni_resume.cmd")).read() if os.path.exists(os.path.expanduser("~/Developer/competition/OMNI-evo/omni_resume.cmd")) else open("/Users/chrisli/Developer/competition/OMNI-evo/omni_resume.cmd").read()
E.BASE_BOT = Path(_re.search(r"--base (\S+)", cmd).group(1))
E.write_variant(pop[0], Path("bots/FOCUS_elite.py"))
r = subprocess.run(["bash", "tools/omni_gym_compare.sh", "bots/FOCUS_elite.py", f"FOC{G}", "100", "8", "bots/omniB_gen576.py"],
                   capture_output=True, text=True, timeout=1800)
for line in r.stdout.splitlines():
    if any(x in line for x in ("CANDIDATE:", "CHAMPION", "COMPARISON DELTA", "GATE")):
        print(line)
