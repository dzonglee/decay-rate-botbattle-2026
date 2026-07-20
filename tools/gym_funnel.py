"""
Gym-realism audit: does our training lobby reproduce the live field's opening
race? Runs N gym matches (standard league lobby), then computes the same
funnel we measured on the live corpus, for the base bot's seats.

Live-field reference (from replays/all, July 7):
  team 1  (apex): mass3 @ r383 (91%), mass6 @ r494 (83%), mass12 @ r550 (57%),
                  first kill r334, 5.9 kills < r400, 34.7 kills/match
  team 35 (us):   mass3 @ r481 (78%), mass6 @ r577 (57%), mass12 @ r692 (33%),
                  first kill r453, 1.7 kills < r400, 14.2 kills/match

Usage: python3 tools/gym_funnel.py bots/my_bot.py 8
"""

import json
import subprocess
import sys
from collections import defaultdict

bot = sys.argv[1] if len(sys.argv) > 1 else "bots/my_bot.py"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 8

t_to = {3: [], 6: [], 12: []}
first_kill, kills_tot, kills_early = [], [], []
played = 0
for i in range(n):
    ws = f"gymcheck/ws{i}"
    subprocess.run(["simulation", "--headless", "--workspace", ws,
                    f"2:{bot}", "2:bots/mimic_p4.py", "2:bots/champion_gen134.py",
                    "1:bots/hungry_shy.py", "1:bots/template_bot.py"],
                   capture_output=True, text=True, timeout=900)
    try:
        data = json.load(open(f"{ws}/output/game.json"))
    except Exception:
        continue
    # bot occupies slots 0 and 1
    for pid in (0, 1):
        played += 1
        rnd = 0; hit = {k: None for k in t_to}; kills = 0; ke = 0; fk = None
        for e in data:
            et = e["event_type"]
            if et == "move_player" and e.get("player_id") == 0:
                rnd += 1
            elif et == "event_player_moved" and e.get("player_id") == pid:
                b = e.get("blobs") or []
                if b:
                    m = sum(x["radius"] ** 2 for x in b)
                    for k in hit:
                        if hit[k] is None and m >= k:
                            hit[k] = rnd
            elif et == "event_player_eaten" and e.get("eater_player_id") == pid:
                kills += 1
                if fk is None:
                    fk = rnd
                if rnd < 400:
                    ke += 1
        for k in hit:
            if hit[k] is not None:
                t_to[k].append(hit[k])
        kills_tot.append(kills); kills_early.append(ke)
        if fk is not None:
            first_kill.append(fk)


def avg(l):
    return sum(l) / len(l) if l else -1


print(f"GYM FUNNEL for {bot} over {played} bot-games:")
for k in (3, 6, 12):
    print(f"  reach mass {k:2d}: avg r{avg(t_to[k]):.0f}  (in {len(t_to[k])}/{played})")
print(f"  first kill: avg r{avg(first_kill):.0f}   kills/match {avg(kills_tot):.1f}   kills<r400 {avg(kills_early):.1f}")
print("Compare against the live reference in this file's docstring: if the gym's")
print("race is slower/gentler than the live field's, the lobby under-prices the opening.")
