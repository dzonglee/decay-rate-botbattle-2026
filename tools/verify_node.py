#!/usr/bin/env python3
"""GYM-INTEGRITY VERIFIER for remote match-API nodes — FACT-BASED (Chris 2026-07-13:
"querying facts not outcomes"). No statistical tests, negligible compute.

Checks, all deterministic:
  1. ENGINE VERSION  — /integrity engine_version == required (2026.1.13)
  2. ENGINE CONTENT  — /integrity engine_sha == sha256 of OUR local engine's
                       .py sources. Same bytes = same game. Version strings
                       can lie; content hashes cannot.
  3. BOT CACHE       — upload the two fodder bots, then /bots?verify=1: the
                       node re-hashes every cached body server-side; all
                       entries must verify (content-addressed cache intact).
  4. JOB FIDELITY    — queue ONE match; /jobs/<id> must echo exactly the 8
                       shas we requested (the node runs what we ask, no
                       substitution), and the result must report the standard
                       match length (rounds == 1400) with 8 masses.

Usage:  verify_node.py <api_url> [token_file]
"""
import glob
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_REQUIRED = "2026.1.13"
ROUNDS_REQUIRED = 1400
LOCAL_VENV = Path("/Users/chrisli/Developer/competition/evolution-2/.venv")
BOTS = [ROOT / "bots" / "simple_bot.py", ROOT / "bots" / "naive_splitter.py"]


def local_engine_fingerprint():
    h = hashlib.sha256()
    roots = sorted(glob.glob(str(LOCAL_VENV / "lib" / "python*" / "site-packages")))
    files = []
    for r in roots:
        files += glob.glob(r + "/agario*/**/*.py", recursive=True)
        files += glob.glob(r + "/agario*.py")
    for f in sorted(set(files)):
        rel = f.split("site-packages/")[-1]
        h.update(rel.encode())
        h.update(Path(f).read_bytes())
    return {"files": len(set(files)), "sha": h.hexdigest()}


def api(base, tok, method, path, data=None, timeout=30):
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"X-Auth": tok, "User-Agent": "decayrate-verify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    base = sys.argv[1].rstrip("/")
    tokfile = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / ".botapi_token")
    tok = Path(tokfile).read_text().strip()
    fails = []

    # [1]+[2] engine facts
    integ = api(base, tok, "GET", "/integrity")
    local = local_engine_fingerprint()
    ok_v = integ.get("engine_version") == ENGINE_REQUIRED
    ok_h = integ.get("engine_sha") == local["sha"]
    print(f"[1] engine version : {integ.get('engine_version')}   ", "OK" if ok_v else "FAIL")
    print(f"[2] engine content : node {str(integ.get('engine_sha'))[:16]}… "
          f"({integ.get('engine_files')} files) vs local {local['sha'][:16]}… "
          f"({local['files']} files)   ", "OK" if ok_h else "FAIL")
    if not ok_v: fails.append("engine version mismatch")
    if not ok_h: fails.append("engine CONTENT mismatch — not the same game")
    print(f"    node: python {integ.get('python')} on {integ.get('platform')}, "
          f"{integ.get('workers')} workers")

    # [3] bot cache integrity
    shas = []
    for b in BOTS:
        data = b.read_bytes()
        sha = hashlib.sha256(data).hexdigest()[:20]
        try:
            api(base, tok, "GET", f"/bots/{sha}")
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            api(base, tok, "POST", f"/bots/{sha}", data)
        shas.append(sha)
    bots = api(base, tok, "GET", "/bots?verify=1", timeout=60)
    bad = [s for s, ok in bots.get("bots", {}).items() if not ok]
    have = all(s in bots.get("bots", {}) for s in shas)
    print(f"[3] bot cache      : {len(bots.get('bots', {}))} cached, "
          f"{len(bad)} failed re-hash, fodder present: {have}   ",
          "OK" if (not bad and have) else "FAIL")
    if bad: fails.append(f"{len(bad)} cache entries fail content re-hash")
    if not have: fails.append("uploaded bots missing from cache")

    # [4] job fidelity (one match: echo + match length — facts, not outcomes)
    room = [shas[0], shas[1]] * 4
    jid = api(base, tok, "POST", "/jobs", json.dumps({"bots": room}).encode())["job_id"]
    print(f"[4] job fidelity   : queued {jid}, waiting…")
    deadline = time.time() + 420
    jr = {}
    while time.time() < deadline:
        time.sleep(8)
        try:
            jr = api(base, tok, "GET", f"/jobs/{jid}", timeout=15)
        except Exception:
            continue
        if jr.get("status") in ("done", "error"):
            break
    echo_ok = jr.get("bots") == room
    res = jr.get("result") or {}
    rounds_ok = res.get("rounds") == ROUNDS_REQUIRED
    shape_ok = jr.get("status") == "done" and len(res.get("masses", [])) == 8
    print(f"    status={jr.get('status')} echo={'OK' if echo_ok else 'FAIL'} "
          f"rounds={res.get('rounds')} ({'OK' if rounds_ok else 'FAIL'}) "
          f"masses={'OK' if shape_ok else 'FAIL'}")
    if not echo_ok: fails.append("node did not echo the requested bots")
    if not rounds_ok: fails.append(f"match length {res.get('rounds')} != {ROUNDS_REQUIRED}")
    if not shape_ok: fails.append("match did not complete with 8 masses")

    print()
    if fails:
        print("VERDICT: FAIL —", "; ".join(fails))
        return 1
    print("VERDICT: PASS — engine bytes identical, cache intact, jobs run as specified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
