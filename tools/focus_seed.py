#!/usr/bin/env python3
"""FOCUSED-SEARCH SEEDER (Chris's Machine-1 conversion, 2026-07-10 night).
Builds state.json: pop 20, every individual = gen576 chassis (all genes frozen)
EXCEPT the machine's exposed set. 1 clean + 10 gaussian-local + 9 range-uniform.
Usage: focus_seed.py <exposed_genes.json> <chassis_bot.py> <base_bot.py>
"""
import sys, json, ast, re, random
sys.path.insert(0, "tools")
from pathlib import Path
import evolve_v2 as E

reg_path, chassis_path, base_path = sys.argv[1], sys.argv[2], sys.argv[3]
random.seed(20260711)
reg = {k: v for k, v in json.load(open(reg_path)).items() if not k.startswith("_")}
E.BASE_BOT = Path(base_path)
base = E.read_base_config()
cfg = ast.literal_eval("{" + re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", open(chassis_path).read(), re.S).group(1) + "\n}")
chassis = {k: cfg.get(k, base[k]) for k in base}   # gen576 values; organ genes default where absent
frozen = [k for k in chassis if k not in reg]

def clamp(k, v):
    lo, hi = reg[k]; return min(max(v, lo), hi)

pop = []
g = dict(chassis); g["_FROZEN_SET"] = frozen
pop.append(g)                                                    # 1 clean chassis
for _ in range(10):                                              # 10 local gaussians
    g = dict(chassis)
    for k, (lo, hi) in reg.items():
        g[k] = clamp(k, chassis[k] + random.gauss(0, 0.2 * (hi - lo)))
    g["_FROZEN_SET"] = frozen
    pop.append(g)
for _ in range(9):                                               # 9 range-uniform explorers
    g = dict(chassis)
    for k, (lo, hi) in reg.items():
        g[k] = random.uniform(lo, hi)
    g["_FROZEN_SET"] = frozen
    pop.append(g)
json.dump({"generation": 0, "population": pop, "best": pop[0], "best_mass": 0.0, "best_rank": 9.0},
          open("evolution_v2/state.json", "w"))
print(f"seeded: pop 20 on {chassis_path} chassis | exposed {len(reg)} genes: {sorted(reg)} | frozen {len(frozen)}")
