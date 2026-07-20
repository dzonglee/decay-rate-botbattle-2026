"""
Evolution strategy over my_bot.py's CONFIG.

The genome is the set of numeric CONFIG values. Each generation:
  1. Every individual is materialised as a real bot file (variants/genG_iN.py)
  2. Fitness = mean rank over --games matches of 4 copies of the individual
     vs 4 copies of the reference bot (lower rank = better)
  3. Top --elite survive; the rest are replaced by mutated copies of survivors
     (gaussian perturbation of each gene with prob --mut-prob, sigma --sigma
     relative to the gene's current magnitude)
State is checkpointed to evolution/state.json after every generation (resumable).

Usage (screening speed — patch the engine first):
    python3 tools/speed_patch.py set 0.01
    python3 tools/evolve.py --pop 20 --gens 15 --games 20 --parallel 20
    python3 tools/speed_patch.py restore

Then re-verify the best genome at real speed on the ladder before promoting.
"""

import argparse
import ast
import json
import random
import re
import shutil
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_BOT = ROOT / "bots" / "my_bot.py"
EVO_DIR = ROOT / "evolution"
VARIANTS = EVO_DIR / "variants"
STATE = EVO_DIR / "state.json"
OUTCOME_RE = re.compile(r"ranking=\[([\d, ]+)\].*final_masses=\{([^}]*)\}")

# genes we do NOT evolve:
# - booleans and engine-rule constants
# - SPLIT_REACH is physics (eject 1.6 / (1-0.82) ~ 8.9), not a preference
# - the virus-feast genes are DEAD on engine 2026.1.9 (consumption grants zero
#   mass by design, per changelog) — searching them wastes dimensions
FROZEN = {"SPLIT_ENABLED", "EAT_RATIO", "SPLIT_MIN_MASS", "VIRUS_DANGER_MASS_RATIO",
          "SPLIT_REACH", "W_VIRUS_FOOD", "BOOT_VIRUS_MULT", "BOOT_VIRUS_CLEAR",
          "BOOT_MASS", "SPLIT_RUN_ENABLED",
          # organs proven to work ONLY together (ablation: latch-only -6, veto-only 0,
          # both +1.8) -> keep both ON; evolution tunes their genes, not their existence
          "VETO_ENABLED", "LOCK_ENABLED", "LUNGE_DISC_PANIC"}


def read_base_config() -> dict[str, float]:
    src = BASE_BOT.read_text()
    m = re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S)
    cfg = ast.literal_eval("{" + m.group(1) + "}")
    return {k: v for k, v in cfg.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in FROZEN}


def write_variant(genome: dict[str, float], path: Path) -> None:
    src = BASE_BOT.read_text()
    for key, val in genome.items():
        src = re.sub(
            rf'("{key}":\s*)-?[0-9.]+',
            rf"\g<1>{val:.6g}",
            src,
        )
    path.write_text(src)


# Genes with physical validity bounds: evolution must not shave through physics.
# (Found the hard way: a genome drifted SAFETY_RATIO to 1.22 > EAT_RATIO 1.2,
#  making just-barely-lethal blobs invisible to every defence.)
BOUNDS = {
    "SAFETY_RATIO": (1.00, 1.18),   # must stay below the 1.2 eat ratio
    "LEAD_TICKS": (1.0, 12.0),
    "VETO_HORIZON": (2.0, 15.0),
    "VETO_SOFT_MASS": (0.81, 20.0),
    "LOCK_TICKS_MAX": (20.0, 300.0),
    "LOCK_ABANDON_T": (10.0, 200.0),
    "FRESH_MASS": (0.81, 8.0),
    "OPEN_ROUNDS": (100.0, 700.0),
    "OPEN_GREED": (1.0, 6.0),
    "OPEN_FEAR": (0.2, 1.5),
    "EDGE_HUNT_RATIO": (1.2, 2.0),
    "W_EDGE_HUNT": (1.0, 8.0),
}


def mutate(genome: dict[str, float], sigma: float, mut_prob: float) -> dict[str, float]:
    child = dict(genome)
    for k in child:
        if random.random() < mut_prob:
            scale = abs(child[k]) if child[k] != 0 else 1.0
            child[k] = max(0.0, child[k] + random.gauss(0, sigma * scale))
        if k in BOUNDS:
            lo, hi = BOUNDS[k]
            child[k] = min(max(child[k], lo), hi)
    return child


def crossover(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    return {k: (a[k] if random.random() < 0.5 else b[k]) for k in a}


def one_match(variant: Path, reference: str, ws: str, keep: bool = False) -> tuple[float, float] | None:
    """Return mean rank of the variant's 4 slots in one 4v4 match."""
    spec_v, spec_r = f"4:{variant}", f"4:{reference}"
    proc = subprocess.run(
        ["simulation", "--headless", "--workspace", ws, spec_v, spec_r],
        capture_output=True, text=True, timeout=900,
    )
    m = OUTCOME_RE.search(proc.stdout + proc.stderr)
    if not m:
        (EVO_DIR / "failures.log").open("a").write(
            f"--- ws={ws} rc={proc.returncode} ---\n{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}\n"
        )
        if not keep:
            shutil.rmtree(ws, ignore_errors=True)
        return None
    if keep:
        # keep logs for postmortem; strip pipes (useless plumbing) and record outcome
        for pipe in Path(ws).rglob("*.pipe"):
            pipe.unlink(missing_ok=True)
        (Path(ws) / "outcome.txt").write_text(m.group(0) + "\n")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    ranking = [int(x) for x in m.group(1).split(",")]
    masses = {}
    for part in m.group(2).split(","):
        k, v = part.split(":")
        masses[int(k.strip())] = float(v.strip())
    # slots 0-3 = variant, 4-7 = reference
    ranks = [place for place, slot in enumerate(ranking, start=1) if slot < 4]
    mass = statistics.mean([masses.get(s2, 0.0) for s2 in range(4)])
    return statistics.mean(ranks), mass


def evaluate_league(pop, gen, appearances, parallel, keep, archetypes):
    """League mode: each match seats 8 DIFFERENT genomes (or 6 + 2 archetype
    bots if provided). Every individual is graded in ~`appearances` matches by
    its own final mass -> 8 fitness readings per game instead of 1."""
    import random as _r
    VARIANTS.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, genome in enumerate(pop):
        pth = VARIANTS / f"gen{gen:03d}_i{i:02d}.py"
        write_variant(genome, pth)
        paths.append(str(pth))
    seats = 8 - len(archetypes) - (2 if PREY else 0)
    # build a schedule where each individual appears ~appearances times
    pool = list(range(len(pop))) * appearances
    _r.shuffle(pool)
    matches = []
    while len(pool) >= seats:
        seat_ids, seen = [], set()
        rest = []
        for i in pool:
            if len(seat_ids) < seats and i not in seen:
                seat_ids.append(i); seen.add(i)
            else:
                rest.append(i)
        if len(seat_ids) < seats:
            break
        pool = rest
        matches.append(seat_ids)
    masses = {i: [] for i in range(len(pop))}
    ranks = {i: [] for i in range(len(pop))}
    def r400_masses(ws):
        """slot -> total mass at first round >= EARLY_ROUND (from the engine's own log)."""
        try:
            import json as _j
            data = _j.load(open(f"{ws}/output/game.json"))
        except Exception:
            return {}
        rnd, out = 0, {}
        for e in data:
            et = e.get("event_type")
            if et == "move_player" and e.get("player_id") == 0:
                rnd += 1
                if rnd > EARLY_ROUND:
                    break
            elif et == "event_player_moved" and rnd >= EARLY_ROUND - 20:
                b = e.get("blobs") or []
                if b:
                    out[e["player_id"]] = sum(x["radius"] ** 2 for x in b)
        return out

    def run(mi, seat_ids):
        specs = [f"1:{paths[i]}" for i in seat_ids] + [f"1:{a}" for a in archetypes]
        if PREY:
            # rotate 2 prey seats through the graded-incompetence band so the
            # population meets every level and cannot overfit one flavor
            specs += [f"1:{PREY[(gen + mi) % len(PREY)]}",
                      f"1:{PREY[(gen + mi + 1) % len(PREY)]}"]
        ws = f"{EVO_DIR}/ws/g{gen}_m{mi}"
        proc = subprocess.run(["simulation", "--headless", "--workspace", ws, *specs],
                              capture_output=True, text=True, timeout=900)
        m = OUTCOME_RE.search(proc.stdout + proc.stderr)
        early = r400_masses(ws) if EARLY_WEIGHT > 0 else {}
        shutil.rmtree(ws, ignore_errors=True)
        if not m:
            return None
        ranking = [int(x) for x in m.group(1).split(",")]
        fm = {}
        for part in m.group(2).split(","):
            k, v = part.split(":"); fm[int(k.strip())] = float(v.strip())
        # fitness = final mass + EARLY_WEIGHT * mass at round EARLY_ROUND
        for slot in list(fm):
            fm[slot] = fm[slot] + EARLY_WEIGHT * early.get(slot, 0.0)
        return seat_ids, ranking, fm
    with ThreadPoolExecutor(max_workers=parallel) as pool_ex:
        futs = [pool_ex.submit(run, mi, sid) for mi, sid in enumerate(matches)]
        for f in futs:
            r = f.result()
            if r is None:
                continue
            seat_ids, ranking, fm = r
            for slot, ind in enumerate(seat_ids):
                masses[ind].append(fm.get(slot, 0.0))
                ranks[ind].append(ranking.index(slot) + 1 if slot in ranking else 8)
    mr = [statistics.mean(ranks[i]) if ranks[i] else 9.0 for i in range(len(pop))]
    mm = [statistics.mean(masses[i]) if masses[i] else 0.0 for i in range(len(pop))]
    return mr, mm


def evaluate(pop: list[dict], gen: int, games: int, reference: str, parallel: int, keep: bool = False) -> tuple[list[float], list[float]]:
    VARIANTS.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, genome in enumerate(pop):
        p = VARIANTS / f"gen{gen:03d}_i{i:02d}.py"
        write_variant(genome, p)
        paths.append(p)

    jobs = [(i, g) for i in range(len(pop)) for g in range(games)]
    ranks: dict[int, list[float]] = {i: [] for i in range(len(pop))}
    masses: dict[int, list[float]] = {i: [] for i in range(len(pop))}
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futs = {
            pool.submit(one_match, paths[i], reference, f"{EVO_DIR}/ws/g{gen}_i{i}_m{g}", keep): i
            for i, g in jobs
        }
        for fut, i in futs.items():
            r = fut.result()
            if r is not None:
                ranks[i].append(r[0])
                masses[i].append(r[1])
    mean_rank = [statistics.mean(ranks[i]) if ranks[i] else 9.0 for i in range(len(pop))]
    mean_mass = [statistics.mean(masses[i]) if masses[i] else 0.0 for i in range(len(pop))]
    return mean_rank, mean_mass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=16)
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--games", type=int, default=20, help="matches per individual per generation")
    ap.add_argument("--parallel", type=int, default=16)
    ap.add_argument("--elite", type=int, default=4)
    ap.add_argument("--sigma", type=float, default=0.25)
    ap.add_argument("--mut-prob", type=float, default=0.4)
    ap.add_argument("--reference", default=str(BASE_BOT), help="opponent pool bot file")
    ap.add_argument("--prey", default="",
                    help="comma list of prey bots; 2 rotating seats per match (graded incompetence)")
    ap.add_argument("--early-weight", type=float, default=0.0,
                    help="fitness bonus weight on mass at round 400 (opening-race pressure)")
    ap.add_argument("--early-round", type=int, default=400)
    ap.add_argument("--league", action="store_true",
                    help="8 different genomes per match (8x sample efficiency)")
    ap.add_argument("--archetypes", default="",
                    help="comma-separated bot paths to seat in every league match, e.g. bots/mimic_p4.py,bots/hungry_shy.py")
    ap.add_argument("--keep-workspaces", action="store_true",
                    help="preserve per-match logs (pipes stripped) for postmortem analysis")
    ap.add_argument("--reset", action="store_true", help="ignore saved state")
    args = ap.parse_args()
    global EARLY_WEIGHT, EARLY_ROUND, PREY
    EARLY_WEIGHT, EARLY_ROUND = args.early_weight, args.early_round
    PREY = [x for x in args.prey.split(",") if x]

    EVO_DIR.mkdir(exist_ok=True)
    base = read_base_config()

    if STATE.exists() and not args.reset:
        saved = json.loads(STATE.read_text())
        pop, start_gen = saved["population"], saved["generation"] + 1
        print(f"resuming from generation {start_gen}", file=sys.stderr)
    else:
        pop = [dict(base)] + [mutate(base, args.sigma, 1.0) for _ in range(args.pop - 1)]
        start_gen = 0

    for gen in range(start_gen, start_gen + args.gens):
        if args.league:
            arch = [a for a in args.archetypes.split(",") if a]
            mean_rank, mean_mass = evaluate_league(pop, gen, args.games, args.parallel,
                                                   args.keep_workspaces, arch)
        else:
            mean_rank, mean_mass = evaluate(pop, gen, args.games, args.reference, args.parallel, args.keep_workspaces)
        # leaderboard metric is AVG FINAL WEIGHT -> fitness = mean mass, higher is better
        order = sorted(range(len(pop)), key=lambda i: -mean_mass[i])
        elites = [pop[i] for i in order[: args.elite]]

        print(f"\n=== generation {gen} ===")
        for rank_pos, i in enumerate(order):
            marker = "*" if rank_pos < args.elite else " "
            print(f"{marker} i{i:02d}  mean_mass={mean_mass[i]:7.2f}  mean_rank={mean_rank[i]:.3f}")
        best = elites[0]
        print("best genome:", json.dumps(best, indent=None))

        # next generation: elites + mutated/crossed offspring
        children = []
        while len(children) < len(pop) - args.elite:
            a, b = random.sample(elites, 2) if len(elites) > 1 else (elites[0], elites[0])
            children.append(mutate(crossover(a, b), args.sigma, args.mut_prob))
        pop = elites + children

        STATE.write_text(json.dumps({"generation": gen, "population": pop, "best": best, "best_mass": mean_mass[order[0]], "best_rank": mean_rank[order[0]]}))

    print(f"\nbest genome saved in {STATE}; materialise it with write_variant or copy from variants/")


if __name__ == "__main__":
    main()
