"""
Autopsy a match replay (local output/game.json or a portal
visualiser_forwards_differential.json — same event schema).

Usage:
    python3 tools/autopsy.py replays/match30.json --me 5
    python3 tools/autopsy.py .agario/simulation/output/game.json --me 0

Prints: final result, your death/kill ledger, mass trajectory checkpoints,
and a one-line failure-mode diagnosis per death.
"""

import argparse
import json
import math
from collections import defaultdict

ARENA = 60.0


def load_events(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("events", [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("--me", type=int, required=True, help="your player_id in this match")
    args = ap.parse_args()

    events = load_events(args.replay)
    me = args.me

    round_no = 0
    max_rounds = 1400
    # last known position/mass per player (from event_player_moved)
    mass_of: dict[int, float] = defaultdict(float)
    pos_of: dict[int, tuple[float, float]] = {}
    blobs_of: dict[int, int] = defaultdict(int)
    my_traj: list[tuple[int, float, int]] = []  # (round, mass, blob_count)
    deaths: list[dict] = []
    kills: list[dict] = []
    splits_me = 0

    for e in events:
        et = e.get("event_type")
        if et == "event_game_started":
            max_rounds = e.get("max_rounds", 1400)
            for p in e.get("players", []):
                mass_of[p["player_id"]] = p["radius"] ** 2
                pos_of[p["player_id"]] = tuple(p["pos"])
        elif et == "move_player":
            if e.get("player_id") == me and e.get("split"):
                splits_me += 1
            if e.get("player_id") == 0:
                round_no += 1  # crude round counter: first mover each round
        elif et == "event_player_moved":
            pid = e.get("player_id")
            blobs = e.get("blobs") or []
            if blobs:
                m = sum(b["radius"] ** 2 for b in blobs)
                mass_of[pid] = m
                bx = sum(b["pos"][0] * b["radius"] ** 2 for b in blobs) / m
                by = sum(b["pos"][1] * b["radius"] ** 2 for b in blobs) / m
                pos_of[pid] = (bx, by)
                blobs_of[pid] = len(blobs)
            if pid == me and blobs:
                my_traj.append((round_no, mass_of[me], len(blobs)))
        elif et == "event_player_eaten":
            eater, eaten = e.get("eater_player_id"), e.get("eaten_player_id")
            rec = {
                "round": round_no,
                "eater": eater,
                "eaten": eaten,
                "my_mass": mass_of.get(me, 0.0),
                "their_mass": mass_of.get(eater if eaten == me else eaten, 0.0),
                "pos": pos_of.get(eaten),
                "my_blobs": blobs_of.get(me, 1),
            }
            if eaten == me:
                deaths.append(rec)
            elif eater == me:
                kills.append(rec)

    # ---- report ----
    print(f"rounds seen ~{round_no}/{max_rounds}   my splits submitted: {splits_me}")
    print(f"kills: {len(kills)}   deaths: {len(deaths)}")

    if my_traj:
        n = len(my_traj)
        for frac in (0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
            r, m, b = my_traj[min(int(n * frac) - 1, n - 1)]
            print(f"  ~round {r:4d}: mass {m:7.2f}  blobs {b}")
        peak = max(my_traj, key=lambda t: t[1])
        print(f"  peak mass {peak[1]:.2f} at ~round {peak[0]}")
        print(f"  FINAL mass {my_traj[-1][1]:.2f} at ~round {my_traj[-1][0]}  <-- leaderboard metric")

    for i, d in enumerate(deaths):
        frac = d["round"] / max_rounds
        wall = ""
        if d["pos"]:
            dist_wall = min(d["pos"][0], d["pos"][1], ARENA - d["pos"][0], ARENA - d["pos"][1])
            wall = f" wall_dist={dist_wall:.1f}"
        diag = []
        if frac > 0.85:
            diag.append("LATE DEATH (catastrophic under avg-final-weight)")
        if d["my_blobs"] > 1:
            diag.append("died while split")
        if d["pos"]:
            if min(d["pos"][0], d["pos"][1], ARENA - d["pos"][0], ARENA - d["pos"][1]) < 5:
                diag.append("cornered near wall")
        if d["their_mass"] and d["my_mass"] and d["their_mass"] < d["my_mass"] * 2.5:
            diag.append("eaten by comparable blob (likely split-kill)")
        print(f"death {i+1}: round ~{d['round']} ({frac:.0%}) by P{d['eater']} "
              f"(their mass {d['their_mass']:.1f} vs mine {d['my_mass']:.1f}){wall}"
              f"  -> {'; '.join(diag) or 'outmassed'}")

    if not deaths and my_traj and my_traj[-1][1] < 5:
        print("diagnosis: never died but finished tiny -> STARVATION / displacement, not predation")


if __name__ == "__main__":
    main()
