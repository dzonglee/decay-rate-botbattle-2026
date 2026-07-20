#!/usr/bin/env python3
"""Build a time-gated dual-genome ship: QUALIFY params before cutover (UTC),
FINALS params after. Usage:
  make_dual_ship.py <qualify_genome.json> <finals_genome.json> <cutover_utc ISO> <out.py>
Fails safe: any clock error -> QUALIFY branch."""
import json, re, sys
from pathlib import Path
BODY = Path(__file__).resolve().parent.parent / "bots" / "omni_mixer_v3.py"

def overlay(src, genome):
    for k, v in genome.items():
        if k.startswith("_"): continue
        src = re.sub(rf'("{k}":\s*)-?[0-9.]+(?:[eE][+-]?[0-9]+)?', rf"\g<1>{v:.6g}", src, count=1)
    return src

def main(qpath, fpath, cutover, out):
    q = json.load(open(qpath)); f = json.load(open(fpath))
    src = BODY.read_text()
    m = re.search(r"CONFIG\s*=\s*\{.*?\n\}", src, re.S)
    config_block = m.group(0)
    q_block = overlay(config_block, q).replace("CONFIG =", "CONFIG_QUALIFY =", 1)
    f_block = overlay(config_block, f).replace("CONFIG =", "CONFIG_FINALS =", 1)
    gate = f'''{q_block}

{f_block}

# ---- time-gated selection (fails safe to QUALIFY) ----
_FINALS_CUTOVER_UTC = "{cutover}"
try:
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    _now = _dt.now(_tz.utc)
    _IS_FINALS = _now.strftime("%Y-%m-%dT%H:%M:%S") >= _FINALS_CUTOVER_UTC
    try:
        import sys as _sys
        _syd = _now.astimezone(_tz(_td(hours=10)))
        print(f"[dual-gate] utc={{_now.strftime('%Y-%m-%dT%H:%M:%S')}} "
              f"sydney={{_syd.strftime('%Y-%m-%dT%H:%M:%S')}}AEST "
              f"cutover={{_FINALS_CUTOVER_UTC}}Z branch={{'FINALS' if _IS_FINALS else 'QUALIFY'}}",
              file=_sys.stderr, flush=True)
    except Exception:
        pass
except Exception:
    _IS_FINALS = False
CONFIG = CONFIG_FINALS if _IS_FINALS else CONFIG_QUALIFY'''
    src = src.replace(config_block, gate, 1)
    Path(out).write_text(src)
    print(f"wrote {out}  (cutover {cutover}Z; qualify={Path(qpath).name}, finals={Path(fpath).name})")

if __name__ == "__main__":
    main(*sys.argv[1:5])
