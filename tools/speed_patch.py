"""
Speed-patch the installed agario-kit engine for fast local runs.

The engine sleeps TURN_DURATION_SECONDS (default 0.1) per tick, so games run
wall-clock (~2.3 min). For screening/evolution runs we patch the installed
package to a smaller value, and restore afterwards.

Usage:
    python3 tools/speed_patch.py set 0.01    # 10x faster games (~15-20s each)
    python3 tools/speed_patch.py restore     # back to 0.1
    python3 tools/speed_patch.py show

IMPORTANT: anything promoted from patched-speed runs must be re-verified at
real speed (0.1) — bot compute-per-tick margins shrink at high tick rates.
"""

import re
import sys
from pathlib import Path




def config_file() -> Path:
    # TURN_DURATION_SECONDS lives in lib/config/arena.py in the installed kit
    base = Path(list(__import__("lib").__path__)[0]) / "config"
    for py in base.glob("*.py"):
        if "TURN_DURATION_SECONDS" in py.read_text():
            return py
    raise FileNotFoundError("TURN_DURATION_SECONDS not found in lib/config/*.py")


def show() -> None:
    text = config_file().read_text()
    m = re.search(r"TURN_DURATION_SECONDS\s*=\s*([0-9.]+)", text)
    print(f"TURN_DURATION_SECONDS = {m.group(1) if m else '?'} ({config_file()})")


def set_duration(value: float) -> None:
    path = config_file()
    text = path.read_text()
    new = re.sub(
        r"TURN_DURATION_SECONDS\s*=\s*[0-9.]+",
        f"TURN_DURATION_SECONDS = {value}",
        text,
    )
    path.write_text(new)
    show()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "set":
        set_duration(float(sys.argv[2]))
    elif cmd == "restore":
        set_duration(0.1)
    else:
        show()
