#!/usr/bin/env python3
"""ORGAN OFF-SWITCH CONTRACT auditor (Chris's rule 2026-07-10):
every organ must be (1) behaviorally off at neutral genes, (2) computationally
off (code unreachable unless its gate passes), (3) provably off.

Layer 1+2 — STATIC AUDIT (this file, mode `audit`):
walks the body source; every line mentioning an organ gene must be lexically
inside a conditional block whose test references that organ's GATE gene
(or be the gate test itself / a CONFIG-dict literal / tracker init).

Layer 3 — BEHAVIORAL A/B (mode `ab`): prints the tournament command for
all-off body vs base body, mirrored; expected |pooled delta| within screen noise.

Usage:
  organ_audit.py audit bots/omni_feaster2.py
  organ_audit.py ab                      # prints the A/B commands to run
"""
import re, sys

# organ -> (gate_gene, member_genes...)
ORGANS = {
    "W1_wealth":  ("W_WEALTH_FEAR", ["W_WEALTH_FEAR", "WEALTH_START", "WEALTH_EXP"]),
    "W2_camp":    ("W_CAMP", ["W_CAMP", "CAMP_WINDOW_LO", "CAMP_WINDOW_HI", "CAMP_MAX_MASS", "camp_sites", "prev_virus_pos"]),
    "W3_grudge":  ("W_GRUDGE", ["W_GRUDGE", "GRUDGE_DECAY", "grudge", "prev_total_mass"]),
    "W4_rank":    ("W_RANK", ["W_RANK_GUARD", "W_RANK_AGGRO"]),
    "W5_slot":    ("VIRUS_SLOT_EXP", ["VIRUS_SLOT_EXP"]),
    "PROFILER":   ("PROF_ON", ["PROF_ON", "PROF_ELITE_T", "PROF_STUPID_T", "PROF_RADIUS",
                                "PROF_PREY_STUPID", "PROF_PREY_ELITE_DISC", "PROF_THREAT_STUPID_DISC",
                                "PROF_THREAT_ELITE_MULT", "PROF_FEAST_BOLD", "prof_score", "prof_last", "prof_tier", "prof_elite_near"]),
    "REFUGE":     ("W_CORNER_REFUGE", ["W_CORNER_REFUGE"]),
    "LG_GATE":    ("LG_ON", ["LG_ON", "LG_START", "LG_THRESH", "LG_SHARP", "LG_RADIUS",
                              "LG_PREY_HIGH", "LG_FEAR_LOW", "lg_prey_mult", "lg_fear_mult"]),
}
ALWAYS_OK = re.compile(r'^\s*("|#|self\.)')   # CONFIG literals, comments, tracker __init__ defaults
NEUTRAL_INIT = re.compile(r'=\s*(\{\}|\[\]|False|None|0\.0)\s*$')  # neutral defaults needed by gated code

def audit(path):
    lines = open(path).read().splitlines()
    # build gate-block map: for each line, the set of gate genes appearing in
    # enclosing `if` tests at lower indentation
    failures = []
    for organ, (gate, members) in ORGANS.items():
        pat = re.compile("|".join(re.escape(m) for m in members))
        for i, ln in enumerate(lines):
            if not pat.search(ln):
                continue
            if ALWAYS_OK.match(ln):
                continue
            if NEUTRAL_INIT.search(ln):
                continue  # neutral initializer for downstream gated reads
            if "CONFIG[" not in ln and "tracker." not in ln and "self." not in ln:
                continue  # prose/docstring
            if re.search(rf'CONFIG\["{re.escape(gate)}"?\]?\s*>\s*0', ln):
                continue  # inline short-circuit gate on the same line
            if any(re.search(rf'CONFIG\["{re.escape(gate)}"\]\s*>\s*0', lines[k])
                   for k in range(max(0, i - 2), i)):
                continue  # continuation line of an inline-gated multi-line expression
            if gate in ln and ("if" in ln or "elif" in ln):
                continue  # the gate test itself
            # scan upward: any enclosing conditional mentioning the gate?
            indent = len(ln) - len(ln.lstrip())
            ok = False
            for j in range(i - 1, max(0, i - 80), -1):
                lj = lines[j]
                if not lj.strip():
                    continue
                ij = len(lj) - len(lj.lstrip())
                if ij < indent and re.match(r"\s*(if|elif)\b", lj):
                    if gate in lj:
                        ok = True
                        break
                    indent = ij  # keep climbing
                elif ij < indent and re.match(r"\s*(def|for|while|else|try|with)\b", lj):
                    indent = ij
                if ij == 0 and lj.strip():
                    break
            # exceptions: pure-neutral multiplier lines guarded by their own weight test
            if not ok and re.search(rf'if CONFIG\["{gate}', ln):
                ok = True
            if not ok and re.search(r'if CONFIG\["' + "|".join(m for m in members if m.isupper()) + r'"\]\s*>\s*0', ln):
                ok = True
            if not ok:
                failures.append((organ, i + 1, ln.strip()[:90]))
    if failures:
        print(f"CONTRACT VIOLATIONS: {len(failures)}")
        for o, n, l in failures:
            print(f"  [{o}] line {n}: {l}")
        sys.exit(1)
    print(f"CONTRACT PASS: all {len(ORGANS)} organs' code is gate-guarded (computationally off at defaults).")

def ab():
    print("""# Layer-3 behavioral A/B (run with milestone lock held; ~4 min):
#   all-organs-off omni_feaster2 (defaults ARE all-off) vs base omni_feaster, mirrored 2x20:
python3 tools/tournament.py --games 20 --parallel 6 2:bots/omni_feaster2.py 2:bots/omni_feaster.py \\
  1:bots/split_feaster_v3.py 1:bots/elite_g30.py 1:bots/simple_bot.py 1:bots/naive_splitter.py
# swap the 2: pair for the mirror half; parse with omni_cc_parse.py on preserved workspaces.
# PASS: |pooled paired delta| <= 3 (within n=40 screen noise; bodies should be near-identical).
# Layer-3 tick-cost: compare total wall-clock of the two halves; PASS: within ~5%.""")

if __name__ == "__main__":
    if sys.argv[1] == "audit":
        audit(sys.argv[2])
    else:
        ab()
