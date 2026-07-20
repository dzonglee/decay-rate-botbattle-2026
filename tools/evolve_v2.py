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
BASE_BOT = ROOT / "bots" / "gen099_i19.py"   # v2 default: the live champion; override with --base
EVO_DIR = ROOT / "evolution_v2"   # isolated from v1 state — never clobber a running tree
VARIANTS = EVO_DIR / "variants"
STATE = EVO_DIR / "state.json"
BENCH = []   # rotating contested bench (set from --bench); module-level default keeps imports safe
GAMELOG = ""   # gym gamelog dir (set from --gamelog); empty = off (zero cost)
CYCLE_FREEZE: set = set()   # handicap-cycle: genes whose MUTATION is frozen this phase (crossover unaffected)
# CYCLE-2 GUARDRAIL (Chris's order 2026-07-10): freeze draws operate on ATOMIC UNITS —
# a coupled organ (gate + its economy/params) is frozen whole or not at all. The cycle-1
# crash (-15.12) came from freezing W_VIRUS_FEAST/FEAST_* while SPLIT_CYCLE_ON stayed
# mutable: 35 gens of cycling-without-economy, locked. Partial freezes of these groups
# are now impossible.
FREEZE_COUPLES = [
    {"SPLIT_CYCLE_ON", "CYCLE_MIN_MASS", "CYCLE_TARGET_BLOBS", "CYCLE_THREAT_CLEAR"},
    {"W_VIRUS_FEAST", "FEAST_MIN_MASS", "FEAST_SLOT_SAT", "VIRUS_FEAST_CLEAR", "VIRUS_FEAST_FALLOFF"},
    {"AGGRO_ON", "W_AGGRO", "AGGRO_DECAY"},
    {"STALL_KICK_ON", "STALL_TICKS", "STALL_DIST", "W_STALL_KICK"},
    {"CORNER_SKIP_ON", "CORNER_TUCK", "CORNER_MARGIN"},
    {"ENDGAME_START", "ENDGAME_FEAR_MULT"},
    {"W_WEALTH_FEAR", "WEALTH_START", "WEALTH_EXP"},
    {"W_CAMP", "CAMP_WINDOW_LO", "CAMP_WINDOW_HI", "CAMP_MAX_MASS"},
    {"W_GRUDGE", "GRUDGE_DECAY"},
    {"PROF_ON", "PROF_ELITE_T", "PROF_STUPID_T", "PROF_RADIUS", "PROF_PREY_STUPID",
     "PROF_PREY_ELITE_DISC", "PROF_THREAT_STUPID_DISC", "PROF_THREAT_ELITE_MULT", "PROF_FEAST_BOLD"},
]
OUTCOME_RE = re.compile(r"ranking=\[([\d, ]+)\].*final_masses=\{([^}]*)\}")

# genes we do NOT evolve:
# - booleans and engine-rule constants
# - SPLIT_REACH is physics (eject 1.6 / (1-0.82) ~ 8.9), not a preference
# - the virus-feast genes are DEAD on engine 2026.1.9 (consumption grants zero
#   mass by design, per changelog) — searching them wastes dimensions
# 2026.1.11: virus consumption grants +2.25 mass again -> feast genes LIVE.
FROZEN = {"SPLIT_ENABLED", "EAT_RATIO", "SPLIT_MIN_MASS", "VIRUS_DANGER_MASS_RATIO",
          "SPLIT_REACH", "SPLIT_RUN_ENABLED",
          # organs proven to work ONLY together (ablation: latch-only -6, veto-only 0,
          # both +1.8) -> keep both ON; evolution tunes their genes, not their existence
          "VETO_ENABLED", "LOCK_ENABLED", "LUNGE_DISC_PANIC",
          "EXPECTED_ROUNDS"}   # OMNI: fixed at 1400 (engine round budget), not evolved


def read_base_config() -> dict[str, float]:
    src = BASE_BOT.read_text()
    m = re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S)
    cfg = ast.literal_eval("{" + m.group(1) + "\n}")  # \n} tolerates a trailing inline comment on the last CONFIG line
    return {k: v for k, v in cfg.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in FROZEN}


def write_variant(genome: dict[str, float], path: Path) -> None:
    src = BASE_BOT.read_text()
    for key, val in genome.items():
        if key == "_FROZEN_SET":
            continue
        src = re.sub(
            rf'("{key}":\s*)-?[0-9.]+(?:[eE][+-]?[0-9]+)?',
            rf"\g<1>{val:.6g}",
            src,
        )
    path.write_text(src)


# Genes with physical validity bounds: evolution must not shave through physics.
# (Found the hard way: a genome drifted SAFETY_RATIO to 1.22 > EAT_RATIO 1.2,
#  making just-barely-lethal blobs invisible to every defence.)
BOUNDS = {
    "SAFETY_RATIO": (1.15, 2.0),   # .12 mass-space (m12b): soft threat-avoid; hard veto at EAT_RATIO 1.2
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
    # 2026.1.11: viruses grant +2.25 again; avoidance is a strategy, not law.
    "VIRUS_AVOID_DIST": (0.3, 8.0),
    "W_VIRUS_FOOD": (0.0, 30.0),
    "VIRUS_FEAST_CLEAR": (2.0, 30.0),
    # v2 (GYM_V2 era): the i19 gate-deletion (FEAST_SLOT_SAT ~0.4 -> posture
    # always on) is now CHAMPION DOCTRINE, so it stays reachable — but bounded
    # so drift stays interpretable. FEAST_MIN_MASS floor = engine consume gate.
    # feastgym-3: all feast genes LIVE and clamped; FEAST_MIN_MASS tightened
    # 2.7->4 floor / 60->45 ceiling, W_VIRUS_FEAST ceiling 30->40.
    "FEAST_MIN_MASS": (4.0, 45.0),
    "FEAST_SLOT_SAT": (0.3, 16.0),
    "W_VIRUS_FEAST": (0.0, 40.0),
    # feastgym-3: raise the W_THREAT floor to 1.0 — stop breeding gym-fear-deletion
    # (the live world punishes threat-blindness even where the mimics don't fully).
    # Ceiling 12 is generous headroom above both bases (i19 1.70 / feast 4.97).
    "W_THREAT": (1.0, 12.0),
    "PROF_OBS_DIST": (4.0, 12.0),
    "PROF_OBS_MIN": (3.0, 20.0),
    "W_NAIVE_HUNT": (0.0, 8.0),     # 0 reachable: population can veto honestly
    "NAIVE_COMP_MAX": (0.1, 0.6),
    "W_NAIVE_LOCK": (0.0, 60.0),    # 0 reachable
    "NAIVE_LOCK_TICKS": (20.0, 250.0),
    "NAIVE_LOCK_RANGE": (5.0, 25.0),
    # SPLIT-FEAST CYCLE ORGAN (split_feaster; the .12 virus economy from Team-15/
    # Washed-CS replays). SPLIT_CYCLE_ON is VETOABLE (<=0.5 disables) so selection
    # can tune the cycle OR switch it off if a lineage can't make it pay -> bounded
    # downside. Seeded 1.0/30/28 (the live-audition values); selection tunes around.
    "SPLIT_CYCLE_ON": (0.5, 1.0),     # OMNI floor: cycle stays ON — the decode says cycling is CORRECT (conditional on mass); don't let the soft room rediscover "don't cycle"
    "CYCLE_MIN_MASS": (40.0, 60.0),   # OMNI floor: accumulate to >=40 (viable 16-piece fragments, 40/16=2.5>2.0) BEFORE cycling — "accumulate then cycle"
    "CYCLE_THREAT_CLEAR": (2.0, 30.0),
    # --- OMNI organs (OMNI_ARCHITECTURE.md ranges) ---
    "CORNER_SKIP_ON": (0.0, 1.0), "CORNER_TUCK": (0.5, 4.0), "CORNER_MARGIN": (-1.0, 3.0),
    "THREAT_SIZE_GATE": (0.0, 3.0),
    "W_VIRUS_SHIELD": (0.0, 8.0), "SHIELD_MAX_MASS": (2.0, 20.0),
    "W_FRAG_HUNT": (0.0, 4.0), "FRAG_HUNT_MIN_BLOBS": (2.0, 16.0),
    "W_PIECE_GUARD": (0.0, 8.0), "PIECE_GUARD_TICKS": (2.0, 60.0),
    "W_MERGE_IDLE": (0.0, 5.0), "W_CENTER": (-3.0, 3.0),
    "FOOD_HUNGER_EXP": (0.0, 2.0),
    "STALL_KICK_ON": (0.0, 1.0), "STALL_TICKS": (10.0, 200.0), "STALL_DIST": (0.2, 5.0), "W_STALL_KICK": (0.0, 6.0),
    "ENDGAME_START": (0.3, 1.0), "ENDGAME_FEAR_MULT": (0.5, 4.0),
    "W_ENVELOPE_SCALE": (0.0, 3.0),
    "AGGRO_ON": (0.0, 1.0), "W_AGGRO": (0.0, 3.0), "AGGRO_DECAY": (0.9, 0.999),
    "CYCLE_TARGET_BLOBS": (4.0, 16.0),
    # 9 promoted magic numbers (±50% of default; CYCLE_TARGET_BLOBS listed above)
    "HUNTER_AVOID_MULT": (0.75, 2.25), "HUNTER_REPEL_MULT": (1.0, 3.0),
    "WALL_ESC_MARGIN_MULT": (0.6, 1.8), "WALL_ESC_NUDGE": (0.1, 0.3),
    "LUNGE_DISC_FRAC": (0.45, 1.35), "SPLIT_ALIGN_MIN": (0.35, 1.05),
    "DEATH_COST_SCALE": (12.5, 37.5), "VIRUS_FEAST_FALLOFF": (0.5, 1.5),
}


def mutate(genome: dict[str, float], sigma: float, mut_prob: float) -> dict[str, float]:
    child = dict(genome)
    frozen_set = set(child.get("_FROZEN_SET", []))
    for k in child:
        if k == "_FROZEN_SET" or k in frozen_set or k in CYCLE_FREEZE:
            continue
        if re.match(r"ARCH_N\d+_(OP|A|B|TARGET)$", k):
            continue  # structural genes handled once-per-child below (mixer protocol)
        if random.random() < mut_prob:
            scale = abs(child[k]) if child[k] != 0 else 1.0
            # ORGAN UN-TRAP FLOOR (Chris's doctrine 2026-07-10): zero-anchored organ genes
            # previously mutated with step ~ |value| -> extinct organs were unreachable
            # (explains 770 gens of organ darkness in B). Floor gives them a real step.
            if k in BOUNDS and BOUNDS[k][0] <= 0.0:
                scale = max(scale, 0.15)
            child[k] = child[k] + random.gauss(0, sigma * scale)
        if k in BOUNDS:
            lo, hi = BOUNDS[k]
            child[k] = min(max(child[k], lo), hi)   # bounded -> real range (allows negative: W_CENTER, CORNER_MARGIN)
        else:
            child[k] = max(0.0, child[k])            # legacy unbounded genes stay >= 0
    # MIXER PROTOCOL (ChatGPT 2026-07-11): at most ONE structural rewiring per child —
    # 35% chance: resample exactly one unfrozen OP/A/B/TARGET gene categorically.
    _struct = [k for k in child
               if re.match(r"ARCH_N\d+_(OP|A|B|TARGET)$", k)
               and k not in frozen_set and k not in CYCLE_FREEZE and k in BOUNDS]
    if _struct and random.random() < 0.35:
        k = random.choice(_struct)
        lo, hi = BOUNDS[k]
        cur = int(round(child[k]))
        choices = [c for c in range(int(lo), int(hi) + 1) if c != cur]
        if choices:
            child[k] = float(random.choice(choices))
    return child


# omni-B seed-scatter: the zeroable/switchable organs worth kicking ON so gen-0
# starts spread across basins instead of clustered at the incumbent's defaults.
SCATTER_ORGANS = ["THREAT_SIZE_GATE", "W_VIRUS_SHIELD", "W_FRAG_HUNT",
                  "W_PIECE_GUARD", "W_MERGE_IDLE", "W_CENTER", "FOOD_HUNGER_EXP",
                  "STALL_KICK_ON", "W_ENVELOPE_SCALE", "AGGRO_ON", "ENDGAME_FEAR_MULT"]

# OMNI-2.1 gene space (Chris's order 2026-07-10): merge new-organ bounds + scatter
import sys as _s; _s.path.insert(0, "tools")
try:
    from omni2_bounds_addendum import OMNI2_BOUNDS, OMNI2_SCATTER
    BOUNDS.update(OMNI2_BOUNDS)
    SCATTER_ORGANS = list(set(SCATTER_ORGANS) | set(OMNI2_SCATTER))
except ImportError:
    pass  # addendum absent -> classic gene space

# (default-OFF organs only: kicking one genuinely activates it, decorrelating from
#  omni-A's conservative default-off run. CORNER_SKIP_ON/SPLIT_CYCLE_ON are on in
#  both runs; CYCLE_TARGET_BLOBS already at max -> excluded, no decorrelation value.)


def scatter_seed(genome: dict, k_lo: int = 2, k_hi: int = 3) -> dict:
    """omni-B: kick k (2-3) random organs into their ACTIVE band. Decorrelated
    exploration — more garbage, and if any organ wins, more surprises."""
    g = dict(genome)
    pool = [o for o in SCATTER_ORGANS if o in g and o in BOUNDS]
    if not pool:
        return g
    k = random.randint(k_lo, min(k_hi, len(pool)))
    for o in random.sample(pool, k):
        lo, hi = BOUNDS[o]
        if lo < 0:   # signed organ (W_CENTER): random side, strong magnitude
            g[o] = random.choice([-1.0, 1.0]) * random.uniform(0.4 * hi, hi)
        else:        # switch/weight: upper (active) half of the range
            g[o] = random.uniform(lo + 0.5 * (hi - lo), hi)
    return g


def crossover(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    child = {k: (a[k] if random.random() < 0.5 else b[k]) for k in a if k != "_FROZEN_SET"}
    if "_FROZEN_SET" in a:
        child["_FROZEN_SET"] = list(a["_FROZEN_SET"])
        for k in a["_FROZEN_SET"]:
            if k in child and k in a:
                child[k] = a[k]   # frozen genes stay at the lineage's anchored values
    return child


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
    # feastgym-3: every PREY entry is a FIXED seat each match (was 2 rotating).
    # rotating-bench room (Chris order 2026-07-10): ONE bench seat per match if BENCH set.
    seats = 8 - len(archetypes) - len(PREY) - (1 if BENCH else 0)
    if seats < 1:
        sys.exit(f"lobby overfull: {len(archetypes)} archetypes + {len(PREY)} "
                 f"pressure seats leaves {seats} pop seats; trim one.")
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
        if BENCH:
            # deterministic balanced rotation: cycles by match index, phase-shifted by gen
            # so each candidate-evaluation-block sees a balanced draw across the bench.
            bench_bot = BENCH[(gen + mi) % len(BENCH)]
            specs += [f"1:{bench_bot}"]
            print(f"[bench] g{gen} m{mi}: {bench_bot}")
        # feastgym-3: seat EVERY pressure bot as a fixed seat each match (was 2
        # rotating prey). mimic_t1 + mimic_t44 ride here so selection prices
        # predator pressure every game, not just harvest; sluggish + hungry_shy
        # hold the prey floor. Deterministic ecology -> lower fitness variance.
        specs += [f"1:{p}" for p in PREY]
        ws = f"{EVO_DIR}/ws/g{gen}_m{mi}"
        proc = subprocess.run(["simulation", "--headless", "--workspace", ws, *specs],
                              capture_output=True, text=True, timeout=900)
        m = OUTCOME_RE.search(proc.stdout + proc.stderr)
        early = r400_masses(ws) if EARLY_WEIGHT > 0 else {}
        if GAMELOG:
            # NEW STRATEGY (Chris 2026-07-10): log every gym match like a real replay.
            # gzip level 3 (fast); sidecar meta bundled in-file; janitor enforces the 35GB cap.
            try:
                import gzip as _gz
                _ev = open(f"{ws}/output/game.json").read()
                _meta = json.dumps({"gen": gen, "match": mi, "seats": specs})
                with _gz.open(f"{GAMELOG}/g{gen:04d}_m{mi:03d}.json.gz", "wt", compresslevel=3) as _f:
                    _f.write('{"meta":' + _meta + ',"events":' + _ev + "}")
            except Exception:
                pass  # logging must never kill a match
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
    global EARLY_WEIGHT, EARLY_ROUND, PREY, HANDICAP_FRAC, HANDICAP_N, HANDICAP_LINEAGES, BASE_BOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=16)
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--games", type=int, default=20, help="matches per individual per generation")
    ap.add_argument("--parallel", type=int, default=16)
    ap.add_argument("--elite", type=int, default=4)
    ap.add_argument("--sigma", type=float, default=0.25)
    ap.add_argument("--mut-prob", type=float, default=0.4)
    ap.add_argument("--seed-scatter", type=int, default=0,
                    help="omni-B decorrelation: kick 2-3 random organs into active range per gen-0 individual (0=off)")
    ap.add_argument("--reference", default=str(BASE_BOT), help="opponent pool bot file")
    ap.add_argument("--base", default=str(BASE_BOT),
                    help="genome source: the bot whose CONFIG seeds the population (v2 default: live champion)")
    ap.add_argument("--handicap-frac", type=float, default=0.0,
                    help="fraction of population with frozen genes (mixed-handicap evolution)")
    ap.add_argument("--handicap-lineages", type=int, default=2,
                    help="number of distinct frozen-gene sets among the handicapped pool")
    ap.add_argument("--handicap-n", type=int, default=5,
                    help="how many genes each handicapped individual has frozen")
    ap.add_argument("--prey", default="bots/sluggish.py,bots/hungry_shy.py",
                    help="comma list of prey bots; 2 rotating seats per match (graded incompetence)")
    ap.add_argument("--bench", default="",
                    help="comma list of doctrine-diverse contested bots; ONE seat per match, "
                         "deterministic balanced rotation ((gen+match_idx) mod len), draw logged per match")
    ap.add_argument("--run-id", default="RUN",
                    help="run identity stamped on every generation dump, e.g. 'HANDICAP-A / Studio'")
    ap.add_argument("--bounds-override", default="",
                    help="JSON file {gene:[lo,hi]} merged into BOUNDS at launch (focused-search ranges)")
    ap.add_argument("--gamelog", default="",
                    help="dir to archive every match's full event log (gzip, with seat-map meta); empty=off")
    ap.add_argument("--freeze-cycle", default="",
                    help="'FZ,FR,N' e.g. '60,30,20': freeze mutation of N random genes for FZ gens, "
                         "then FR gens fully free, repeat. Freeze set deterministic per cycle (resume-stable).")
    ap.add_argument("--early-weight", type=float, default=0.0,
                    help="fitness bonus weight on mass at round 400 (opening-race pressure)")
    ap.add_argument("--early-round", type=int, default=400)
    ap.add_argument("--league", action="store_true",
                    help="8 different genomes per match (8x sample efficiency)")
    ap.add_argument("--archetypes", default="bots/champion_gen134.py,bots/mimic_t44.py",
                    help="comma-separated bot paths to seat in every league match (v2 default: GYM_V2 ecology — a competent generalist + the T59 virus-competitor)")
    ap.add_argument("--keep-workspaces", action="store_true",
                    help="preserve per-match logs (pipes stripped) for postmortem analysis")
    ap.add_argument("--reset", action="store_true", help="ignore saved state")
    ap.add_argument("--elite-carry", type=float, default=0.0,
                    help="elite fitness carryover: surviving elites blend prior fitness with new samples "
                         "(inverse-variance weighting); value = memory cap as a multiple of --games (0=off)")
    args = ap.parse_args()
    BASE_BOT = Path(args.base).resolve()
    if not BASE_BOT.exists():
        sys.exit(f"--base bot not found: {BASE_BOT}")
    EARLY_WEIGHT, EARLY_ROUND = args.early_weight, args.early_round
    PREY = [x for x in args.prey.split(",") if x]
    global BENCH
    BENCH = [x for x in args.bench.split(",") if x]
    if args.bounds_override:
        import json as _j
        _ov = {k: tuple(v) for k, v in _j.load(open(args.bounds_override)).items() if not k.startswith("_")}
        BOUNDS.update(_ov)
        print(f"[bounds-override] {len(_ov)} gene ranges from {args.bounds_override}", file=sys.stderr)
    global GAMELOG
    GAMELOG = args.gamelog
    if GAMELOG:
        Path(GAMELOG).mkdir(parents=True, exist_ok=True)
    HANDICAP_FRAC, HANDICAP_N = args.handicap_frac, args.handicap_n
    HANDICAP_LINEAGES = args.handicap_lineages

    EVO_DIR.mkdir(exist_ok=True)
    base = read_base_config()

    carry = None
    if STATE.exists() and not args.reset:
        saved = json.loads(STATE.read_text())
        pop, start_gen = saved["population"], saved["generation"] + 1
        c = saved.get("carry")
        carry = c if c and len(c) == len(pop) else [None] * len(pop)
        print(f"resuming from generation {start_gen}", file=sys.stderr)
    else:
        pop = [dict(base)] + [mutate(base, args.sigma, 1.0) for _ in range(args.pop - 1)]
        if args.seed_scatter > 0:
            # omni-B: individual 0 stays the clean incumbent anchor; every other
            # gen-0 individual gets 2-3 organs kicked ON -> spread across basins.
            pop = [pop[0]] + [scatter_seed(ind) for ind in pop[1:]]
            print(f"[seed-scatter] {len(pop)-1} individuals seeded with 2-3 active organs", file=sys.stderr)
        if HANDICAP_FRAC > 0:
            keys = [k for k in base if k != "_FROZEN_SET"]
            n_h = int(round(HANDICAP_FRAC * len(pop)))
            for idx in random.sample(range(len(pop)), n_h):
                fro = random.sample(keys, min(HANDICAP_N, len(keys)))
                pop[idx]["_FROZEN_SET"] = fro
                for k in fro:
                    pop[idx][k] = base[k]   # anchor frozen genes at base values
            print(f"handicap: {n_h}/{len(pop)} individuals with {HANDICAP_N} frozen genes each")
        start_gen = 0

    for gen in range(start_gen, start_gen + args.gens):
        if args.freeze_cycle:
            fz, fr, ng = (int(x) for x in args.freeze_cycle.split(","))
            cyc, pos = divmod(gen, fz + fr)
            global CYCLE_FREEZE
            if pos < fz:
                # atomic-unit draw (cycle-2 guardrail): couples freeze whole-or-not
                keys = sorted(BOUNDS.keys())
                coupled = set().union(*FREEZE_COUPLES)
                units = [sorted(c & set(keys)) for c in FREEZE_COUPLES if c & set(keys)]
                units += [[k] for k in keys if k not in coupled]
                rnd = random.Random(4242 + cyc)
                rnd.shuffle(units)
                new_set = set()
                for u in units:
                    if len(new_set) >= ng:
                        break
                    new_set.update(u)
                if new_set != CYCLE_FREEZE:
                    CYCLE_FREEZE = new_set
                    print(f"[freeze-cycle] cycle {cyc} FROZEN phase (gens {cyc*(fz+fr)}-{cyc*(fz+fr)+fz-1}), {ng} genes: {sorted(CYCLE_FREEZE)}")
            elif CYCLE_FREEZE:
                CYCLE_FREEZE = set()
                print(f"[freeze-cycle] cycle {cyc} FREE phase (gens {cyc*(fz+fr)+fz}-{(cyc+1)*(fz+fr)-1}): all genes mutable")
        if args.league:
            arch = [a for a in args.archetypes.split(",") if a]
            mean_rank, mean_mass = evaluate_league(pop, gen, args.games, args.parallel,
                                                   args.keep_workspaces, arch)
        else:
            mean_rank, mean_mass = evaluate(pop, gen, args.games, args.reference, args.parallel, args.keep_workspaces)
        # leaderboard metric is AVG FINAL WEIGHT -> fitness = mean mass, higher is better
        carry_w = [float(args.games)] * len(pop)
        if args.elite_carry > 0 and carry:
            cap = args.elite_carry * args.games
            for i, prev in enumerate(carry[: len(pop)]):
                if prev is None:
                    continue
                pf, pw = prev
                blended = (pf * pw + mean_mass[i] * args.games) / (pw + args.games)
                print(f"[carry] i{i:02d} raw={mean_mass[i]:.2f} prev={pf:.2f}(w={pw:.0f}) -> {blended:.2f}")
                mean_mass[i] = blended
                carry_w[i] = min(pw + args.games, cap)
        order = sorted(range(len(pop)), key=lambda i: -mean_mass[i])

        print(f"\n[{args.run_id} / gen {gen}]")
        print(f"=== generation {gen} ===")   # keep the legacy marker: tooling greps it
        for rank_pos, i in enumerate(order):
            tag = "H" if "_FROZEN_SET" in pop[i] else " "
            marker = "*" if rank_pos < args.elite else " "
            print(f"{marker}{tag} i{i:02d}  mean_mass={mean_mass[i]:7.2f}  mean_rank={mean_rank[i]:.3f}")

        if HANDICAP_FRAC > 0:
            # PROTECTED POOLS (Chris's design): free and handicapped breed
            # separately; both live in the same lobbies, neither can extinguish
            # the other. The milestone comparison is best-H vs best-free.
            h_idx = [i for i in range(len(pop)) if "_FROZEN_SET" in pop[i]]
            f_idx = [i for i in range(len(pop)) if "_FROZEN_SET" not in pop[i]]
            new_pop_parts = []
            for pool_idx in (f_idx, h_idx):
                if not pool_idx:
                    continue
                pool_order = sorted(pool_idx, key=lambda i: -mean_mass[i])
                n_el = max(1, round(args.elite * len(pool_idx) / len(pop)))
                pool_elites = [pop[i] for i in pool_order[:n_el]]
                kids = []
                while len(kids) < len(pool_idx) - n_el:
                    a, b = (random.sample(pool_elites, 2) if len(pool_elites) > 1
                            else (pool_elites[0], pool_elites[0]))
                    kids.append(mutate(crossover(a, b), args.sigma, args.mut_prob))
                new_pop_parts.append((pool_elites, kids))
            best_f = max(f_idx, key=lambda i: mean_mass[i]) if f_idx else None
            best_h = max(h_idx, key=lambda i: mean_mass[i]) if h_idx else None
            if best_f is not None and best_h is not None:
                print(f"pool bests: free i{best_f:02d}={mean_mass[best_f]:.2f}  "
                      f"handicapped i{best_h:02d}={mean_mass[best_h]:.2f}  "
                      f"gap={mean_mass[best_f]-mean_mass[best_h]:+.2f}")
            elites = [pop[i] for i in order[: args.elite]]
            best = max(pop, key=lambda g: mean_mass[pop.index(g)]) if pop else None
            best = pop[order[0]]
            print("best genome:", json.dumps(best, indent=None))
            children = []
            elite_all = []
            for pool_elites, kids in new_pop_parts:
                elite_all.extend(pool_elites)
                children.extend(kids)
            elites = elite_all
        else:
            elites = [pop[i] for i in order[: args.elite]]
            best = elites[0]
            print("best genome:", json.dumps(best, indent=None))

            # next generation: elites + mutated/crossed offspring
            children = []
            while len(children) < len(pop) - args.elite:
                a, b = random.sample(elites, 2) if len(elites) > 1 else (elites[0], elites[0])
                children.append(mutate(crossover(a, b), args.sigma, args.mut_prob))
        prev_pop = pop
        pop = elites + children

        if args.elite_carry > 0:
            fit_by_id = {id(prev_pop[i]): (mean_mass[i], carry_w[i]) for i in range(len(prev_pop))}
            carry = [fit_by_id.get(id(ind)) for ind in pop]
        STATE.write_text(json.dumps({"generation": gen, "population": pop, "best": best, "best_mass": mean_mass[order[0]], "best_rank": mean_rank[order[0]], "carry": carry}))

    print(f"\nbest genome saved in {STATE}; materialise it with write_variant or copy from variants/")


if __name__ == "__main__":
    main()
