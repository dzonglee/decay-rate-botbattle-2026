#!/usr/bin/env python3
"""OMNI_V3-style STEADY-STATE LADDER for the sensor-mixer CGP bots.
Faithful to the V3 replication spec (Chris, 2026-07-12):
  - 40 genomes, persistent population, NO generations.
  - Each match: candidate in seat 0; seats 1-7 = fixed curated world:
      2 random BEST_BOTS draws + champion anchor + contested veteran
      + 1 rotating bench + 2 fodder. Candidates NEVER face siblings.
  - Fitness = mean of last 200 seat-0 final masses (the leaderboard metric).
  - Scheduler: weighted random/round-robin; bots below GRACE receive 2x
    scheduling weight, then return to normal weight.
  - Every 500 matches: cull bottom 5 fully-measured, breed 5 crossover
    children of top 5 (alternating refinement/exploration).
  - Non-negotiables: never grade <60 games; flush all windows on any
    room/engine change (world_tag mismatch -> flush).
  - Checkpoint every 100 matches; resume-never-reset.
State: evolution_v3/state.json ; log: evolution_v3/ladder_log.jsonl
"""
import argparse, ast, collections, hashlib, json, os, random, re, statistics, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "evolution_v3"
# engine venv on PATH unconditionally — a restart from a shell without it
# silently killed ALL local matches (FileNotFoundError per match, 2026-07-13)
_VENVBIN = str(ROOT.parent / "evolution-2" / ".venv" / "bin")
if _VENVBIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _VENVBIN + ":" + os.environ.get("PATH", "")
STATE = V3 / "state.json"
LOG = V3 / "ladder_log.jsonl"
VARIANTS = V3 / "variants"
INJECT_DIR = V3 / "inject_queue"   # Chris 2026-07-13: 1 hand-seeded candidate consumed per cull
BODY = ROOT / "bots" / "omni_mixer_v3.py"       # ARCH v3 (2026-07-13): dials+16 nodes+defense sensors; equivalence-gated vs v2
REGISTRY = ROOT / "config" / "exposed_genes_ACTIVE.json"

# --- the curated world (spec mapping to our stable) ---
BEST_POOL_DIR = Path("/Users/chrisli/Desktop/BEST_BOTS")
CHAMPION_ANCHOR = ROOT / "bots" / "SHIP_v2_x401x366_452.py"  # anchor = #452 ship (sub 55), LIVE since 2026-07-13 evening; was #195
VETERAN = ROOT / "bots" / "split_feaster_v3.py"          # contested veteran
BENCH = [ROOT / "bots" / b for b in
         ("split_feaster.py", "gen51_feast.py", "elite_g30.py", "gen099_i19.py")]
FODDER = [ROOT / "bots" / "simple_bot.py", ROOT / "bots" / "naive_splitter.py"]
WORLD_TAG = "v3campaign-9:TRAIN-FINAL-ARCHIVE:engine2026.1.13"   # Chris 2026-07-19: reseeded from TRAINFINALv2 rank01-08; PL4 discarded (clamped [0,0]); lite+memo economics

POP = 40
WINDOW = 300   # Chris 2026-07-13: all fitness = last 300 plays
GRACE = 75   # Chris 2026-07-14: raised 60->75 (random scheduling, newborns mature slower)
GRACE_SCHED_WEIGHT = 3    # Chris 2026-07-14: grace bots play at 3x frequency (was 2x)
VETERAN_GAMES = 300       # Chris 2026-07-14: 300+-game veterans damped to 0.75x quota
VETERAN_DAMP = 0.75
CULL_MATURE = 75   # coupled to GRACE (cullable only after grace);
                   # windows NOT restarted on this change
CULL_EVERY = 850   # Chris 2026-07-13 (2nd bump): was 750, was 500
CULL_N = 5
BREED_MIN = 150   # Chris 2026-07-13: breeding eligibility n>=150 (= ship bar)
ELITE_POOL = 6   # breeding parents = top 6 of (graced pop + anchor) (Chris 2026-07-12; was 8)
CHECKPOINT_EVERY = 20

def now(): return time.strftime("%Y-%m-%d %H:%M:%S")

def scheduling_pool(population):
    """Integer-weighted draw cycle (quarter units so 0.75x stays exact):
    grace bots 3x (12/4), mature 1x (4/4), 300+-game veterans 0.75x (3/4)."""
    weighted = []
    for g in population:
        if g.get("_lineage", "").endswith("-pend"):
            continue
        games = g.get("_games", 0)
        if games < GRACE:
            w = 4 * GRACE_SCHED_WEIGHT          # 12 -> 3x
        elif games >= VETERAN_GAMES:
            w = int(4 * VETERAN_DAMP)           # 3  -> 0.75x
        else:
            w = 4                               # 4  -> 1x
        weighted.extend([g] * w)
    return weighted

def load_bounds():
    reg = json.load(open(REGISTRY))
    return {k: tuple(v) for k, v in reg.items() if not k.startswith("_")}

def read_base():
    src = BODY.read_text()
    m = re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S)
    cfg = ast.literal_eval("{" + m.group(1) + "\n}")
    return {k: v for k, v in cfg.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}

def read_anchor_cfg():
    # Read the live ship's CONFIG so its proven genes can be overlaid onto the
    # breeding gene space. ARCH v3 MIGRATION: the ship is a v2-numbered body —
    # node-output refs (A/B >= 19) shift +3 to the v3 numbering.
    src = CHAMPION_ANCHOR.read_text()
    m = re.search(r"CONFIG\s*=\s*\{(.*?)\n\}", src, re.S)
    cfg = ast.literal_eval("{" + m.group(1) + "\n}")
    out = {k: v for k, v in cfg.items()
           if isinstance(v, (int, float)) and not isinstance(v, bool)}
    for k in list(out):
        if re.match(r"ARCH_N\d+_(A|B)$", k) and out[k] >= 19:
            out[k] = out[k] + 3
    return out

def build_anchor_genome(base, anchor_cfg, window):
    # Full-space genome: body defaults overlaid with the champion's own gene values.
    # Mixer (ARCH_*) genes the champion lacks stay at body default so crossover is valid
    # in both directions. Fitness comes from its measured seat-3 masses (`window`).
    g = dict(base)
    for k, v in anchor_cfg.items():
        if k in g:
            g[k] = v
    w = window[-WINDOW:]
    g["_window"] = list(w); g["_games"] = len(w)
    g["_id"] = -1; g["_lineage"] = "ship452-anchor"; g["_anchor"] = True
    return g

def write_variant(genome, path):
    src = BODY.read_text()
    for k, v in genome.items():
        if k.startswith("_"): continue
        src = re.sub(rf'("{k}":\s*)-?[0-9.]+(?:[eE][+-]?[0-9]+)?',
                     rf"\g<1>{v:.6g}", src, count=1)
    path.write_text(src)

CATEGORICAL = re.compile(r"ARCH_N\d+_(OP|A|B|TARGET)$")

_IS_GRAPH_GENE = re.compile(r"ARCH_")

_BASE_DEFAULTS = read_base()   # body CONFIG defaults; backfill genes newer than a genome

def _fill(genome, bounds):
    """Ensure a genome has every evolvable gene (genes added after it was bred
    default to the body value). Prevents KeyError when bounds gains new genes."""
    for k in bounds:
        if k not in genome:
            genome[k] = _BASE_DEFAULTS.get(k, sum(bounds[k]) / 2.0)
    return genome

def mutate(genome, bounds, big):
    genome = _fill(dict(genome), bounds)
    # The GRAPH is inherited wholesale (crossover gives it ZERO diversity), so
    # mutation is its ONLY source of novelty — it therefore mutates HARDER than
    # the chassis (Chris 2026-07-13): higher perturbation rate + magnitude on
    # graph continuous genes, and every child gets 1-3 structural rewires (all
    # structural genes are graph genes). Chassis genes recombine via family-block
    # crossover, so they need less mutation churn.
    child = dict(genome)
    cats = [k for k in bounds if CATEGORICAL.match(k)]
    for k in bounds:
        if CATEGORICAL.match(k):
            continue
        graph = bool(_IS_GRAPH_GENE.match(k))
        if graph:
            prob = 0.85 if big else 0.55
            sigma = 0.50 if big else 0.22        # ~1.5-1.8x the chassis magnitude
        else:
            prob = 0.60 if big else 0.35
            sigma = 0.35 if big else 0.12
        if random.random() < prob:
            lo, hi = bounds[k]
            child[k] = max(lo, min(hi, child[k] + random.gauss(0, sigma * (hi - lo))))
    # structural rewires (op/input/target flips) — the graph's qualitative
    # innovation channel; at least 1 always, up to 3 when audacious.
    n_struct = 1 + (1 if random.random() < 0.55 else 0) + (1 if big and random.random() < 0.6 else 0)
    for _ in range(n_struct):
        if not cats:
            break
        k = random.choice(cats)
        lo, hi = bounds[k]
        cur = int(round(child[k]))
        opts = [c for c in range(int(lo), int(hi) + 1) if c != cur]
        if opts: child[k] = float(random.choice(opts))
    return child

# --- INHERITANCE DOCTRINE (Chris 2026-07-13): co-adapted genes travel together ---
# The GRAPH is one organism: all 16 nodes + their constitution inherit whole from
# ONE parent (nodes reference each other's outputs; splitting silently rewires
# references). CHASSIS ORGANS inherit as family blocks (a whole tuned organ from
# one parent — never father's WEALTH_FEAR with mother's WEALTH_START). Loose
# singletons coin-flip per gene.
GRAPH_PREFIXES = ("ARCH_N", "ARCH_AUTHORITY", "ARCH_MIN_AUTHORITY",
                  "ARCH_SPLIT_THRESHOLD", "ARCH_MAX_ACTIVE", "ARCH_BASE_")
GENE_FAMILIES = {
    "wealth":   ("W_WEALTH_FEAR", "WEALTH_START", "WEALTH_EXP"),
    "virus":    ("W_VIRUS_FEAST", "VIRUS_FEAST_CLEAR", "VIRUS_FEAST_FALLOFF",
                 "VIRUS_SLOT_EXP", "W_VIRUS_BIG", "W_VIRUS_SHIELD", "SHIELD_MAX_MASS",
                 "VIRUS_AVOID_DIST", "VIRUS_DANGER_MASS_RATIO", "HUNTER_AVOID_MULT",
                 "HUNTER_REPEL_MULT"),
    "cycle":    ("SPLIT_CYCLE_ON", "CYCLE_MIN_MASS", "CYCLE_TARGET_BLOBS",
                 "CYCLE_THREAT_CLEAR"),
    "corner":   ("CORNER_SKIP_ON", "CORNER_TUCK", "CORNER_MARGIN", "CORNER_VETO_TICKS",
                 "W_CORNER_REFUGE"),
    "camp":     ("W_CAMP", "CAMP_WINDOW_LO", "CAMP_WINDOW_HI", "CAMP_MAX_MASS"),
    "pl3":      ("PL3_ON", "PL3_DIAL", "PL3_RANGE", "PL3_H", "PL3_CANDS",
                 "PL3_CD", "PL3_MAXM"),
    "pl4":      ("PL4_ON", "PL4_DIAL", "PL4_CRIT_TTC", "PL4_H_CAP",
                 "PL4_COMMIT", "PL4_BUDGET_FRAC"),
    "vuln":     ("VULN_ON", "VULN_DETECT_RANGE", "VULN_COMMIT_MARGIN", "VULN_MIN_COOLDOWN",
                 "VULN_EAT_MARGIN", "VULN_THREAT_CLEAR", "VULN_APPROACH_WEIGHT",
                 "VULN_MIN_TARGET_MASS", "VULN_MAX_BANK_RISK", "VULN_LOCK_TICKS",
                 "VULN_MAX_BLOBS"),
    "rank":     ("W_RANK_GUARD", "W_RANK_AGGRO"),
    "grudge":   ("W_GRUDGE", "GRUDGE_DECAY"),
    "profiler": ("PROF_ON", "PROF_ELITE_T", "PROF_STUPID_T", "PROF_RADIUS",
                 "PROF_THREAT_STUPID_DISC", "PROF_THREAT_ELITE_MULT",
                 "PROF_PREY_STUPID", "PROF_PREY_ELITE_DISC", "PROF_FEAST_BOLD"),
    "lock":     ("LOCK_ENABLED", "W_LOCK", "LOCK_MIN_VALUE", "LOCK_ABANDON_T",
                 "LOCK_THREAT_BREAK", "LOCK_TICKS_MAX"),
    "veto":     ("VETO_ENABLED", "VETO_SOFT_MASS", "VETO_HORIZON"),
    "fraghunt": ("W_FRAG_HUNT", "FRAG_HUNT_MIN_BLOBS"),
}
_GENE2FAM = {g: fam for fam, gs in GENE_FAMILIES.items() for g in gs}

def _is_graph(k):
    return any(k.startswith(pfx) for pfx in GRAPH_PREFIXES)

def crossover(a, b, bounds):
    a = _fill(dict(a), bounds); b = _fill(dict(b), bounds)
    graph_parent = a if random.random() < 0.5 else b       # whole graph from one parent
    fam_parent = {fam: (a if random.random() < 0.5 else b)  # each organ from one parent
                  for fam in GENE_FAMILIES}
    child = {}
    for k in a:
        if k not in bounds:
            child[k] = a[k]                                 # non-evolvable: keep base A
        elif _is_graph(k):
            child[k] = graph_parent[k]
        elif k in _GENE2FAM:
            child[k] = fam_parent[_GENE2FAM[k]][k]
        else:
            child[k] = a[k] if random.random() < 0.5 else b[k]   # loose singleton
    return child

def fitness(g):
    w = g["_window"]
    return statistics.mean(w) if w else 0.0

CONTESTED = [ROOT / "bots" / b for b in
             ("split_feaster_v3.py", "split_feaster.py", "gen51_feast.py",
              "elite_g30.py", "gen099_i19.py")]
_CONTESTED_NAMES = {p.name for p in CONTESTED}
# BEST_BOTS is frozen by policy. Snapshot it once per run: repeated concurrent
# Desktop scans can block macOS File Provider and stall both local and remote
# dispatch. A restart is required for any explicitly ordered pool change.
BEST_POOL = tuple(p for p in BEST_POOL_DIR.glob("*.py")
                  if p.name not in _CONTESTED_NAMES)
if not BEST_POOL:
    raise RuntimeError(f"frozen BEST_BOTS pool is empty or unreadable: {BEST_POOL_DIR}")

def _draw_room():
    # CENSUS DESIGN (aligned to Chris's gym, 2026-07-12):
    #   seat 1 = 1 random draw from the Desktop best pool (contested-tier bots
    #            excluded from the elite draw - they live in seats 2-3)
    #   seats 2-3 = 2 random draws from the 5-bot contested tier
    #   seats 4-7 = 2x simple_bot + 2x naive_splitter
    # Anchor reference is PASSIVE: when the elite draw happens to be the live
    # ship, its seat mass is logged as "anchor".
    # Chris 2026-07-12 (census-4, Design B): mimic the CURRENT live era exactly
    # (1.00 elite / 1.18 contested / 4.82 fodder) with live-like elite variance:
    #   seats 1-2: each 50% elite / 50% contested  -> P(0 elite)=25%, P(1)=50%, P(2)=25%
    #   seat  3  : 18% contested / 82% fodder
    #   seats 4-7: fodder
    # FINALS-MIX ROOM v2 (Chris 2026-07-16): the finals won't be 7 true elites —
    # survivor-gate analysis says the top-8 is ~4-5 real killers + 2-3
    # farm-inflated bots (SUNMO 11%@245 hard, spaghetti 19%/3.16@240) with NO
    # fodder to farm. Train for that exact mix (2E world archived as
    # 2e-archive-1): 4 elite stand-ins + 1 contested + 2 farmer stand-ins
    # (farmer_1415 = our 0E split-feast champion; split_feaster_v3 = mass-
    # hungry contested farmer). Fixed shape per Chris's spec.
    # TRAIN-PRE1E (Chris 2026-07-18): live meta collapsed to soft rooms
    # (census 1.49E/1.61C/4.9G — most elites frozen, fodder returned). Train
    # the pre-final banking bot in a live-shaped 1E room:
    #   seat 1 = 1 true elite (BEST_POOL)
    #   seat 2 = contested; seat 3 = 50% contested / 50% fodder
    #   seats 4-7 = fodder  ->  E=1, C=1.5, G=4.5
    # TRAIN-FINAL-PL4 (Chris 2026-07-19): shipped the pre-final bundle; now
    # train the FINAL genome. Back to the finals mix (4E + 1C + 2 farmers,
    # no fodder) — same shape as TRAINFINALv2, population carried over.
    s1, s2, s3 = random.choice(BEST_POOL), random.choice(BEST_POOL), random.choice(BEST_POOL)
    rest = [random.choice(BEST_POOL), random.choice(CONTESTED),
            ROOT / "bots" / "farmer_1415.py", ROOT / "bots" / "split_feaster_v3.py"]
    world = [str(s1), str(s2), str(s3)] + [str(x) for x in rest]
    return s1, s2, s3, world

def _record(masses, cons, s1, s2, s3):
    fm = masses[0]
    rank = 1 + sum(1 for i in range(1, 8) if masses[i] > fm)
    anchor = None
    if s1.name == "SHIP_v2_x401x366_452.py": anchor = masses[1]
    elif s2.name == "SHIP_v2_x401x366_452.py": anchor = masses[2]
    occ = [s1.stem, s2.stem, s3.stem if hasattr(s3, "stem") else str(s3)]
    return {"mass": fm, "rank": rank, "cons": cons, "anchor": anchor,
            "elite": s1.stem, "emass": round(masses[1], 2),
            "cont": occ[1:],
            "cmass": [round(masses[2], 2), round(masses[3], 2)]}

def run_match(cand_path, mi):
    s1, s2, s3, world = _draw_room()
    specs = [f"1:{cand_path}"] + [f"1:{w}" for w in world[:7]]
    ws = V3 / "ws" / f"m{mi}"
    proc = subprocess.run(["simulation", "--headless", "--workspace", str(ws), *specs],
                          capture_output=True, text=True, timeout=900)
    try:
        res = json.load(open(ws / "output" / "results.json"))
        if res.get("result_type") != "SUCCESS":
            return None
        ev = json.load(open(ws / "output" / "game.json"))
    except Exception:
        return None
    masses = {i: 0.0 for i in range(8)}
    cons = 0
    for e in ev:
        if not isinstance(e, dict): continue
        t = e.get("event_type")
        if t == "event_player_moved":
            b = e.get("blobs") or []
            masses[e["player_id"]] = sum(x["radius"] ** 2 for x in b) if b else 0.0
        elif t == "event_virus_consumed" and e.get("player_id") == 0:
            cons += 1
    subprocess.run(["rm", "-rf", str(ws)], capture_output=True)
    return _record(masses, cons, s1, s2, s3)

# --- DISTRIBUTED GYM v2 (Chris's API design, 2026-07-13): fully async. ---
# The Studio runs a match API at https://bot.chrisverse.uk (queue + 4 workers).
# The laptop NEVER blocks on it: a pump thread keeps ~REMOTE_INFLIGHT jobs
# queued (uploading bodies once, by content-sha) and drops finished results
# into _remote_results; the main loop drains that queue between local waves.
# Local waves therefore run back-to-back at full CPU — no cross-machine
# barrier, no pulsing. Remote failures are dropped (candidate replays later).
import queue as _queue
import urllib.request, urllib.error

NODES_CFG = ROOT / "config" / "gym_nodes.json"
API_QUEUE_TARGET = int(os.environ.get("LADDER_QUEUE", "300"))   # total, split across nodes
API_STATS = V3 / "api_stats.json"
_remote_results = _queue.Queue()     # (cand_id, record)
_dispatch_q = _queue.Queue()         # (cand_id, variant_path) — shared, nodes drain it
_last_cancelled = None

class GymNode:
    def __init__(self, name, url, token):
        self.name = name; self.url = url.rstrip("/"); self.token = token
        self.shas = set()            # bodies known cached ON THIS node
        self.meta = {}               # job_id -> (cand_id, s1, s2, s3)
        self.cand_sha = {}           # cand_id -> body sha (for cull-cancel)
        self.cursor = None
        self.done_times = collections.deque(maxlen=200)
        self.lat = {"submit": collections.deque(maxlen=200),
                    "poll": collections.deque(maxlen=200),
                    "upload": collections.deque(maxlen=100)}
        self.workers = 0; self.rate = None; self.ok = False

    def api(self, method, path, data=None, timeout=30, cls=None):
        req = urllib.request.Request(self.url + path, data=data, method=method,
                                     headers={"X-Auth": self.token,
                                              "User-Agent": "decayrate-ladder/1.0"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        finally:
            if cls: self.lat[cls].append(time.time() - t0)

    def ensure(self, path):
        data = Path(path).read_bytes()
        sha = hashlib.sha256(data).hexdigest()[:20]
        if sha in self.shas:
            return sha
        try:
            self.api("GET", f"/bots/{sha}", cls="upload")
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            self.api("POST", f"/bots/{sha}", data, cls="upload")
        self.shas.add(sha)
        return sha

def _load_nodes():
    nodes = []
    try:
        cfg = json.loads(NODES_CFG.read_text())
    except Exception:
        cfg = [{"name": "studio", "url": "https://bot.chrisverse.uk",
                "token_file": "~/.botapi_token"}]
    for n in cfg:
        tf = Path(os.path.expanduser(n["token_file"]))
        if not tf.exists():
            continue
        nodes.append(GymNode(n["name"], n["url"], tf.read_text().strip()))
    return nodes

NODES = _load_nodes()

def _pct(d):
    v = sorted(d)
    if not v: return None
    return {"p50_ms": round(v[len(v)//2]*1000),
            "p95_ms": round(v[max(0,int(len(v)*0.95)-1)]*1000), "n": len(v)}

def _write_api_stats():
    per=[]
    tot_rate=0.0; tot_share=0
    for nd in NODES:
        per.append({"name": nd.name, "url": nd.url, "ok": nd.ok,
                    "workers": nd.workers, "inflight": len(nd.meta),
                    "rate": round(nd.rate,1) if nd.rate else None,
                    "latency": {k: _pct(v) for k,v in nd.lat.items()}})
        if nd.rate: tot_rate += nd.rate
    obj={"t": now(), "nodes": per, "queue_target": API_QUEUE_TARGET,
         "total_rate": round(tot_rate,1), "last_cull_cancelled": _last_cancelled}
    try: API_STATS.write_text(json.dumps(obj))
    except Exception: pass

def _node_pump(nd):
    per_target = max(60, API_QUEUE_TARGET // max(1, len(NODES)) + 40)
    while True:
        try:
            h = nd.api("GET", "/health", timeout=15, cls="poll")
            nd.ok = h.get("ok") is True; nd.workers = h.get("workers", 0)
            if nd.cursor is None:
                nd.cursor = h.get("cursor", 0)
                try:
                    nd.api("DELETE", "/jobs?all=1", cls="submit")
                except Exception:
                    pass
            need = per_target - (h.get("queued", 0) + h.get("running", 0))
            while need > 0:
                batch, bmeta = [], []
                for _ in range(min(50, need)):
                    try:
                        cid, vp = _dispatch_q.get_nowait()
                    except _queue.Empty:
                        break
                    s1, s2, s3, world = _draw_room()
                    shas = [nd.ensure(vp)] + [nd.ensure(w) for w in world[:7]]
                    nd.cand_sha[cid] = shas[0]
                    batch.append(shas); bmeta.append((cid, s1, s2, s3))
                if not batch: break
                r = nd.api("POST", "/jobs/batch",
                           json.dumps({"jobs": batch}).encode(), cls="submit")
                for jid, m in zip(r.get("job_ids", []), bmeta):
                    if jid: nd.meta[jid] = m
                need -= len(batch)
            r = nd.api("GET", f"/results?since={nd.cursor}", timeout=20, cls="poll")
            nd.cursor = r.get("cursor", nd.cursor)
            for item in r.get("results", []):
                m = nd.meta.pop(item["job_id"], None)
                if m is None or item.get("status") != "done":
                    continue
                cid, s1, s2, s3 = m
                res = item["result"]
                masses = {i: float(x) for i, x in enumerate(res["masses"])}
                rec = _record(masses, int(res.get("cons0", 0)), s1, s2, s3)
                rec["src"] = nd.name
                _remote_results.put((cid, rec))
                nd.done_times.append(time.time())
            if len(nd.done_times) >= 10:
                span = nd.done_times[-1] - nd.done_times[0]
                nd.rate = (len(nd.done_times)-1)/span*60 if span > 0 else None
            _write_api_stats()
            time.sleep(3)
        except Exception:
            nd.ok = False
            time.sleep(10)

def _cull_cancel(doomed_ids):
    """Cancel queued matches involving culled bots, on every node."""
    global _last_cancelled
    total = 0
    for nd in NODES:
        shas = sorted({nd.cand_sha[i] for i in doomed_ids if i in nd.cand_sha})
        if not shas: continue
        try:
            r = nd.api("DELETE", "/jobs?bots=" + ",".join(shas), cls="submit")
            total += r.get("cancelled", 0)
        except Exception:
            pass
    _last_cancelled = total
    if total:
        log({"t": now(), "event": "CULL_CANCEL", "cancelled": total})

def _api_ensure_all(path):
    """Push a newborn body to every node's cache immediately (post-cull)."""
    for nd in NODES:
        try: nd.ensure(path)
        except Exception: pass

def _remote_start():
    if API_QUEUE_TARGET <= 0 or not NODES:
        return []
    live = []
    for nd in NODES:
        try:
            if nd.api("GET", "/health", timeout=15).get("ok") is True:
                live.append(nd)
        except Exception:
            pass
    for nd in live:
        threading.Thread(target=_node_pump, args=(nd,), daemon=True).start()
    return live

def log(rec):
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parallel", type=int, default=16)   # Chris 2026-07-13: 16 per device
    args = ap.parse_args()
    V3.mkdir(exist_ok=True); VARIANTS.mkdir(parents=True, exist_ok=True); (V3 / "ws").mkdir(exist_ok=True)
    bounds = load_bounds()
    base = read_base()
    anchor_cfg = read_anchor_cfg()

    if STATE.exists():
        s = json.loads(STATE.read_text())
        if s.get("world_tag") != WORLD_TAG:
            for g in s["population"]:
                g["_window"] = []; g["_games"] = 0
            s["anchor_window"] = []
            s["world_tag"] = WORLD_TAG
            log({"t": now(), "event": "WORLD_CHANGE_FLUSH", "tag": WORLD_TAG})
        print(f"[ladder] resume at match {s['match_no']}", file=sys.stderr)
    else:
        # v3 CAMPAIGN SEEDING (Chris 2026-07-13): 40 fresh randoms on the ARCH v3
        # body — NO inheritance from prior campaigns (monoculture broke the
        # plateau ceiling; diversity is the point). 3 big scatter mutations each.
        pop = []
        for i in range(POP):
            g = dict(base)
            for _ in range(3):
                g = mutate(g, bounds, big=True)
            g["_id"] = i; g["_lineage"] = f"rnd{i}"; g["_window"] = []; g["_games"] = 0; g["_born"] = 0
            pop.append(g)
        s = {"population": pop, "match_no": 0, "next_id": POP, "world_tag": WORLD_TAG}
        log({"t": now(), "event": "LADDER_BORN", "pop": POP, "world": WORLD_TAG})
        STATE.write_text(json.dumps(s))

    from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait
    K = max(1, args.parallel)
    live_nodes = _remote_start()
    remote_on = bool(live_nodes)
    log({"t": now(), "event": "REMOTE_GYM", "mode": "api-async-multinode",
         "queue_target": API_QUEUE_TARGET if remote_on else 0,
         "nodes": [n.name for n in live_nodes], "local_parallel": K,
         "note": f"{len(live_nodes)} node(s) live" if remote_on else "no nodes"})

    def apply_result(cand, r, mi, aw):
        cand["_window"].append(r["mass"])
        if len(cand["_window"]) > WINDOW: cand["_window"] = cand["_window"][-WINDOW:]
        cand.setdefault("_ranks", []).append(r["rank"])
        cand["_ranks"] = cand["_ranks"][-WINDOW:]
        cand["_cons"] = cand.get("_cons", 0) + r["cons"]
        cand["_games"] += 1
        if r["anchor"] is not None:
            aw.append(r["anchor"])   # passive: only games where the ship was the elite draw
        rec = {"t": now(), "m": mi, "id": cand["_id"], "mass": round(r["mass"], 2),
               "rank": r["rank"], "cons": r["cons"], "elite": r["elite"],
               "emass": r["emass"], "cont": r["cont"], "cmass": r["cmass"],
               "fit": round(fitness(cand), 2), "n": len(cand["_window"])}
        if r.get("src"): rec["src"] = r["src"]
        if r["anchor"] is not None:
            rec["anchor"] = round(r["anchor"], 2)
        log(rec)

    # ROLLING LOCAL SCHEDULER: no waves, no barrier. A persistent K-slot pool;
    # the moment any match finishes, the next weighted-random candidate is
    # submitted. Grace bots have 2x weight; all mature bots remain uniform.
    # -pend placeholders never play (see injection design).
    ex = ThreadPoolExecutor(max_workers=K)
    futures = {}                       # future -> cand_id
    inflight_local = collections.Counter()

    def pick_next():
        # Weighted random, never least-played-first: below-GRACE candidates get
        # exactly two entries; every mature candidate gets one.
        return random.choice(scheduling_pool(s["population"]))

    def submit_one():
        cand = pick_next()
        if cand.get("_anchor"):
            vp = CHAMPION_ANCHOR                     # byte-exact live ship
        else:
            vp = VARIANTS / f"g{cand['_id']}.py"
            if not vp.exists() or s["match_no"] % 50 == 0:
                write_variant(cand, vp)
        fut = ex.submit(run_match, vp, s["match_no"] + len(futures))
        futures[fut] = cand["_id"]
        inflight_local[cand["_id"]] += 1

    for _ in range(K):
        submit_one()

    while True:
        pop = s["population"]
        mi = s["match_no"]
        by_id = {g["_id"]: g for g in pop}
        done, _ = wait(list(futures), timeout=10, return_when=FIRST_COMPLETED)
        aw = s.setdefault("anchor_window", [])
        played = 0
        for fut in done:
            cid = futures.pop(fut)
            inflight_local[cid] -= 1
            try:
                r = fut.result()
            except Exception:
                r = None
            cand = by_id.get(cid)
            if cand is not None and r is not None:
                apply_result(cand, r, mi, aw)
                played += 1
        # drain finished Studio games (async — never blocks)
        while True:
            try:
                cid, r = _remote_results.get_nowait()
            except _queue.Empty:
                break
            cand = by_id.get(cid)
            if cand is not None and r is not None:
                apply_result(cand, r, mi, aw)
                played += 1
        if len(aw) > WINDOW: s["anchor_window"] = aw[-WINDOW:]
        s["match_no"] = mi + played
        # Keep remote dispatch fed. This is a shuffled weighted round-robin:
        # grace candidates occur twice per cycle and mature candidates once.
        if remote_on and _dispatch_q.qsize() < 60:
            ordered = scheduling_pool(pop)
            random.shuffle(ordered)
            for cand in ordered[K:]:
                if cand.get("_anchor"):
                    vp = CHAMPION_ANCHOR
                else:
                    vp = VARIANTS / f"g{cand['_id']}.py"
                    if not vp.exists():
                        write_variant(cand, vp)
                _dispatch_q.put((cand["_id"], str(vp)))
        # refill local slots immediately (rolling)
        while len(futures) < K:
            submit_one()

        if s["match_no"] - s.get("last_cull", 0) >= CULL_EVERY:
            s["last_cull"] = s["match_no"]
            s["cull_no"] = s.get("cull_no", 0) + 1
            # BREEDING eligibility: n>=BREED_MIN (Chris 2026-07-13) — only genomes
            # proven over 150 games can become parents (same bar as shipping).
            # Cull gate: n>=CULL_MATURE so newborns get a full audition first.
            measured = [g for g in pop if g["_games"] >= BREED_MIN]
            cullable = [g for g in pop if g["_games"] >= CULL_MATURE
                        and not g.get("_anchor")]   # the live-ship candidate is never culled
            if len(cullable) > CULL_N * 2:
                ranked = sorted(cullable, key=fitness)
                doomed = {g["_id"] for g in ranked[:CULL_N]}   # cull bottom-5 of population only
                with open(V3 / "graveyard.jsonl", "a") as gy:
                    for g in ranked[:CULL_N]:
                        gy.write(json.dumps({"t": now(), "why": "culled", "fit": round(fitness(g), 2),
                                             "games": g["_games"], "genome": {k: v for k, v in g.items()
                                             if not k.startswith("_") or k in ("_id", "_lineage")}}) + "\n")
                # ELITE = top 6 of (graced population + anchor). The x0x1 anchor is a
                # real breeding candidate (Chris 2026-07-12): if its mean seat-3 mass
                # ranks it in the top 6 it enters the parent pool, immigrating champion
                # genes. It is never culled — only the population is. It qualifies only
                # once its own rolling window clears GRACE (it plays every match, so it
                # clears almost immediately).
                # elite = top-6 of measured; the anchor candidate is IN the
                # population now (real seat-0 window), no synthetic genome needed
                if len(measured) < 2:
                    # fresh campaign: nobody at 150 yet -> breed from best graced
                    measured = [g for g in pop if g["_games"] >= GRACE]
                elite = sorted(measured, key=fitness)[-ELITE_POOL:]
                newpop = [g for g in pop if g["_id"] not in doomed]
                # INJECTION (Chris 2026-07-13): consume 1 queued hand-seeded genome per
                # cull from inject_queue/, PLUS 1 from inject_queue/extra/ while it has
                # files (Chris's +1 corner-sticky candidates, next 3 culls). Each takes
                # one of the 5 newborn slots.
                n_breed = CULL_N
                inj_files = sorted(INJECT_DIR.glob("*.json"))[:1] if INJECT_DIR.exists() else []
                extra_dir = INJECT_DIR / "extra"
                if extra_dir.exists():
                    inj_files += sorted(extra_dir.glob("*.json"))[:1]
                for inj_file in inj_files:
                    try:
                        inj = json.loads(inj_file.read_text())
                        child = {k: v for k, v in inj["genes"].items() if not k.startswith("_")}
                        child["_id"] = s["next_id"]; s["next_id"] += 1
                        child["_lineage"] = inj.get("lineage", "inj")
                        child["_window"] = []; child["_games"] = 0; child["_born"] = s["match_no"]
                        child["_born_cull"] = s.get("cull_no", 0)
                        newpop.append(child)
                        n_breed -= 1
                        done = INJECT_DIR / "consumed"; done.mkdir(exist_ok=True)
                        inj_file.rename(done / inj_file.name)
                        log({"t": now(), "event": "INJECT", "m": s["match_no"],
                             "id": child["_id"], "lineage": child["_lineage"]})
                    except Exception as e:
                        log({"t": now(), "event": "INJECT_FAIL", "err": str(e)})
                # BREEDING: remaining newborn slots = random-walk crossovers from the
                # top-6 elite. Parents may include the anchor (labelled "anc").
                # BREEDING TEMPERAMENT (Chris 2026-07-13): of the bred newborns,
                # the first 2 are AUDACIOUS (big mutation — bold new values), the
                # rest CONSERVATIVE (small mutation — refine what works).
                def _lbl(g): return "anc" if g.get("_anchor") else g["_id"]
                for j in range(n_breed):
                    a, b = random.sample(elite, 2)
                    audacious = j < 2
                    child = mutate(crossover(a, b, bounds), bounds, big=audacious)
                    child = {k: v for k, v in child.items() if not k.startswith("_")}
                    child["_id"] = s["next_id"]; s["next_id"] += 1
                    tag = f"x{_lbl(a)}x{_lbl(b)}" + ("-bold" if audacious else "-fine")
                    child["_lineage"] = tag
                    child["_window"] = []; child["_games"] = 0; child["_born"] = s["match_no"]
                    child["_born_cull"] = s.get("cull_no", 0)
                    newpop.append(child)
                with open(V3 / "graveyard.jsonl", "a") as gy:
                    for g in newpop[-CULL_N:]:
                        gy.write(json.dumps({"t": now(), "why": "born", "lineage": g["_lineage"],
                                             "genome": {k: v for k, v in g.items()
                                             if not k.startswith("_") or k in ("_id", "_lineage")}}) + "\n")
                s["population"] = newpop
                log({"t": now(), "event": "CULL_BREED", "m": s["match_no"],
                     "culled": sorted(doomed), "elite": [g["_id"] for g in elite],
                     "temperament": "2bold+rest-fine"})
                if remote_on:
                    # Chris's v2 spec: cancel queued API matches involving the
                    # culled bots, and push the newborn bodies immediately.
                    _cull_cancel(doomed)
                    for g in newpop[-CULL_N:]:
                        vp = VARIANTS / f"g{g['_id']}.py"
                        try:
                            write_variant(g, vp)
                            _api_ensure_all(str(vp))
                        except Exception:
                            pass

        if s["match_no"] - s.get("last_ckpt", 0) >= CHECKPOINT_EVERY:
            s["last_ckpt"] = s["match_no"]
            STATE.write_text(json.dumps(s))

if __name__ == "__main__":
    main()
