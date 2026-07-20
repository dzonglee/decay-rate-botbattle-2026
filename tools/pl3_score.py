#!/usr/bin/env python3
"""pl3_score.py — per-cull scorecard for the PL3 carrier campaign (2026-07-17).

Prints every pl3-* genome in the population with window fitness, depth, and
the ON-vs-OFF twin delta per chassis, plus the current pool top-10 for
context. Run at each monitor wake."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
st = json.load(open(ROOT / "evolution_v3" / "state.json"))
pop = st["population"]

rows = []
for g in pop:
    w = g.get("_window") or []
    fit = sum(w) / len(w) if w else 0.0
    rows.append({"id": g.get("_id"), "lin": g.get("_lineage", ""),
                 "fit": fit, "n": len(w), "games": g.get("_games", 0),
                 "anchor": bool(g.get("_anchor")),
                 "pl3on": g.get("PL3_ON", 0), "dial": g.get("PL3_DIAL"),
                 "maxm": g.get("PL3_MAXM")})

rows.sort(key=lambda r: -r["fit"])
print(f"== pool top 10 (cull #{st.get('cull_no')}, match {st.get('match_no')}) ==")
for i, r in enumerate(rows[:10]):
    tag = " <-- PL3" if str(r["lin"]).startswith("pl3") and r["pl3on"] else ""
    print(f"{i+1:>3}. {r['id'] or 'anc':>5} {str(r['lin'])[:30]:30s} "
          f"{r['fit']:6.2f} @w{r['n']:<3} g{r['games']:<4}{tag}")

pl3 = [r for r in rows if str(r["lin"]).startswith("pl3")]
print(f"\n== PL3 carriers in pool: {len(pl3)} ==")
for r in pl3:
    rank = rows.index(r) + 1
    print(f"  #{rank:>2} {r['id']:>5} {r['lin']:22s} fit {r['fit']:6.2f} "
          f"@w{r['n']:<3} games {r['games']:<4} "
          f"(dial {r['dial']} maxm {r['maxm']} on={r['pl3on']})")

# twin deltas per chassis
print("\n== ON-vs-OFF twin deltas (same chassis, same cull) ==")
by = {}
for r in pl3:
    parts = r["lin"].split("-")
    if len(parts) == 3:
        cfg, chas = parts[1], parts[2]
        by.setdefault(chas, {})[cfg] = r
for chas, d in sorted(by.items()):
    off = d.get("off")
    for cfg, r in sorted(d.items()):
        if cfg == "off" or off is None:
            continue
        both = min(r["n"], off["n"])
        note = "" if both >= 75 else "  [!] shallow"
        print(f"  {chas}: {cfg} {r['fit']:6.2f}@w{r['n']} vs off "
              f"{off['fit']:6.2f}@w{off['n']} -> delta {r['fit']-off['fit']:+.2f}{note}")

# graveyard check: culled carriers
try:
    gy = [json.loads(l) for l in open(ROOT / "evolution_v3" / "graveyard.jsonl")
          if "pl3-" in l]
    if gy:
        print(f"\n== culled PL3 carriers: {len(gy)} ==")
        for g in gy[-8:]:
            w = g.get("_window") or []
            fit = sum(w) / len(w) if w else 0.0
            print(f"  {g.get('_id')} {g.get('_lineage')} fit {fit:.2f} "
                  f"games {g.get('_games')}")
except FileNotFoundError:
    pass
