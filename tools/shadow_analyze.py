#!/usr/bin/env python3
"""Breakdown of shadow_grade JSONL evidence."""
import json, math, random, sys

rows = [json.loads(l) for l in open(sys.argv[1])]
pts = [r for r in rows if 'err' not in r]
errs = [r for r in rows if 'err' in r]
ov = [r for r in pts if r.get('override') and 'adv' in r]

def stats(xs):
    if not xs:
        return "n=0"
    xs_s = sorted(xs)
    m = sum(xs) / len(xs)
    med = xs_s[len(xs) // 2]
    rnd = random.Random(7)
    boots = sorted(
        sum(xs[rnd.randrange(len(xs))] for _ in xs) / len(xs)
        for _ in range(2000))
    return (f"n={len(xs)} mean {m:+.2f} med {med:+.2f} "
            f"CI95[{boots[50]:+.2f},{boots[1949]:+.2f}] "
            f"win {100*sum(x>0 for x in xs)/len(xs):.0f}% "
            f"tie {100*sum(x==0 for x in xs)/len(xs):.0f}%")

print(f"points {len(pts)}  errors {len(errs)}  overrides {len(ov)} "
      f"({100*len(ov)/max(len(pts),1):.0f}%)")
advs = [r['adv'] for r in ov]
print("ALL overrides:  ", stats(advs))
print("threat points:  ", stats([r['adv'] for r in ov if r.get('threat')]))
print("calm points:    ", stats([r['adv'] for r in ov if not r.get('threat')]))
for lo, hi, tag in [(0, 15, "mass<15"), (15, 40, "mass 15-40"), (40, 1e9, "mass>40")]:
    print(f"{tag:15s}:", stats([r['adv'] for r in ov if lo <= r['mass'] < hi]))
bd = sum(r['base_died'] for r in ov); pd = sum(r['plan_died'] for r in ov)
saves = sum(1 for r in ov if r['base_died'] and not r['plan_died'])
kills = sum(1 for r in ov if r['plan_died'] and not r['base_died'])
print(f"deaths: base {bd} planner {pd}  (saves {saves}, planner-caused {kills})")
# excluding death swings: pure mass economy
nod = [r['adv'] for r in ov if not r['base_died'] and not r['plan_died']]
print("no-death subset:", stats(nod))
# prediction calibration
preds = [r['pred_adv'] for r in ov]
mp = sum(preds)/len(preds); ma = sum(advs)/len(advs)
cov = sum((p-mp)*(a-ma) for p, a in zip(preds, advs))
vp = math.sqrt(sum((p-mp)**2 for p in preds)) or 1e-9
va = math.sqrt(sum((a-ma)**2 for a in advs)) or 1e-9
print(f"prediction corr r={cov/(vp*va):+.2f}   "
      f"mean pred {mp:+.2f} vs realized {ma:+.2f}")
# does gating on predicted advantage help? sweep thresholds
print("\nif we only accepted overrides with pred_adv >= T:")
for T in [0.0, 0.5, 1.0, 2.0, 4.0]:
    sub = [r['adv'] for r in ov if r['pred_adv'] >= T]
    print(f"  T={T:4.1f}: {stats(sub)}")
# worst 5 / best 5
ovs = sorted(ov, key=lambda r: r['adv'])
print("\nworst 5:", [(r['m'], r['t'], r['adv'], 'pd' if r['plan_died'] else '') for r in ovs[:5]])
print("best 5: ", [(r['m'], r['t'], r['adv'], 'bs' if r['base_died'] else '') for r in ovs[-5:]])
