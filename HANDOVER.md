# HANDOVER — Decay Rate / SYNCS Bot Battle 2026
_Last updated: 2026-07-14 ~00:20 AEST. Competition ends July 19. You are taking over a live, running system._

## 0. Who / what / where
- **Team**: "Decay Rate", teamId **35** on the competition server. Chris (chrischengdzonglee@gmail.com) is the human; he does ALL uploads to the competition site himself.
- **Engine**: `agario-kit 2026.1.13` (installed in `/Users/chrisli/Developer/competition/evolution-2/.venv` — the `simulation` binary lives in its `bin/`).
- **Repo root**: `/Users/chrisli/Developer/competition/botbattle/` (NOT a git repo).
- **Journal**: `JOURNAL.md` here — Chris's standing order: every significant discovery gets a same-day dated entry. Read the last ~10 entries before doing anything; tonight's entries contain hard-won measurement lessons.

## 1. CHRIS'S STANDING LAWS (violating these gets you shouted at, deservedly)
1. **Nothing auto-launches.** No cron, no launchd auto-start, no watchdogs on the laptop without his explicit permission. Manual `nohup` processes only.
2. **Local data first.** If he names a local source (a zip, a folder), inventory it COMPLETELY before any claim. If it lacks what you need, SAY SO AND STOP — never silently fall back to network fetches. If he insists something exists that you didn't see, re-check immediately; he's usually right (files appear mid-conversation).
3. **No heavy compute on gym nodes while the evolver runs** (wastes matches via silent timeout-bans → thins samples; it can NOT bend recorded values — engine blocks per move, banned games never enter records).
4. **BEST_BOTS pool is FROZEN** without his explicit order. Any ordered change gets a journal line + note the timestamp (room difficulty changes with the pool).
5. **Never quote a bot at its window peak.** Rolling-window excursions span ±8–10 mass here. Before any ship claim: per-50-game lifetime trajectory (flat/rising = real; peaked-and-decaying = mirage). #452 peaked 46.7→settled 38; #121 peaked 47.8→culled at 37. #171 was shipped on a RISING trajectory — that's the standard now.
6. **End every action-bearing response with a compact `Summary` block.**
7. **Room composition reports**: classify opponents by LEADERBOARD avg (elite >22 / contested 10–22 / garbage <10), large samples, everyone not just us.
8. He swears when frustrated; the correct response is facts, receipts, and shorter answers — not apologies at length.

## 2. THE EVOLVER (the main thing you're babysitting)
- **Script**: `tools/ladder_v3.py`. **State**: `evolution_v3/state.json` (resume-safe). **Log**: `evolution_v3/ladder_log.jsonl` (one record per match, `src` field = local/studio/wsl). **Graveyard**: `evolution_v3/graveyard.jsonl`.
- **Run**: `cd ~/Developer/competition/botbattle && nohup /opt/homebrew/bin/python3.12 -u tools/ladder_v3.py > /tmp/ladder.log 2>&1 &`
- **Stop**: `pkill -f "[l]adder_v3.py"` — always restart promptly; Chris watches the portal pulse. A restart shows "EVOLVER DOWN" for ~20s; that's normal.
- The script **prepends the engine venv to PATH itself** (a restart from a bare shell once silently killed all local matches — fixed in code, don't remove that block).
- **Current constants** (2026-07-14): `POP=40`+anchor, `WINDOW=300`, `GRACE=75`, `CULL_MATURE=75`, `CULL_EVERY=850`, `CULL_N=5`, `BREED_MIN=150` (breeding AND certification bar), **scheduling = uniform RANDOM** (Chris killed least-played priority; do not reintroduce).
- **Anchor**: `_id=-1`, plays the byte-exact live ship file `CHAMPION_ANCHOR` (currently `bots/SHIP_v2_x401x366_452.py`). It is a real 41st candidate, cycles like everyone, cannot be culled. **Do not re-anchor without Chris's order** (he explicitly declined re-anchoring to #121).
- **Body**: `bots/omni_mixer_v3.py` — 255 genes; ARCH graph = 16 nodes; ops: 0=a,1=a+b,2=a−b,3=a×b,4=max,5=min,6=sigmoid(k·a+bias),7=(a>b)?1:−1; features 0–21 (13=late,14=feast_ready,16=true_rank,17=vuln_window,18=kill_pulse,19=threat_prox,20=dominance,21=opp_frag; node i may also read outputs 22..21+i); targets: 1–6 force channels, 7 ordinary-split vote, 8 cycle vote, dials 9=THREAT 10=FEAST 11=CYCLE_GATE 12=VULN_MARGIN 13=PREY (exp() multipliers; vuln/cycle: negative = looser/freer).
- **Breeding doctrine**: family-block crossover (whole organs from one parent; the ENTIRE graph incl. AUTHORITY from one parent), graph genes mutate harder (only source of graph novelty), 2 audacious + 3 conservative newborns/cull.
- **Injection contract**: JSON `{"lineage": str, "genes": {255 genes}}` dropped in `evolution_v3/inject_queue/` (1 consumed per cull, alphabetical) AND `inject_queue/extra/` (1 more per cull). Consumed files move to `consumed/`.
- **RUNNING CAMPAIGN**: `all16` — 100 injectables from `~/Desktop/SHIP171_ALL16_INJECTABLES_100/` (ship #171 + all 16 nodes activated, 10 doctrine families × 10 doses), deployed 50 in main + 50 in extra ⇒ **2 per cull for ~50 culls, finishing ~06:00 on 07-14**. Readout = which FAMILIES survive culls above the bred-children baseline, judged on mature windows only.

## 3. DISTRIBUTED GYM (web API you control)
- **Config**: `config/gym_nodes.json` — currently:
  - `studio` → `https://bot.chrisverse.uk`, token file `~/.botapi_token`
  - `wsl` → `https://liabilities-handhelds-examining-reprint.trycloudflare.com`, token file `~/.botapi_wsl_token` — **trycloudflare URLs are EPHEMERAL**: when the WSL node's tunnel rotates, the other agent will hand over a new URL; update this config and restart the ladder.
- **Auth**: header `X-Auth: <token file contents>`. **Set a custom User-Agent** (e.g. `decayrate-ladder/1.0`) — Cloudflare bot-fight 403s python-urllib's default.
- **Endpoints** (per node): `GET /health` (workers, queue, cursor, engine), `GET /integrity` (engine source sha — must equal local `c425da0baf259604…`), `GET /bots?verify=1` (cache re-hash), `POST /bots/{sha20}` (upload body), `POST /jobs/batch` `{jobs:[[sha×8],…]}` (≤100), `GET /results?since={cursor}`, `DELETE /jobs?all=1`, `DELETE /jobs?bots=sha,…` (cull-cancel).
- **Architecture facts**: rooms are drawn ON THE LAPTOP (`_draw_room()`, same code local + remote); every seat file travels by content-sha (`ensure()`); nodes have NO pools or room logic of their own — a job cannot run with different bytes than the laptop drew. Node results are TESTIMONY (masses only) — sha checks verify identity, not execution quality; the only fully witnessed games are local ones.
- **Verify a node**: `tools/verify_node.py` (engine version + content sha, cache re-hash, one job echo, rounds==1400). Facts, not outcomes — Chris's requirement.
- **Workers**: Studio runs `~/botbattle_worker/studio_api.py` (16 workers, nice-10). WSL node runs the same code (14 workers) — it belongs to ANOTHER agent; you talk to it only via the API.

## 4. MAC STUDIO (compute node + Hermes)
- **SSH**: `ssh chrisli@100.102.72.37` (Tailscale, keyless, just works). Quirks: zsh there chokes on `===` echo separators and `~/x*` globs that don't match; long jobs over ssh get killed — use `nohup … > /tmp/out 2>&1 &` then poll the file.
- **Hermes** = headless Chrome on the Studio, CDP on `localhost:9222`, holding an **authenticated syncs.org.au session**. Fetch pattern (see `/tmp/compo_zip.py` on the Studio): find the page target via `http://localhost:9222/json`, open its webSocketDebuggerUrl, `Runtime.evaluate` an async `fetch(url, {credentials:"include"})`. This is how you read authenticated competition endpoints.
- **Key Studio files**: `/tmp/match_meta.jsonl` (match metadata sweep, ids 16400→~19000+; EXTEND it via CDP batches rather than re-pulling), `/tmp/*.py` (a library of past forensics scripts), `~/Developer/competition/syncs_replays_all.zip` (3,683 full replays, ids 30–18729), `~/Developer/competition/replay_logs.zip` (10GB — OUR OWN v2 gym logs, NOT competition replays).
- **Docker on the Studio runs Chris's production services** (incl. a broken immich_server) — do not restart Docker or `brew services` anything without asking.

## 5. COMPETITION SERVER FACTS
- Base: `https://api.syncs.org.au`. **Public**: `/teams/leaderboard` (fields: teamName, avgMass, numMatches — avg is per CURRENT submission). **Authenticated** (via Hermes or Chris's browser): `/matches/{id}` (participants, rankings 0=win, outcome, banReason, bannedSubmissionId), `/submissions/self/history`.
- **Replays**: `/matches/{id}/files/public/visualiser_forwards_differential.json` — **participant-gated** (404 for games we're not in). Parse: `event_game_started`→player_id→team_id map (team_id = platform teamId; we are 35); mass = Σ radius² of last `event_player_moved` per player.
- **Ban mechanics** (from engine source): 2s per move (SIGALRM), 8s cumulative per match. Ban = that match only, nullified + sealed; no scheduler ban for one timeout. Ship risk: a FAULTY upload freezes the team (recoverable by re-upload); a worse-but-working upload replaces your banked average with truth in ~50 games.
- **State of the field** (07-14 00:00): team #1 (~51, regressing from 59.6 peak, garbage-room specialist: 74% wins in 0-elite rooms, 23% with an elite present); Washed 37 (elite-robust, flat 45% vs 1–2 elites); us #6 ~33.4 on sub 55 (#452). Rooms are fair (~1.0 elite / 1.2 contested / 4.8 garbage for everyone). Our measured gap: win SIZE (66 avg-win vs team's ~105 inferred).

## 6. SHIP PROTOCOL (non-negotiable gate; Chris says "ship this")
1. Extract genome from `state.json` → overlay onto body via regex (`tools/ladder_v3.py::write_variant` pattern) → `bots/SHIP_v3_<lineage>_<id>.py`.
2. `cmp` against `evolution_v3/variants/g<id>.py` — MUST be byte-identical (provenance = the gym tested these exact bytes).
3. `py_compile`, then ONE witness match under the real engine vs a census room — require `result_type: SUCCESS` and 0 ban events (a faulty upload freezes the team; this gate is why we've never frozen).
4. Vault: copy .py + genome JSON to `archive/vault/`, append sha256 to `config/vault_log.txt`, journal entry, copy to `~/Desktop/ship_staging/`, attach file to Chris. **He uploads; you never do.**
- Currently staged & not yet confirmed uploaded: `SHIP_v3_x83x102_171.py` (47.8@n=232, rising trajectory, sha `fc7742a8…`). Previously staged #40/#121 are SUPERSEDED.

## 7. PORTAL (mission control)
- `portal/server.py`, port **8973**, restart: `pkill -f "portal/server.py"; nohup /opt/homebrew/bin/python3.12 portal/server.py > /tmp/portal.log 2>&1 &`
- Reachable: `http://localhost:8973`, tailnet `http://100.99.9.34:8973`, tunnel `https://ears-explicitly-kijiji-taken.trycloudflare.com` (ephemeral; cloudflared runs as `cloudflared tunnel --url http://localhost:8973`, log at `logs/portal_tunnel.log` — if dead, relaunch the same way and give Chris the new URL).
- Serves thresholds via `/api` (grace/cert) so UI stays consistent with the ladder — keep portal constants in sync with ladder constants on every change (GRACE/WINDOW/CULL_EVERY at top of both files).

## 8. MEASUREMENT EPISTEMICS (tonight's expensive lessons — read twice)
- **Rolling windows lie**: a fixed bot's 300-window ranges ±8–10 around truth (autocorrelated room streaks). The recurring "~47 top score" is the excursion ceiling of an upper-30s-true bot, not a skill level. The v2 campaign's "flat 47 plateau" was different bots rotating through the peak slot.
- **The anchor is the only unselected reading** — but luck is symmetric: equal-skill would put it mid-table, so its current LAST place means the pool's true level genuinely passed it. The honest metric is **anchor vs cull-floor** (floor can't be cherry-picked).
- **Live is the only absolute meter** (26→33 across ships proves real progress the gym's flat top line couldn't show). But live comparisons across submissions are era-confounded too (the field stiffens daily).
- **Gym reads for #195 and #452 are indistinguishable** (38.6@73 vs 37.7@300); pool median passed both. Reverting was rejected on this basis.
- Never build causal stories from timing coincidences (I did, twice, wrongly — see the RETRACTION journal entry). Demand a verified mechanism (engine source, worker code) before claiming causation. Engine source lives in the venv: `…/evolution-2/.venv/lib/python3.12/site-packages/engine/`.
- Id-collision trap: genome ids are reused across campaigns/eras — always filter log queries by match number/time window.

## 9. WHAT'S RUNNING RIGHT NOW (2026-07-14 00:20)
- Evolver: match ~54,300, ~150 games/min (16 local sims + studio + wsl). Random scheduling, GRACE 75.
- all16 injection campaign: ~90 genomes still queued, 2/cull, ~6h remaining.
- Portal on :8973 + cloudflared tunnel + tailnet.
- Chris's monitors: the portal (phone), and he reads lineage tags — `all16-<family>-d<dose>` for the campaign, filter "HT" for the older hand-tuned probes (HT1/HT2 culled, HT3 mid-table, HT4 young).
- Memory dir (if you have access): `~/.claude/projects/-Users-chrisli-Developer-competition/memory/` — the laws above are also stored there.

## 10. OPEN THREADS
- **#171 upload**: staged, awaiting Chris. When he gives a sub number: do NOT re-anchor unless he orders it; he may order adding #171 to BEST_BOTS (pool change = journal it).
- **all16 readout** (~morning): family-level cull-survival vs bred baseline; mature windows only.
- **WSL node tunnel** rotates — update `config/gym_nodes.json` + restart ladder when the other agent reports a new URL.
- **team (rival)**: watch their leaderboard regression; their sub 1404 resumed from a scheduler freeze — freezes are recoverable, remember that if OUR upload ever freezes.
- Optional offered-but-not-ordered: `-ref` lineage cull-protection for reference injections; win-size metric on portal; node per-match move-time echo ("facts not outcomes" extension).
