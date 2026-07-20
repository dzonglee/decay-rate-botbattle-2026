#!/usr/bin/env python3
"""meta_report.py — the canonical live-meta analysis (room composition, our
performance, per-submission comparison). Runs FROM the laptop; data lives on
the Mac Studio (Hermes cache). Any agent can run this — see OPERATOR.md §4.

The report includes Chris's preferred elite head-to-head table: for each of
our submissions, non-successful/ban rows plus each current elite opponent's
times faced, times we placed above them, and above percentage.
It also compares every current elite's latest submission within the selected
era, including a separate 2E+ opponent cell, so old leaderboard buffers do not
decide who is currently strongest in the hard world.

Usage:
  python3 tools/meta_report.py                 # refresh cache via Hermes, then report (DEFAULT)
  python3 tools/meta_report.py --no-extend     # report from cached metadata only
  python3 tools/meta_report.py --since 28343   # override analysis start id
  python3 tools/meta_report.py --windows 4     # number of equal id-windows

Rule (Chris 2026-07-16): meta analysis ALWAYS pulls the latest results first —
extending is cheap (seconds), stale data is not. Hence extend-by-default.

Data + schema (Studio):
  /tmp/match_meta.jsonl    one JSON per line: {id, createdDate(UTC), outcome,
                           banReason, bannedSubmissionId, participants:[{teamId,
                           teamName, submissionId, ranking}]}  ranking 0 = WIN.
  /tmp/leaderboard_now.json  [{teamName, avgMass, numMatches}] — avgMass is for
                           the team's CURRENT submission only.
  /tmp/meta_extend.py      extends the cache through Hermes (headless Chrome
                           CDP :9222, logged-in syncs.org.au session; batches
                           of 25 ids until 24x404 = caught up).

Standards (see ASSISTANT.md): tiers by CURRENT leaderboard avg E>20 / C 10-20
/ G<10; we are teamId 35; quote n everywhere; small cells are noise; times to
Chris in AEST (UTC+10). Studio sims are paused during the remote work and
ALWAYS resumed (pause-gym law).

TIME-CONFOUNDING GUARD (lesson 2026-07-16): when comparing an old submission
to a new one, NEVER use the old sub's full history — the live meta drifts, so
a long-lived sub's aggregate mixes eras and inflates apparent composition
"steps" at the upload boundary. Set --since so the report covers only the
overlap era (the old sub's final slice + the new sub), e.g.
`--since <old_sub_last_id - ~300>`. Streaks are also selection: a hot run at
the end of a 40%-win tail is expected variance, not a performance level.
"""
import argparse, subprocess, sys

STUDIO = "chrisli@100.102.72.37"

REMOTE = r'''
import json, sys
from collections import Counter, defaultdict
SINCE = __SINCE__
NWIN = __NWIN__
ETHR = __ETHR__
LOOKBACK = __LOOKBACK__
SHIP_IDS = set(__SHIP_IDS__)
LIFECYCLE_SID = __LIFECYCLE_SID__
LIFECYCLE_WINDOWS = __LIFECYCLE_WINDOWS__
REAL_LOOKBACK = __REAL_LOOKBACK__
recs = {}
all_recs = {}
team_ids = {}
all_latest = {}
for l in open("/tmp/match_meta.jsonl"):
    r = json.loads(l)
    if "participants" in r:
        all_recs[r["id"]] = r
        for p in r["participants"]:
            team_ids[p["teamName"]] = p["teamId"]
            all_latest[p["teamName"]] = (p["submissionId"], r["id"])
        if r["id"] >= SINCE:
            recs[r["id"]] = r
if not recs:
    sys.exit("no records since __SINCE__ — run with --extend or lower --since")
lb = json.load(open("/tmp/leaderboard_now.json"))
avg = {t["teamName"]: t["avgMass"] for t in lb}
elite_names = {t["teamName"] for t in lb if t["avgMass"] > ETHR}
def tier(n):
    a = avg.get(n)
    return "E" if a and a > ETHR else ("C" if a and a >= 10 else "G")
def successful(r):
    outcome = str(r.get("outcome", "")).strip().lower()
    ban_reason = str(r.get("banReason", "")).strip().lower()
    return (outcome in {"success", "successful"}
            and ban_reason in {"", "none", "null"}
            and r.get("bannedSubmissionId") is None)

lo, hi = min(recs), max(recs)
step = max(1, (hi - lo + 1) // NWIN)
print(f"cache: ids {lo}-{hi} ({len(recs)} matches), latest {recs[hi]['createdDate'][:19]}Z")
print(f"\n== room composition by window (tiers by CURRENT leaderboard avg) ==")
print(f"{'window':>15} {'games':>5} | E/C/G per room | teams | ourG  opp-E 0/1/2/3+ | win% rank")
for w in range(NWIN):
    a, b = lo + w * step, (lo + (w + 1) * step) if w < NWIN - 1 else hi + 1
    ids = [i for i in recs if a <= i < b]
    if not ids: continue
    teams = set(); e = c = g = 0; ourh = Counter(); our = []
    for i in ids:
        parts = recs[i]["participants"]
        names = [p["teamName"] for p in parts]
        teams.update(names)
        tl = [tier(n) for n in names]
        e += tl.count("E"); c += tl.count("C"); g += tl.count("G")
        us = next((p for p in parts if p["teamId"] == 35), None)
        if us:
            oe = sum(1 for p in parts if p["teamId"] != 35 and tier(p["teamName"]) == "E")
            ourh[min(oe, 3)] += 1; our.append(us["ranking"])
    n = len(ids); m = len(our)
    winr = f"{100*sum(1 for r in our if r == 0)/m:.0f}%" if m else "-"
    mr = f"{sum(our)/m:.2f}" if m else "-"
    print(f"{a:>7}-{b-1:<7} {n:>5} | {e/n:.2f}/{c/n:.2f}/{g/n:.2f} | {len(teams):>3}  | {m:>4}  "
          f"{ourh[0]}/{ourh[1]}/{ourh[2]}/{ourh[3]} | {winr} {mr}")

print(f"\n== our submissions (teamId 35) since {SINCE} ==")
subs = defaultdict(list)
for i, r in recs.items():
    us = next((p for p in r["participants"] if p["teamId"] == 35), None)
    if us:
        oe = sum(1 for p in r["participants"] if p["teamId"] != 35 and tier(p["teamName"]) == "E")
        subs[us["submissionId"]].append((i, us["ranking"], oe, r["createdDate"]))
for sid, gms in sorted(subs.items()):
    gms.sort()
    rks = [x[1] for x in gms]; n = len(gms)
    print(f"\nsub {sid}: {n} games, ids {gms[0][0]}-{gms[-1][0]}, "
          f"{gms[0][3][:16]}Z -> {gms[-1][3][:16]}Z")
    print(f"  win {100*sum(1 for r in rks if r == 0)/n:.0f}%  mean rank {sum(rks)/n:.2f}"
          + ("   [!] n<150 — do not judge" if n < 150 else ""))
    for e in (0, 1, 2, 3):
        cell = [x for x in gms if min(x[2], 3) == e]
        if cell:
            w = sum(1 for x in cell if x[1] == 0)
            print(f"    {e}E rooms: n={len(cell):>4}  win {100*w/len(cell):.0f}%  "
                  f"mean rank {sum(x[1] for x in cell)/len(cell):.2f}"
                  + ("  [!]" if len(cell) < 30 else ""))

if LIFECYCLE_SID is not None:
    life = sorted(subs.get(LIFECYCLE_SID, []))
    print(f"\n== sub {LIFECYCLE_SID} full lifecycle: exact 2E vs 3E+ ==")
    print("Rooms are reclassified using TODAY's elite band; slices contain equal numbers "
          "of this submission's games, not equal match-id spans.")
    if not life:
        print("  no games in selected --since range")
    else:
        print(f"{'slice':>5} {'ids':>15} {'all n':>5} | {'2E win@n/rank':>16} | "
              f"{'3E+ win@n/rank':>17}")
        def life_cell(cell):
            if not cell:
                return "-"
            wins = sum(1 for x in cell if x[1] == 0)
            return f"{100*wins/len(cell):.0f}%@{len(cell)}/{sum(x[1] for x in cell)/len(cell):.2f}"
        for w in range(LIFECYCLE_WINDOWS):
            a = len(life) * w // LIFECYCLE_WINDOWS
            b = len(life) * (w + 1) // LIFECYCLE_WINDOWS
            sl = life[a:b]
            if not sl:
                continue
            two = [x for x in sl if x[2] == 2]
            three = [x for x in sl if x[2] >= 3]
            print(f"{w+1:>5} {sl[0][0]:>7}-{sl[-1][0]:<7} {len(sl):>5} | "
                  f"{life_cell(two):>16} | {life_cell(three):>17}")
        two = [x for x in life if x[2] == 2]
        three = [x for x in life if x[2] >= 3]
        print(f"{'ALL':>5} {life[0][0]:>7}-{life[-1][0]:<7} {len(life):>5} | "
              f"{life_cell(two):>16} | {life_cell(three):>17}")

print(f"\n== current-sub metadata 2E vs live-bundle recognizable elites ==")
print("Metadata E counts room presence. Recognizable E is only an upper bound: "
      "the bundle must still sight each team before switching modes.")
latest_sid = max(subs, key=lambda sid: max(x[0] for x in subs[sid]))
two_e = []
for i, r in sorted(recs.items()):
    us = next((p for p in r["participants"]
               if p["teamId"] == 35 and p["submissionId"] == latest_sid), None)
    if not us:
        continue
    current_e = sum(1 for p in r["participants"]
                    if p["teamId"] != 35 and tier(p["teamName"]) == "E")
    if current_e != 2:
        continue
    recognizable_e = sum(1 for p in r["participants"]
                         if p["teamId"] != 35 and p["teamId"] in SHIP_IDS)
    two_e.append((us["ranking"], recognizable_e))
print(f"sub {latest_sid}: current-tier 2E n={len(two_e)}; "
      f"bundle elite ids={','.join(str(x) for x in sorted(SHIP_IDS))}")
for e in range(3):
    cell = [x for x in two_e if min(x[1], 2) == e]
    if not cell:
        continue
    wins = sum(1 for rank, _ in cell if rank == 0)
    print(f"  bundle-recognizable {e}{'+' if e == 2 else ''}E: n={len(cell):>4}  "
          f"win {100*wins/len(cell):.0f}%  "
          f"mean rank {sum(rank for rank, _ in cell)/len(cell):.2f}"
          + ("  [!]" if len(cell) < 30 else ""))

print(f"\n== current-sub exact-2E outcome by elite identity ==")
print("Each exact-2E game appears once for each of its two elite opponents.")
print(f"{'opponent':<24} {'n':>4} {'our win':>8} {'our rank':>9} {'we placed above':>16}")
for name in sorted(elite_names):
    cell = []
    for i, r in sorted(recs.items()):
        us = next((p for p in r["participants"]
                   if p["teamId"] == 35 and p["submissionId"] == latest_sid), None)
        them = next((p for p in r["participants"] if p["teamName"] == name), None)
        if not us or not them or name == "Decay Rate":
            continue
        current_e = sum(1 for p in r["participants"]
                        if p["teamId"] != 35 and tier(p["teamName"]) == "E")
        if current_e == 2:
            cell.append((us["ranking"], them["ranking"]))
    if cell:
        n = len(cell); wins = sum(1 for ur, _ in cell if ur == 0)
        above = sum(1 for ur, tr in cell if ur < tr)
        print(f"{name:<24} {n:>4} {100*wins/n:>7.0f}% "
              f"{sum(ur for ur, _ in cell)/n:>9.2f} {above:>6}/{n:<4} ({100*above/n:.0f}%)"
              + ("  [!]" if n < 30 else ""))

print(f"\n== elite head-to-head since {SINCE} (current elite band) ==")
for sid in sorted(subs):
    rows = []
    bad = ours_banned = 0
    faced = Counter(); above = Counter()
    for i, r in sorted(recs.items()):
        us = next((p for p in r["participants"]
                   if p["teamId"] == 35 and p["submissionId"] == sid), None)
        if not us:
            continue
        rows.append(r)
        banned_sid = r.get("bannedSubmissionId")
        is_bad = not successful(r)
        bad += int(is_bad)
        ours_banned += int(banned_sid is not None and str(banned_sid) == str(sid))
        for p in r["participants"]:
            if p["teamId"] != 35 and p["teamName"] in elite_names:
                faced[p["teamName"]] += 1
                above[p["teamName"]] += int(us["ranking"] < p["ranking"])
    print(f"\nsub {sid}: {len(rows)} games | non-successful/ban rows: {bad} "
          f"(ours banned: {ours_banned})")
    print("   elite opponents faced (times | we placed above them):")
    for name, n in sorted(faced.items(), key=lambda kv: (-kv[1], kv[0])):
        a = above[name]
        print(f"     {name:<24} {n:>3} | above {a:>3} ({100*a/n:.0f}%)"
              + ("  [!]" if n < 30 else ""))

print(f"\n== current elite submissions in this era (hard-world placement proxy) ==")
elite_perf = []
for name in elite_names:
    if name not in all_latest:
        continue
    sid = all_latest[name][0]
    rows = []
    bad = 0
    for i, r in sorted(recs.items()):
        me = next((p for p in r["participants"]
                   if p["teamName"] == name and p["submissionId"] == sid), None)
        if not me:
            continue
        if not successful(r):
            bad += 1
            continue
        oe = sum(1 for p in r["participants"]
                 if p["teamName"] != name and tier(p["teamName"]) == "E")
        rows.append((me["ranking"], oe))
    hard = [x for x in rows if x[1] >= 2]
    all_win = sum(1 for rank, _ in rows if rank == 0) / len(rows) if rows else -1
    all_rank = sum(rank for rank, _ in rows) / len(rows) if rows else 99
    hard_win = sum(1 for rank, _ in hard if rank == 0) / len(hard) if hard else -1
    hard_rank = sum(rank for rank, _ in hard) / len(hard) if hard else 99
    cells = [[x for x in rows if min(x[1], 3) == e] for e in range(4)]
    elite_perf.append((name, sid, rows, hard, bad, all_win, all_rank,
                       hard_win, hard_rank, cells))
print(f"{'team':<24} {'sub':>5} {'n':>4} {'bad':>3} | {'all win/rank':>14} | "
      f"{'2E+ n':>5} {'win/rank':>10}")
for name, sid, rows, hard, bad, aw, ar, hw, hr, cells in sorted(
        elite_perf, key=lambda x: (-x[7], x[8], -len(x[3]))):
    all_s = f"{100*aw:.0f}%/{ar:.2f}" if rows else "-"
    hard_s = f"{100*hw:.0f}%/{hr:.2f}" if hard else "-"
    print(f"{name:<24} {sid:>5} {len(rows):>4} {bad:>3} | {all_s:>14} | "
          f"{len(hard):>5} {hard_s:>10}"
          + ("  [!]" if len(hard) < 30 else ""))

print(f"\n== mode-switch REAL elites (hard-room survivor gate) ==")
print(f"Candidate must have current leaderboard avg > threshold. Sample is current-first "
      f"n={REAL_LOOKBACK}: use current-submission games first, then backfill the missing "
      "games from immediately prior submissions. Gate: hard n>=100, hard win>=18.75% "
      "(1.5x random), hard mean rank<=3.00. Us is excluded.")
real_elites = []
for name in sorted(elite_names, key=lambda n: -avg.get(n, -1)):
    if name == "Decay Rate":
        continue
    sid = all_latest.get(name, (None, None))[0]
    history = []
    for i, r in sorted(all_recs.items()):
        me = next((p for p in r["participants"] if p["teamName"] == name), None)
        if not me or not successful(r):
            continue
        oe = sum(1 for p in r["participants"]
                 if p["teamName"] != name and tier(p["teamName"]) == "E")
        history.append((me["ranking"], oe, i, me["submissionId"]))
    current = [x for x in history if x[3] == sid]
    current_take = current[-REAL_LOOKBACK:]
    need = max(0, REAL_LOOKBACK - len(current_take))
    prior = [x for x in history if x[3] != sid and (not current or x[2] < current[0][2])]
    prior_take = prior[-need:] if need else []
    sample = prior_take + current_take
    hard = [x for x in sample if x[1] >= 2]
    hw = sum(1 for x in hard if x[0] == 0) / len(hard) if hard else -1
    hr = sum(x[0] for x in hard) / len(hard) if hard else 99
    reasons = []
    if len(sample) < REAL_LOOKBACK: reasons.append(f"team n={len(sample)}<{REAL_LOOKBACK}")
    if len(hard) < 100: reasons.append(f"hard n={len(hard)}<100")
    if hard and hw < 0.1875: reasons.append(f"hard win={100*hw:.0f}%<18.75%")
    if hard and hr > 3.0: reasons.append(f"hard rank={hr:.2f}>3.00")
    if not hard: reasons.append("no hard rows")
    if reasons:
        print(f"  REJECT id={str(team_ids.get(name, '?')):>3} {name:<24} "
              + "; ".join(reasons))
    else:
        tid = team_ids.get(name)
        if tid is not None:
            real_elites.append(tid)
        print(f"  ACCEPT id={str(tid):>3} {name:<24} "
              f"hard {100*hw:.0f}%@{len(hard)} rank {hr:.2f} "
              f"[current {len(current_take)} + prior {len(prior_take)}]")
        continue
    print(f"         sample current {len(current_take)} + prior {len(prior_take)}; "
          f"hard {('-' if not hard else f'{100*hw:.0f}%@{len(hard)} rank {hr:.2f}')}")
print("  bundle ids: " + repr(tuple(real_elites)))

print(f"\n== current elite win rate by opponent-elite count since {SINCE} ==")
print(f"{'team':<24} {'sub':>5} {'all':>10} {'0E':>12} {'1E':>12} {'2E':>12} {'3E+':>12}")
def cell_s(cell):
    if not cell:
        return "-"
    n = len(cell); w = sum(1 for x in cell if x[0] == 0)
    return f"{100*w/n:.0f}%@{n}" + ("!" if n < 30 else "")
for name, sid, rows, hard, bad, aw, ar, hw, hr, cells in sorted(
        elite_perf, key=lambda x: -avg.get(x[0], -1)):
    all_s = cell_s(rows)
    print(f"{name:<24} {sid:>5} {all_s:>10} "
          + " ".join(f"{cell_s(cell):>12}" for cell in cells))

print(f"\n== current elites: last {LOOKBACK} team games across submissions ==")
print("Past games are reclassified using TODAY's elite band; rows intentionally mix submissions/eras.")
print(f"{'team':<24} {'n':>4} {'subs':>4} {'all':>10} {'0E':>12} {'1E':>12} {'2E':>12} {'3E+':>12}")
rolling_rows = {}
for name in sorted(elite_names, key=lambda n: -avg.get(n, -1)):
    rows = []
    for i, r in sorted(all_recs.items()):
        me = next((p for p in r["participants"] if p["teamName"] == name), None)
        if not me or not successful(r):
            continue
        oe = sum(1 for p in r["participants"]
                 if p["teamName"] != name and tier(p["teamName"]) == "E")
        rows.append((me["ranking"], oe, i, me["submissionId"]))
    rows = rows[-LOOKBACK:]
    rolling_rows[name] = rows
    cells = [[x for x in rows if min(x[1], 3) == e] for e in range(4)]
    subs_n = len({x[3] for x in rows})
    print(f"{name:<24} {len(rows):>4} {subs_n:>4} {cell_s(rows):>10} "
          + " ".join(f"{cell_s(cell):>12}" for cell in cells))

print(f"\n== current elites: farming dependence / hard-room robustness ==")
print("Soft = 0-1 OTHER elites; hard = 2+ OTHER elites. This measures robustness, "
      "not the hidden mechanism (defence/aggression).")
print(f"{'team':<24} {'soft win@n':>12} {'hard win@n':>12} {'hard-soft':>10}")
def rate_n(cell):
    if not cell:
        return -1, 0
    return sum(1 for x in cell if x[0] == 0) / len(cell), len(cell)
for name in sorted(elite_names, key=lambda n: -avg.get(n, -1)):
    rows = rolling_rows.get(name, [])
    soft = [x for x in rows if x[1] <= 1]
    hard = [x for x in rows if x[1] >= 2]
    sr, sn = rate_n(soft); hr, hn = rate_n(hard)
    ss = f"{100*sr:.0f}%@{sn}" if sn else "-"
    hs = f"{100*hr:.0f}%@{hn}" if hn else "-"
    delta = f"{100*(hr-sr):+.0f}pp" if sn and hn else "-"
    print(f"{name:<24} {ss:>12} {hs:>12} {delta:>10}")

print(f"\n== elite band now (leaderboard avg > {ETHR:g}; avg is per CURRENT sub) ==")
for t in sorted([t for t in lb if t["avgMass"] > ETHR], key=lambda t: -t["avgMass"]):
    tid = team_ids.get(t["teamName"], "?")
    print(f"  id={str(tid):>3}  {t['teamName']:<24} {t['avgMass']:5.1f} @ n={t['numMatches']}")
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extend", dest="extend", action="store_true", default=True,
                    help="refresh cache via Hermes first (DEFAULT)")
    ap.add_argument("--no-extend", dest="extend", action="store_false",
                    help="skip the refresh, use cached metadata")
    ap.add_argument("--since", type=int, default=28343, help="analysis start id (default: post-freeze era)")
    ap.add_argument("--windows", type=int, default=4)
    ap.add_argument("--elite-threshold", type=float, default=20,
                    help="CURRENT leaderboard avgMass cutoff; elite means strictly above (default: 20)")
    ap.add_argument("--team-lookback", type=int, default=500,
                    help="rolling games per current elite across submissions (default: 500)")
    ap.add_argument("--ship-elite-ids", default="85,5,59,1,9,73",
                    help="team ids recognized by the currently uploaded bundle")
    ap.add_argument("--lifecycle-submission", type=int,
                    help="print chronological exact-2E and 3E+ slices for one of our submissions")
    ap.add_argument("--lifecycle-windows", type=int, default=6,
                    help="equal-game slices in the lifecycle section (default: 6)")
    ap.add_argument("--real-elite-lookback", type=int, default=300,
                    help="current-first games per team for mode-elite gate (default: 300)")
    args = ap.parse_args()
    ship_ids = tuple(int(x.strip()) for x in args.ship_elite_ids.split(",") if x.strip())

    def studio(cmd, **kw):
        return subprocess.run(["ssh", "-o", "ConnectTimeout=15", STUDIO, cmd],
                              text=True, **kw)

    if args.extend:
        r = studio('pkill -STOP -f "bin/simulation"; /usr/bin/python3 /tmp/meta_extend.py; '
                   'pkill -CONT -f "bin/simulation"', capture_output=True)
        print(r.stdout.strip() or r.stderr.strip())

    script = (REMOTE.replace("__SINCE__", str(args.since))
                    .replace("__NWIN__", str(args.windows))
                    .replace("__ETHR__", str(args.elite_threshold))
                    .replace("__LOOKBACK__", str(args.team_lookback))
                    .replace("__SHIP_IDS__", repr(ship_ids))
                    .replace("__LIFECYCLE_SID__", repr(args.lifecycle_submission))
                    .replace("__LIFECYCLE_WINDOWS__", str(args.lifecycle_windows))
                    .replace("__REAL_LOOKBACK__", str(args.real_elite_lookback)))
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=15", STUDIO,
                        'pkill -STOP -f "bin/simulation"; /usr/bin/python3 -; '
                        'pkill -CONT -f "bin/simulation"'],
                       input=script, text=True)
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
