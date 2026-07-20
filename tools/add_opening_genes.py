"""
Inject opening-race genes into a v1-family bot (gen51_organs_off, hybrid, etc.).

Adds five evolvable genes and phase-aware force scaling:
  OPEN_ROUNDS      opening phase length (the race window; live data: decided by ~r400)
  OPEN_GREED       food-force multiplier during the opening (sprint for pellets)
  OPEN_FEAR        threat-force multiplier during the opening (<1 = accept risk)
  EDGE_HUNT_RATIO  radius edge over a neighbour that triggers early hunting
  W_EDGE_HUNT      prey-force multiplier when that edge exists during the opening

Usage: python3 tools/add_opening_genes.py bots/gen51_organs_off.py bots/opener.py
"""

import ast
import re
import sys

NEW_GENES = {
    "OPEN_ROUNDS": 400.0,
    "OPEN_GREED": 2.0,
    "OPEN_FEAR": 0.7,
    "EDGE_HUNT_RATIO": 1.25,
    "W_EDGE_HUNT": 3.0,
}

src_path, dst_path = sys.argv[1], sys.argv[2]
s = open(src_path).read()

# 1. parse CONFIG, add genes, re-render the block
m = re.search(r'CONFIG\s*=\s*\{(.*?)\n\}', s, re.S)
cfg = ast.literal_eval('{' + m.group(1) + '}')
for k, v in NEW_GENES.items():
    cfg.setdefault(k, v)
rendered = "CONFIG = {\n" + "".join(f'    "{k}": {v!r},\n' for k, v in cfg.items()) + "}"
s = s[:m.start()] + rendered + s[m.end():]

# 2. opening-phase flag (anchored on the fresh-mode line present in all v1-family bots)
anchor = 'caution = CONFIG["FRESH_CAUTION"] if fresh else 1.0'
assert anchor in s, "fresh-mode anchor missing"
s = s.replace(anchor, anchor + '''
    # OPENING RACE (live-field finding: the r0-400 pellet race decides who
    # snowballs; winners hit mass 3 ~100 rounds before everyone else and
    # convert the edge into kills immediately)
    opening = st.round < CONFIG["OPEN_ROUNDS"]''')

# 3. food force: sprint multiplier during opening
old = 'f = CONFIG["W_FOOD"] / (d ** CONFIG["FOOD_FALLOFF"] + EPS)'
assert old in s, "food anchor missing"
s = s.replace(old, 'f = (CONFIG["W_FOOD"] * (CONFIG["OPEN_GREED"] if opening else 1.0)) '
                   '/ (d ** CONFIG["FOOD_FALLOFF"] + EPS)')

# 4. threat force: risk acceptance during opening
old = 'f = caution * CONFIG["W_THREAT"] * mass(b.radius) / (d ** CONFIG["THREAT_FALLOFF"] + EPS)'
assert old in s, "threat anchor missing"
s = s.replace(old, 'f = caution * (CONFIG["OPEN_FEAR"] if opening else 1.0) * CONFIG["W_THREAT"] '
                   '* mass(b.radius) / (d ** CONFIG["THREAT_FALLOFF"] + EPS)')

# 5. prey force: edge-triggered early hunting (clone of team 1's r334 first kill)
old = 'f = (CONFIG["W_PREY"] / caution) * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)'
assert old in s, "prey anchor missing"
s = s.replace(old, '''edge = my_largest >= b.radius * CONFIG["EDGE_HUNT_RATIO"]
            hunt_mult = CONFIG["W_EDGE_HUNT"] if (opening and edge) else 1.0
            f = hunt_mult * (CONFIG["W_PREY"] / caution) * mass(b.radius) / (d ** CONFIG["PREY_FALLOFF"] + EPS)''')

ast.parse(s)
open(dst_path, "w").write(s)
print(f"opening genes injected -> {dst_path} ({len(cfg)} CONFIG keys)")
