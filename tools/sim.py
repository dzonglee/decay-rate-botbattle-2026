"""Windows-compatible entry point for agario-kit's `simulation` / `interactive`.

The published launcher does `from signal import SIGKILL`, which doesn't exist
on Windows. Shim it to SIGTERM (os.kill maps SIGTERM to TerminateProcess)
before importing, so the installed package stays unmodified.

Usage (same args as the official commands):
    python tools/sim.py --headless 4:bots/template_bot.py 4:bots/my_bot.py
    python tools/sim.py --interactive 7:bots/my_bot.py
"""

import signal
import sys

if not hasattr(signal, "SIGKILL"):
    signal.SIGKILL = signal.SIGTERM  # type: ignore[attr-defined]

from agario_visualiser.launch_local_match import interactive_main, simulation_main


def main() -> None:
    if "--interactive" in sys.argv:
        sys.argv.remove("--interactive")
        interactive_main()
    else:
        simulation_main()


if __name__ == "__main__":
    main()
