#!/usr/bin/env python3
"""Build 100 all-node-live ARCH-v3 injection genomes from staged ship #171.

The output is deliberately structured, not a random parameter spray:
ten strategy families, ten controlled doses each.  N0-N2 remain the proven
#171 program.  N3-N15 are all enabled, routed, and given non-zero gains, while
ARCH_MAX_ACTIVE is raised to 16 so the evaluator actually executes every slot.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import random
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = Path("/Users/chrisli/Desktop/SHIP_STAGING/SHIP_v3_x83x102_171.py")
DEFAULT_STATE = ROOT / "evolution_v3" / "state.json"
DEFAULT_BOUNDS = ROOT / "config" / "exposed_genes_ACTIVE.json"
DEFAULT_OUTPUT = Path("/Users/chrisli/Desktop/SHIP171_ALL16_INJECTABLES_100")


@dataclass(frozen=True)
class Motif:
    op: int
    a: int
    b: int
    target: int
    gain: float
    k: float = 1.0
    bias: float = 0.0


# Feature ids:
# 0 const, 1 time, 2 mass, 3 wealth, 4 blob count, 5 threat,
# 6 prey opportunity, 7 virus visible, 8 edge, 9 fragmented, 10 rank lead,
# 11 incumbent magnitude, 12 threatened, 13 late, 14 feast ready,
# 15 safe prey, 16 global rank (0 best, 1 worst), 17 vulnerability window,
# 18 kill pulse, 19 threat proximity, 20 dominance, 21 opponent fragments.
# Targets: 1..6 mixer logits; 7/8 split votes; 9 threat; 10 feast;
# 11 cycle clearance; 12 vulnerable-prey margin; 13 prey force.
MOTIFS = {
    # Defensive capital preservation.
    "threat_near": Motif(0, 19, 0, 9, +0.28),
    "wealth_threat": Motif(3, 3, 19, 9, +0.40),
    "late_wealth": Motif(3, 13, 3, 9, +0.27),
    "danger_escape": Motif(4, 12, 19, 3, +0.30),
    "dominated_escape": Motif(3, 20, 19, 3, +0.32),
    "edge_escape": Motif(3, 8, 19, 5, +0.24),
    "lead_guard": Motif(3, 10, 19, 9, +0.30),
    "chaos_guard": Motif(3, 18, 19, 9, +0.34),
    "dominated_guard": Motif(0, 20, 0, 9, +0.24),
    "danger_prey_brake": Motif(3, 12, 6, 13, -0.28),
    "danger_feast_brake": Motif(3, 12, 14, 10, -0.32),
    "rich_virus_brake": Motif(3, 3, 14, 4, -0.28),
    "late_cycle_brake": Motif(3, 13, 9, 11, +0.24),
    "danger_cycle_brake": Motif(3, 12, 9, 11, +0.30),
    "danger_split_veto": Motif(0, 12, 0, 7, -0.42),
    "global_best_guard": Motif(10, 16, 0, 9, +0.24),
    "rich_incumbent": Motif(0, 3, 0, 6, +0.18),
    "late_incumbent": Motif(3, 13, 10, 6, +0.18),
    "edge_center": Motif(0, 8, 0, 5, +0.22),
    # Harvest and virus-cycle control.
    "safe_feast": Motif(10, 5, 0, 10, +0.30),
    "safe_virus": Motif(10, 5, 0, 4, +0.20),
    "safe_cycle": Motif(10, 5, 0, 11, -0.22),
    "safe_prey": Motif(0, 15, 0, 13, +0.24),
    "lead_feast": Motif(3, 10, 14, 10, +0.27),
    "lead_virus": Motif(3, 10, 14, 4, +0.18),
    "lead_cycle": Motif(3, 10, 14, 11, -0.20),
    "late_feast": Motif(3, 13, 14, 10, +0.23),
    "late_virus": Motif(3, 13, 14, 4, +0.16),
    "whole_cycle": Motif(10, 9, 0, 11, -0.20),
    "fragment_cycle": Motif(0, 9, 0, 11, +0.22),
    "safe_cycle_vote": Motif(10, 5, 0, 8, +0.22),
    "danger_cycle_vote": Motif(0, 12, 0, 8, -0.30),
    # Tactical prey conversion.
    "vuln_commit": Motif(3, 17, 15, 12, -0.30),
    "vuln_prey": Motif(3, 17, 15, 13, +0.32),
    "oppfrag_vuln": Motif(3, 21, 17, 12, -0.24),
    "frag_hunt": Motif(3, 21, 6, 13, +0.32),
    "frag_channel": Motif(3, 21, 6, 2, +0.24),
    "vuln_split": Motif(3, 17, 15, 7, +0.36),
    "prey_logit": Motif(0, 15, 0, 2, +0.22),
    "trailing_prey": Motif(0, 16, 0, 13, +0.26),
    "trailing_food": Motif(0, 16, 0, 1, +0.18),
    "global_worst_feast": Motif(0, 16, 0, 10, +0.20),
    "global_worst_cycle": Motif(0, 16, 0, 11, -0.18),
    "global_best_feast": Motif(10, 16, 0, 10, +0.18),
    # Fast response to a violent room.
    "kill_escape": Motif(0, 18, 0, 3, +0.28),
    "kill_prey_brake": Motif(3, 18, 6, 13, -0.24),
}


FAMILIES = {
    "balanced": [
        "safe_feast", "wealth_threat", "vuln_commit", "vuln_prey",
        "frag_hunt", "edge_center", "chaos_guard", "trailing_prey",
        "lead_feast", "late_cycle_brake", "danger_split_veto",
        "prey_logit", "rich_incumbent",
    ],
    "bank_guard": [
        "wealth_threat", "late_wealth", "danger_escape", "dominated_escape",
        "lead_guard", "chaos_guard", "danger_prey_brake",
        "danger_feast_brake", "rich_virus_brake", "danger_cycle_brake",
        "danger_split_veto", "global_best_guard", "rich_incumbent",
    ],
    "safe_vacuum": [
        "safe_feast", "safe_virus", "safe_cycle", "safe_prey",
        "lead_feast", "lead_virus", "lead_cycle", "late_feast",
        "late_virus", "whole_cycle", "prey_logit", "danger_feast_brake",
        "threat_near",
    ],
    "rank_posture": [
        "trailing_prey", "trailing_food", "global_worst_feast",
        "global_worst_cycle", "global_best_guard", "global_best_feast",
        "lead_guard", "lead_feast", "lead_cycle", "late_incumbent",
        "danger_prey_brake", "danger_split_veto", "threat_near",
    ],
    "consolidator": [
        "fragment_cycle", "late_cycle_brake", "danger_cycle_brake",
        "rich_virus_brake", "whole_cycle", "safe_cycle", "lead_cycle",
        "late_wealth", "wealth_threat", "rich_incumbent",
        "danger_split_veto", "safe_feast", "prey_logit",
    ],
    "vuln_closer": [
        "vuln_commit", "vuln_prey", "oppfrag_vuln", "frag_hunt",
        "frag_channel", "vuln_split", "safe_prey", "prey_logit",
        "trailing_prey", "danger_split_veto", "threat_near",
        "late_incumbent", "safe_feast",
    ],
    "anti_frag": [
        "frag_hunt", "frag_channel", "oppfrag_vuln", "vuln_prey",
        "vuln_commit", "safe_prey", "prey_logit", "trailing_prey",
        "danger_prey_brake", "danger_split_veto", "threat_near",
        "edge_center", "late_incumbent",
    ],
    "edge_survival": [
        "edge_center", "edge_escape", "dominated_escape", "threat_near",
        "wealth_threat", "lead_guard", "chaos_guard", "danger_escape",
        "danger_prey_brake", "danger_feast_brake", "danger_cycle_brake",
        "danger_split_veto", "rich_incumbent",
    ],
    "kill_tempo": [
        "kill_escape", "chaos_guard", "kill_prey_brake",
        "danger_cycle_vote", "danger_split_veto", "threat_near",
        "dominated_guard", "safe_prey", "safe_feast", "late_wealth",
        "late_cycle_brake", "edge_center", "rich_incumbent",
    ],
    "tempo_harvest": [
        "trailing_prey", "trailing_food", "global_worst_feast",
        "global_worst_cycle", "global_best_guard", "lead_feast",
        "late_feast", "late_cycle_brake", "late_incumbent",
        "safe_cycle_vote", "danger_cycle_vote", "prey_logit",
        "threat_near",
    ],
}


# The first files consumed by lexicographic queue order are middle-dose candidates
# from every family. Extremes arrive only after the coherent centre has auditioned.
FAMILY_ORDER = list(FAMILIES)
DOSE_ORDER = [3, 2, 4, 1, 5, 0, 6, 7, 8, 9]
DOSES = [0.58, 0.68, 0.78, 0.88, 0.98, 1.08, 1.18, 1.28, 1.38, 1.48]
AUTH_OFFSETS = [-0.08, -0.05, -0.025, 0.0, 0.025, 0.05, 0.075, 0.10, -0.10, 0.12]


def parse_config(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "CONFIG" for t in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict):
                raise TypeError("CONFIG is not a dictionary")
            return value
    raise ValueError(f"CONFIG not found in {path}")


def schema_from_state(path: Path, genome_id: int = 171) -> tuple[list[str], dict[str, object]]:
    state = json.loads(path.read_text())
    genome = next((g for g in state["population"] if g.get("_id") == genome_id), None)
    if genome is None:
        raise ValueError(f"genome #{genome_id} not present in {path}")
    keys = [k for k in genome if not k.startswith("_")]
    return keys, genome


def base_genes(config: dict[str, object], keys: list[str]) -> dict[str, float]:
    missing = [k for k in keys if k not in config]
    if missing:
        raise ValueError(f"attached bot lacks {len(missing)} genome keys: {missing[:8]}")
    genes: dict[str, float] = {}
    for key in keys:
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"non-numeric genome value {key}={value!r}")
        if not math.isfinite(float(value)):
            raise ValueError(f"non-finite genome value {key}={value!r}")
        genes[key] = float(value)
    return genes


def apply_motif(genes: dict[str, float], node: int, motif: Motif,
                dose: float, rng: random.Random, variant: int) -> None:
    # Controlled spread around each human hypothesis. Gains vary more than wiring;
    # K/bias vary only to leave useful material if a later mutation selects sigmoid.
    jitter = 1.0 + rng.uniform(-0.09, 0.09)
    gain = max(-1.5, min(1.5, motif.gain * dose * jitter))
    if abs(gain) < 0.04:
        gain = math.copysign(0.04, gain or motif.gain)
    op = motif.op
    k = motif.k
    bias = motif.bias
    # Two of the ten siblings threshold a simple sensor rather than using it
    # linearly. This changes response shape without changing strategic meaning.
    if variant in (7, 9) and op == 0 and motif.a not in (0,):
        op = 6
        k = 3.2 + 0.35 * (variant - 7)
        bias = -1.0 if variant == 7 else -1.35
    genes[f"ARCH_N{node}_ON"] = 1.0
    genes[f"ARCH_N{node}_OP"] = float(op)
    genes[f"ARCH_N{node}_A"] = float(motif.a)
    genes[f"ARCH_N{node}_B"] = float(motif.b)
    genes[f"ARCH_N{node}_K"] = float(k)
    genes[f"ARCH_N{node}_BIAS"] = float(bias)
    genes[f"ARCH_N{node}_TARGET"] = float(motif.target)
    genes[f"ARCH_N{node}_GAIN"] = round(gain, 9)


def build_candidate(base: dict[str, float], family: str, variant: int) -> dict[str, float]:
    genes = dict(base)
    rng = random.Random(171_016_100 + FAMILY_ORDER.index(family) * 100 + variant)
    genes["ARCH_MAX_ACTIVE"] = 16.0
    genes["ARCH_AUTHORITY"] = max(
        0.42, min(0.78, base["ARCH_AUTHORITY"] + AUTH_OFFSETS[variant])
    )
    genes["ARCH_SPLIT_THRESHOLD"] = max(
        0.48,
        min(0.90, base["ARCH_SPLIT_THRESHOLD"] + (variant - 4.5) * 0.018),
    )
    # Preserve the ship's three proven operations exactly, but make their gates
    # explicit. They were already >0.5, so this does not change their phenotype.
    for node in range(3):
        genes[f"ARCH_N{node}_ON"] = 1.0
    motifs = FAMILIES[family]
    if len(motifs) != 13:
        raise AssertionError(f"{family} has {len(motifs)} motifs, expected 13")
    for node, motif_name in zip(range(3, 16), motifs):
        apply_motif(genes, node, MOTIFS[motif_name], DOSES[variant], rng, variant)
    return genes


def validate_candidate(genes: dict[str, float], expected_keys: set[str],
                       bounds: dict[str, object]) -> None:
    if set(genes) != expected_keys:
        missing = sorted(expected_keys - set(genes))
        extra = sorted(set(genes) - expected_keys)
        raise ValueError(f"schema mismatch missing={missing} extra={extra}")
    if genes["ARCH_MAX_ACTIVE"] < 16:
        raise ValueError("ARCH_MAX_ACTIVE must execute all 16 nodes")
    for i in range(16):
        if genes[f"ARCH_N{i}_ON"] <= 0.5:
            raise ValueError(f"N{i} is off")
        op = round(genes[f"ARCH_N{i}_OP"])
        target = round(genes[f"ARCH_N{i}_TARGET"])
        a = round(genes[f"ARCH_N{i}_A"])
        b = round(genes[f"ARCH_N{i}_B"])
        gain = genes[f"ARCH_N{i}_GAIN"]
        if not 0 <= op <= 10:
            raise ValueError(f"N{i} bad op {op}")
        if not 1 <= target <= 13:
            raise ValueError(f"N{i} is unrouted (target={target})")
        if abs(gain) < 0.04:
            raise ValueError(f"N{i} effectively silent (gain={gain})")
        if not (0 <= a <= 21 + i and 0 <= b <= 21 + i):
            raise ValueError(f"N{i} violates DAG bounds A={a} B={b}")
    for key, limit in bounds.items():
        if key.startswith("_") or key not in genes:
            continue
        lo, hi = limit
        value = genes[key]
        if not lo - 1e-9 <= value <= hi + 1e-9:
            raise ValueError(f"{key}={value} outside [{lo}, {hi}]")


_NUM = r"-?[0-9.]+(?:[eE][+-]?[0-9]+)?"


def materialize(base_source: str, genes: dict[str, float]) -> str:
    source = base_source
    for key, value in genes.items():
        source, count = re.subn(
            rf'("{re.escape(key)}":\s*){_NUM}',
            rf"\g<1>{value:.9g}",
            source,
            count=1,
        )
        if count != 1:
            raise ValueError(f"could not materialize {key}")
    return source


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_readme(output: Path, base: Path, records: list[dict[str, object]]) -> None:
    family_text = "\n".join(
        f"- `{name}`: {', '.join(FAMILIES[name][:4])}, plus nine supporting nodes."
        for name in FAMILY_ORDER
    )
    top = "\n".join(f"  {r['file']}" for r in records[:10])
    text = f"""# SHIP #171 — 100 all-16-node injectable genomes

Base bot: `{base}`
Base sha256: `{sha256(base)}`

Every JSON file follows the ladder injection contract (`lineage` + full `genes`).
Every candidate:

- preserves #171's proven N0-N2 operations;
- sets all `ARCH_N0_ON` ... `ARCH_N15_ON` to `1.0`;
- sets `ARCH_MAX_ACTIVE=16`, so later slots execute instead of being clipped;
- routes every node to target 1..13 with `abs(gain) >= 0.04`;
- obeys the acyclic input bound `A,B <= 21 + node_index`;
- keeps the original 255-gene schema.

Files are ordered for direct queue consumption. The first ten are the central-dose
candidate from each family, so copying all JSON files into `evolution_v3/inject_queue/`
does not burn the first ten culls on one doctrine:

{top}

## Families

{family_text}

Each family has ten controlled siblings. The family wiring stays coherent while
gain dose, graph authority, split threshold, and (in two siblings) sensor response
shape vary. This is intentional breadth around plausible programs, not uniform
random mutation.

## Files

- `*.json` — the 100 injectables.
- `manifest.json` — family, dose, lineage, and sha256 for every candidate.
- `VALIDATION.txt` — validation and compilation results.

The pack is staged only; it has not been copied into the live queue.
"""
    (output / "README.md").write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--bounds", type=Path, default=DEFAULT_BOUNDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--python", type=Path, default=Path("python3"))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    if not args.base.is_file():
        raise SystemExit(f"base bot not found: {args.base}")
    if args.output.exists():
        if not args.replace:
            raise SystemExit(f"output exists (use --replace): {args.output}")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    config = parse_config(args.base)
    schema_keys, state_genome = schema_from_state(args.state)
    base = base_genes(config, schema_keys)
    # Prove that this really is the staged materialization of state genome #171.
    mismatches = [
        k for k in schema_keys
        if not math.isclose(base[k], float(state_genome[k]), rel_tol=2e-5, abs_tol=2e-6)
    ]
    if mismatches:
        raise ValueError(f"attached bot differs from state genome #171: {mismatches[:12]}")
    bounds = json.loads(args.bounds.read_text())
    expected = set(schema_keys)
    base_source = args.base.read_text()
    records: list[dict[str, object]] = []

    schedule = [(family, dose_i) for dose_i in DOSE_ORDER for family in FAMILY_ORDER]
    with tempfile.TemporaryDirectory(prefix="all16_compile_") as tmp:
        tmpdir = Path(tmp)
        for serial, (family, variant) in enumerate(schedule, start=1):
            genes = build_candidate(base, family, variant)
            validate_candidate(genes, expected, bounds)
            lineage = f"all16-{family}-d{variant}"
            name = f"{serial:03d}_{family}_d{variant}.json"
            path = args.output / name
            payload = {
                "lineage": lineage,
                "genes": {key: genes[key] for key in schema_keys},
            }
            path.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n")
            py_path = tmpdir / f"candidate_{serial:03d}.py"
            py_path.write_text(materialize(base_source, genes))
            records.append({
                "file": name,
                "lineage": lineage,
                "family": family,
                "variant": variant,
                "dose": DOSES[variant],
                "authority": genes["ARCH_AUTHORITY"],
                "split_threshold": genes["ARCH_SPLIT_THRESHOLD"],
                "sha256": sha256(path),
            })
        subprocess.run(
            [str(args.python), "-m", "py_compile", *map(str, sorted(tmpdir.glob("*.py")))],
            check=True,
        )

    (args.output / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    write_readme(args.output, args.base, records)
    validation = (
        "PASS\n"
        "100/100 JSON payloads parsed and matched the #171 255-gene schema.\n"
        "1600/1600 nodes enabled, routed to targets 1..13, and nonzero-gain.\n"
        "100/100 candidates set ARCH_MAX_ACTIVE=16.\n"
        "All node A/B inputs obeyed the acyclic per-node bound.\n"
        "All exposed genes remained inside exposed_genes_ACTIVE.json bounds.\n"
        f"100/100 materialized bot files compiled with {args.python}.\n"
    )
    (args.output / "VALIDATION.txt").write_text(validation)
    print(json.dumps({
        "output": str(args.output),
        "injectables": len(records),
        "families": FAMILY_ORDER,
        "base_sha256": sha256(args.base),
        "validation": "PASS",
    }, indent=2))


if __name__ == "__main__":
    main()
