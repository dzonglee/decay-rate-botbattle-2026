"""Population league: score bots by mean rank across a DIVERSE pool, not a
mirror. Each game fills 8 slots by sampling from the pool (optionally with the
champion anchored into every game). This is the closest local proxy to the
leaderboard objective and the antidote to mirror-overfitting.

Usage:
    python3 tools/league.py --games 200 --parallel 8 --anchor bots/my_bot.py \
        bots/variants/search/*.py bots/meta/*.py bots/template_bot.py

Reads the same engine plumbing as tournament.py (WSL-aware, hang-proof).
"""

import argparse
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from tournament import run_match  # same directory


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--parallel", type=int, default=6, help="concurrent matches")
    ap.add_argument("--tag", default="league", help="workspace prefix")
    ap.add_argument("--anchor", default=None,
                    help="bot included in every game (usually the champion)")
    ap.add_argument("--seed", type=int, default=1, help="lineup sampling seed")
    ap.add_argument("pool", nargs="+", help="bot files forming the population")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    pool = args.pool

    # pre-draw lineups so results are reproducible for a given seed.
    # Shuffle slot positions: the engine breaks eating/food ties by lower
    # player_id, so a fixed slot (e.g. anchor always first) is a measured
    # systematic advantage (~2.8 mean-rank between identical bots).
    lineups: list[list[str]] = []
    for _ in range(args.games):
        k = 7 if args.anchor else 8
        lineup = ([args.anchor] if args.anchor else []) + rng.choices(pool, k=k)
        rng.shuffle(lineup)
        lineups.append(lineup)

    ranks: dict[str, list[int]] = {}
    wins: dict[str, int] = {}

    def play(game_idx: int):
        lineup = lineups[game_idx]
        specs = [f"1:{path}" for path in lineup]
        return lineup, run_match(specs, f".agario_tourney/{args.tag}_ws{game_idx}")

    done = 0
    with ThreadPoolExecutor(max_workers=args.parallel) as pool_exec:
        futures = [pool_exec.submit(play, g) for g in range(args.games)]
        for fut in futures:
            lineup, result = fut.result()
            done += 1
            print(f"game {done}/{args.games} done", file=sys.stderr)
            if result is None:
                continue
            ranking, _masses = result
            for place, slot in enumerate(ranking, start=1):
                path = lineup[slot]
                ranks.setdefault(path, []).append(place)
                if place == 1:
                    wins[path] = wins.get(path, 0) + 1

    print(f"\n{'bot':45s} {'mean rank':>10s} {'sd':>6s} {'n':>5s} {'wins':>5s}")
    for path in sorted(ranks, key=lambda p: statistics.mean(ranks[p])):
        r = ranks[path]
        print(
            f"{path:45s} {statistics.mean(r):10.2f} "
            f"{(statistics.stdev(r) if len(r) > 1 else 0):6.2f} "
            f"{len(r):5d} {wins.get(path, 0):5d}"
        )


if __name__ == "__main__":
    main()
