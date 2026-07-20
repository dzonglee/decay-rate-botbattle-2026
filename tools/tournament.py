"""
Tournament harness: run N headless matches and report mean rank / mass per bot.

Usage:
    python3 tools/tournament.py --games 20 4:bots/template_bot.py 4:bots/my_bot.py

Every idea (weight change, new tactic) should be judged by this script,
never by eyeballing a single game. Variance is high; use >= 20 games.
"""

import argparse
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

OUTCOME_RE = re.compile(r"ranking=\[([\d, ]+)\].*final_masses=\{([^}]*)\}")


def run_match(specs: list[str], workspace: str) -> tuple[list[int], dict[int, float]] | None:
    proc = subprocess.run(
        ["simulation", "--headless", "--workspace", workspace, *specs],
        capture_output=True, text=True, timeout=600,
    )
    m = OUTCOME_RE.search(proc.stdout + proc.stderr)
    if not m:
        print("  [warn] could not parse outcome; skipping game", file=sys.stderr)
        return None
    ranking = [int(x) for x in m.group(1).split(",")]
    masses = {}
    for part in m.group(2).split(","):
        k, v = part.split(":")
        masses[int(k.strip())] = float(v.strip())
    return ranking, masses


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--parallel", type=int, default=4, help="concurrent matches")
    ap.add_argument("specs", nargs="+", help="count:path specs, counts must sum to 8")
    args = ap.parse_args()

    # map slot index -> bot label
    labels: list[str] = []
    for spec in args.specs:
        count, path = spec.split(":", 1)
        labels.extend([path] * int(count))

    ranks: dict[str, list[int]] = {l: [] for l in set(labels)}
    masses: dict[str, list[float]] = {l: [] for l in set(labels)}

    done = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [
            pool.submit(run_match, args.specs, f".agario_tourney/ws{g}")
            for g in range(args.games)
        ]
        for fut in futures:
            result = fut.result()
            done += 1
            print(f"game {done}/{args.games} done", file=sys.stderr)
            if result is None:
                continue
            ranking, final_masses = result
            for place, slot in enumerate(ranking, start=1):
                ranks[labels[slot]].append(place)
                masses[labels[slot]].append(final_masses.get(slot, 0.0))

    print(f"\n{'bot':40s} {'mean rank':>10s} {'sd':>6s} {'mean mass':>10s} {'wins':>5s}")
    for label in list(ranks):
        if not ranks[label]:
            print(f"{label:40s}  NO PARSED GAMES (bad path? check the file exists)")
            del ranks[label]
    for label in sorted(ranks, key=lambda l: statistics.mean(ranks[l])):
        r = ranks[label]
        print(
            f"{label:40s} {statistics.mean(r):10.2f} "
            f"{(statistics.stdev(r) if len(r) > 1 else 0):6.2f} "
            f"{statistics.mean(masses[label]):10.2f} "
            f"{sum(1 for x in r if x == 1):5d}"
        )


if __name__ == "__main__":
    main()
