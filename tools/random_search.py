"""Coordinated multi-knob search: generate variants that perturb 2-3 random
CONFIG weights at once (±20-50%). Single-axis hill climbing proved the
champion is a single-knob local optimum; diagonal moves along weight ridges
are the part of the landscape those tests cannot see.

Usage:
    python3 tools/random_search.py bots/my_bot.py -n 12 --seed 7
    # then screen the crop in a league or A/B the promising ones:
    python3 tools/league.py --games 150 --parallel 8 --anchor bots/my_bot.py \
        bots/variants/search/*.py bots/meta/*.py

Engine-rule constants and booleans are never perturbed.
"""

import argparse
import random
import re
from pathlib import Path

from make_variant import apply_override  # same directory

# facts of the engine or switches, not tunables
EXCLUDE = {
    "EAT_RATIO",
    "SPLIT_MIN_MASS",
    "VIRUS_DANGER_MASS_RATIO",
    "SPLIT_ENABLED",
}
INT_KEYS = {"LEAD_TICKS", "SPLIT_MAX_BLOBS", "ENDGAME_ROUNDS"}
# keep perturbed values physically sensible (eat threshold is 1.2 by radius)
MIN_BOUNDS = {"SAFETY_RATIO": 1.0, "SPLIT_SAFETY_RATIO": 1.21, "EAT_RATIO": 1.2}

CONFIG_RE = re.compile(r'^\s*"([A-Z_0-9]+)":\s*(-?[\d.]+),', re.MULTILINE)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="champion bot file")
    ap.add_argument("-n", "--count", type=int, default=10, help="variants to generate")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--outdir", default="bots/variants/search")
    ap.add_argument("--knobs", type=int, default=None,
                    help="knobs per variant (default: random 2 or 3)")
    args = ap.parse_args()

    text = Path(args.source).read_text(encoding="utf-8")
    tunables = {
        key: float(val) for key, val in CONFIG_RE.findall(text) if key not in EXCLUDE
    }
    if not tunables:
        raise SystemExit("no tunable CONFIG keys found")

    rng = random.Random(args.seed)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        k = args.knobs or rng.choice([2, 3])
        keys = rng.sample(sorted(tunables), k=min(k, len(tunables)))
        variant_text = text
        desc_parts = []
        for key in keys:
            factor = rng.uniform(0.6, 1.5)
            new = max(tunables[key] * factor, MIN_BOUNDS.get(key, 0.0))
            if key in INT_KEYS:
                new_repr = str(max(1, round(new)))
            else:
                new_repr = f"{new:.3g}"
            variant_text = apply_override(variant_text, key, new_repr)
            desc_parts.append(f"{key}={new_repr}")
        name = f"rs{args.seed}_{i:02d}.py"
        (outdir / name).write_text(variant_text, encoding="utf-8")
        print(f"{outdir / name}: {' '.join(desc_parts)}")


if __name__ == "__main__":
    main()
