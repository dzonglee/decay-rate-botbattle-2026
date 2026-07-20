#!/usr/bin/env python3
"""Build the multi-mode BUNDLE ship: base genome + mode overlays (gene diffs)
+ ELITE_TEAM_IDS. v4 (Chris 2026-07-17 three-lever finals design): modes
0/1/2 + FINAL(7). The 3E slot is RETIRED — _mode_for escalates tally>=3
straight to FINAL, and the boot-time backstop / team-id anomaly also force 7.
Usage: make_bundle.py <base(1E).json> <mode0.json|-> <mode2.json|-> <mode7.json|-> <out.py>
The base genome IS the 1E model (mode-1 overlay stays empty)."""
import ast, json, re, sys
from pathlib import Path
BODY = Path(__file__).resolve().parent.parent / "bots" / "omni_mixer_v3.py"
# MODE-SWITCH elites (Chris 2026-07-17: "compute the top 10 as the elite
# now") = CURRENT top-10 leaderboard team ids, minus us (35). The old
# hard-room-survivor gate is retired for mode IDs. REFRESH from the
# canonical meta_report leaderboard at EVERY build — the list below is the
# 2026-07-17 ~20:20 AEST pull: team(15), Ninja(73), spaghetti(85),
# Washed(1), Bot Battle(5), QwQ(37), Banana(9), imposters(56), OJ(24).
# 2026-07-18 ~13:10 AEST refresh: caseoh(88) + imposters(56) in; OJ(24) out.
ELITE_IDS = (1, 5, 9, 15, 24, 31, 37, 44, 53, 56, 73, 88)  # 2026-07-19: everyone above spaghetti

def numeric(g):
    g = g.get("genes", g)
    return {k: v for k, v in g.items() if not k.startswith("_") and isinstance(v, (int, float)) and not isinstance(v, bool)}

def main(base_p, m0_p, m2_p, m7_p, out_p):
    src = BODY.read_text()
    m = re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S)
    defaults = {k: v for k, v in ast.literal_eval("{" + m.group(1) + "\n}").items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    base = dict(defaults); base.update(numeric(json.load(open(base_p))))
    overlays = {}
    for mode, path in ((0, m0_p), (2, m2_p), (7, m7_p)):
        if path == "-": continue
        g = dict(defaults); g.update(numeric(json.load(open(path))))
        overlays[mode] = {k: round(v, 6) if isinstance(v, float) else v
                          for k, v in g.items() if abs(v - base.get(k, 0)) > 1e-9}
    for k, v in base.items():
        src = re.sub(rf'("{k}":\s*)-?[0-9.]+(?:[eE][+-]?[0-9]+)?', rf"\g<1>{v:.6g}", src, count=1)
    ov_lit = "MODE_OVERLAYS = " + repr({0: overlays.get(0, {}), 1: {}, 2: overlays.get(2, {}),
                                        3: {}, 7: overlays.get(7, {})})   # 3E retired
    src = src.replace("MODE_OVERLAYS = {0: {}, 1: {}, 2: {}, 3: {}, 7: {}}", ov_lit, 1)
    src = src.replace("ELITE_TEAM_IDS = ()", f"ELITE_TEAM_IDS = {ELITE_IDS}", 1)
    Path(out_p).write_text(src)
    print(f"bundle written: {out_p}")
    for mode in (0, 2, 7):
        print(f"  mode{mode} diff: {len(overlays.get(mode, {}))} genes")
    print(f"  base genes: {len(base)} | elite ids: {ELITE_IDS}")

if __name__ == "__main__":
    main(*sys.argv[1:6])
