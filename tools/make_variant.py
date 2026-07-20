"""Generate a CONFIG variant of a bot file for A/B tournament testing.

Usage:
    python tools/make_variant.py bots/my_bot.py -o bots/variants/threat70.py \
        W_THREAT=70 THREAT_IGNORE_DIST=8.5 SPLIT_ENABLED=True

Copies the source bot and regex-replaces the given CONFIG values. Fails loudly
if a key is not found exactly once, so typos can't silently test the baseline.
"""

import argparse
import re
import sys
from pathlib import Path


def apply_override(source: str, key: str, value: str) -> str:
    pattern = re.compile(rf'^(\s*"{re.escape(key)}":\s*)([^,]+)(,)', re.MULTILINE)
    matches = pattern.findall(source)
    if len(matches) != 1:
        sys.exit(f"error: key {key!r} matched {len(matches)} times in CONFIG (expected 1)")
    return pattern.sub(rf"\g<1>{value}\g<3>", source)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="bot file to copy (e.g. bots/my_bot.py)")
    ap.add_argument("-o", "--output", required=True, help="variant file to write")
    ap.add_argument("overrides", nargs="+", help="KEY=VALUE CONFIG overrides")
    args = ap.parse_args()

    text = Path(args.source).read_text(encoding="utf-8")
    for override in args.overrides:
        key, _, value = override.partition("=")
        if not value:
            sys.exit(f"error: override {override!r} is not KEY=VALUE")
        text = apply_override(text, key.strip(), value.strip())

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
