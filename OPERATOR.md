# OPERATOR.md — how to run this operation
_Last updated 2026-07-16 ~15:50 AEST. Supersedes HANDOVER.md (2026-07-14) where they conflict.
Companion: **ASSISTANT.md** (how the assistant operates the evolver + assists Chris — keep BOTH current; standing order 2026-07-16)._
Mission: SYNCS Bot Battle 2026, team **Decay Rate** (teamId **35**). Competition ends **end of July 19 Sydney**; finals = top-8, ~10k games in an ALL-ELITE room, run after the freeze._

## 0. The one-page mental model
- We evolve bots in a local **gym** (steady-state ladder, 40 genomes + the live-ship anchor) across **worlds** — room shapes chosen to train specific skills. One world runs at a time; switching worlds = archive current + change `_draw_room()` + change `WORLD_TAG` (tag mismatch auto-flushes windows, genomes carry over).
- The endgame artifact is a **BUNDLE**: one uploadable bot with the **multi-mode architecture** — base genome + `MODE_OVERLAYS {0,1,2,3,7}` (gene diffs) + `ELITE_TEAM_IDS` + a time gate. `ELITE_TEAM_IDS` means **verified hard-room survivors**, not all leaderboard teams >20 (reporting E remains >20). In-game (v3 design, Chris 2026-07-16): **spawn in 1E**; drop to **0E only when the room is identified elite-free** (no sighting by tick `_MODE_0E_COMMIT`=150; a later sighting escalates back out); tally 2→**2E**, ≥3→**3E**, escalate-only; **after 2026-07-19T14:00:00Z (end of Jul 19 Sydney) mode 7E is hardcoded** (finals). Ship builds log to stdout→submission.log: one `[boot]` line (UTC now, 7E state + countdown) and `[mode] tick N` lines for every elite identification and switch. In the gym all overlays are empty ⇒ provably inert AND silent.
- **LOOKAHEAD** (`LOOKAHEAD_ON` + `LA_*` genes): engine-faithful split simulation vetoing fatal commits. Evidence: the **attack-lands veto** (`LA_ATTACK`) is worth ~+7 fitness and was the sole survival factor; virus veto always on; miss-veto redundant; horizon 2–4 suffices. Never seed candidates without `v1,a1`.
- **Ship discipline**: never quote a bot at its window peak (windows excursion ±8–10). Ship on deep-n (≥150, prefer 200+) with flat/rising per-chunk trajectory. Certified peaks regress (#452: 46.7→38; #121: 47.8→culled). The anchor is the only unselected reading; the pool floor vs anchor is the honest progress metric.

## 1. Standing laws (Chris's rules — violating these gets you yelled at)
1. **Nothing auto-launches; no cron on the laptop** without explicit permission. Manual `nohup` only.
2. **Local data first**: named local source → inventory completely; if data is missing, **report the gap and STOP** — never silently fetch remote. If Chris insists something exists, re-check immediately (files appear mid-conversation).
3. **Pause Studio sims during probes** (`ssh studio 'pkill -STOP -f bin/simulation'`), auto-resume ALWAYS armed before the probe (`-CONT`); ≤16 wasted matches accepted. Never leave sims frozen.
4. **Sydney time (AEST, UTC+10)** in everything you tell Chris. Server timestamps are UTC; the laptop clock is CST (UTC+8 → +2h to AEST).
5. **BEST_BOTS pool changes only on explicit order**, always journaled (pool = room difficulty).
6. **Journal** (`JOURNAL.md`): same-day dated entry for every significant discovery/action.
7. End every action-bearing reply with a compact **Summary** block.
8. Chris uploads to SYNCS himself — you stage in `~/Desktop/ship_staging/`, never upload.
9. Show tables when asked for data; state sample sizes; mark small samples ⚠; win% and mass columns from different samples must be flagged.

## 2. Daily operations
### Gym control (laptop)
- Start: `launchctl start com.decayrate.ladder` (manual-only LaunchAgent — no KeepAlive/RunAtLoad; logs → `logs/ladder_v3.log`, cwd botbattle, venv python).
- Stop: `pkill -f "[l]adder_v3.py"`. Restart shows "EVOLVER DOWN" ~20s on the portal — normal.
- Portal start (after reboot): `nohup evolution-2/.venv/bin/python3 portal/server.py >> logs/portal.log 2>&1 &`. Public tunnel (`cloudflared tunnel --url http://127.0.0.1:8973`) needs Chris's explicit OK — it exposes the portal to the internet.
- After ANY body/bounds change: `rm evolution_v3/variants/g*.py` before restart (forces re-materialization).
- Health: portal `/api` → match counter must advance; `ps aux | grep -c '[s]imulation'` ≈ 16 local; both nodes ok. **tput right after restart reads ~0.7 (cold) — check counter movement, not tput.**
- Breeding is hardened (`_fill` backfills genes missing from old genomes) — adding genes to bounds is safe now; still backfill state.json populations when adding genes (see 2026-07-15 KeyError incident).

### World switch (archive → new room)
1. `pkill` ladder. 2. Archive (pattern below). 3. Edit `_draw_room()` + `WORLD_TAG` in tools/ladder_v3.py. 4. `rm variants/g*.py`, restart. 5. Verify `WORLD_CHANGE_FLUSH` event in ladder_log + 0 tracebacks.
- Archive pattern (see any `archive/campaigns/*/RESUME.md`): ranked bots (rankNN_nGAMES_lineage .py+.genome.json), state_final.json, ladder_v3_<WORLD>.py copy, log gz, RESUME.md, then zip.
- Existing archives: `elite-archive-1` (7E mirror), `farm-laf-archive-1` (1E champions), `3e-archive-1` (3E band, ~1h trained), `v3campaign1_final_20260714_7elitepivot` (pre-lookahead farm).

### Injections (the main steering wheel)
- Contract: JSON `{"lineage": str, "genes": {~260 numeric genes}}` into `evolution_v3/inject_queue/` (1/cull) and `inject_queue/extra/` (1/cull) ⇒ 2 per cull. Consumed alphabetically; moved to `consumed/`.
- Build candidates FROM CURRENT WINNERS (state.json top) not stale archives; pin LA invariants **after** any jitter (`LOOKAHEAD_ON=1, LA_VIRUS=1, LA_ATTACK=1`, m coinflip, h∈2–4); clamp to bounds; validate (invariant assert + sample py_compile) BEFORE queueing.
- Mine each batch's results (survival/fitness by lineage tag) to design the next. Lineage tags encode the experiment — keep them parseable.

### Ship gate (single genome) — "ship X"
1. Extract genome from state/archive → overlay onto body (regex, `write_variant` pattern) → `bots/SHIP_*.py`.
2. `cmp` vs `evolution_v3/variants/g<id>.py` (byte-identical) OR archive copy.
3. Trajectory check (per-50/75 chunks: flat/rising required).
4. `py_compile` + witness match(es), require SUCCESS and **0 ban events** (run 3 witnesses for novel code paths).
5. Vault (.py + genome.json to `archive/vault/`, sha256 → `config/vault_log.txt`), journal, copy to `~/Desktop/ship_staging/`.

### Bundle build (multi-mode upload)
1. Pick per-mode champions (deep-n, flat trajectory) — **from CLOSE-of-world
   standings only, never pick-time leaders on a young world** (2026-07-16
   lesson: e3r10-j09 picked at 43.2 on a hours-old world, certified 37.9 at
   close, rank 28/40 — the peak-regression law applies to our own picks).
   A small gym edge (+2-3 mass) is UNDETECTABLE live at cell n<1500; do not
   expect overlays to visibly beat a strong generalist base. v3 (2026-07-16): base/1E=x1213x1147 (56.7@227), 0E=#1415 (80.2@300), 2E=e3r10-j09 (43.2@300, live TRAIN-2E), 3E=s2-nbr-w1211-m1h5-005 (3e-archive r02), 7E=lateguard (20.6@197).
2. `python3 tools/make_bundle.py <base(1E).json> <mode0.json|-> <mode2.json|-> <mode3.json|-> <mode7.json|-> <out.py>` — populates overlays (gene diffs vs base) + `ELITE_TEAM_IDS`. Refresh via `tools/meta_report.py`; for each avg>20 candidate take a current-first n=300 sample (current submission first, then backfill only the missing games from immediately prior submissions), and require hard n>=100, win>=18.75%, rank<=3.00 in rooms with 2+ OTHER candidates; exclude us=35. Current future-build tuple: `(5,15,1,9,73)`.
3. **Codegen**: `python3 tools/codegen.py <bundle.py> <out_CODEGEN.py>` — folds constants, keeps overlay-touched keys dynamic.
4. Gates: compile; witness PRE-cutover (expect `[mode]` ladder lines in submission0/io/**submission.log**); witness a POST-cutover copy (sed the cutover to the past → expect `switched to 7E` at boot); 0 bans everywhere.
5. Vault + sha + stage. Note in journal that bundles are compositions (not byte-identical to one gym variant; component genomes are).

### Verification tools (use them, they've caught everything)
- `tools/verify_moves.py <workspace> <bot.py>` — replays a recorded game through the real bot via the engine's own protocol; 0 mismatches = bit-exact. THE tool for proving body changes inert (reference workspace: old scratchpad `shipver171` — recreate by running a witness match with any deterministic bot if lost).
- `tools/equiv_test.py <bodyA> <bodyB>` — 2000-tick mock-pipeline comparison.
- `tools/codegen.py`, `tools/make_bundle.py`, `tools/make_dual_ship.py` (older 2-way gate; superseded by bundle).
- Witness matches: `simulation --headless --workspace <ws> "1:<bot>" ...7 more` (PATH needs `evolution-2/.venv/bin`; ladder self-fixes its own PATH).

## 3. Infrastructure
- **Nodes**: `config/gym_nodes.json` — studio `https://bot.chrisverse.uk` (token `~/.botapi_token`), wsl `http://desktop-34tntnv.tail35f7fb.ts.net:8975` (tailscale, since 2026-07-16; token `~/.botapi_wsl_token`) — update + restart ladder when a node URL changes. Header `X-Auth`; UA must not be python-urllib default.
- Rooms are drawn ON THE LAPTOP for local AND remote; bots travel by content sha (`ensure`). Node results are testimony; only local games are witnessed. Engine content sha must match local (`tools/verify_node.py`).
- **Studio worker is launchd-supervised** (`com.decayrate.botapi`, binds **127.0.0.1:8975**): restart with `launchctl kickstart -k gui/$(id -u)/com.decayrate.botapi` — NEVER pkill-and-relaunch manually (port race), NEVER touch caddy (:8000, Chris's production).
- **Studio access**: `ssh chrisli@100.102.72.37` (Tailscale). If it prints a login URL, STOP and give Chris the **latest** URL (each attempt mints a new one); don't retry-spam.
- **Hermes** (authenticated competition-data puller): headless Chrome CDP on Studio `localhost:9222` with a logged-in syncs.org.au page. Fetch via `Runtime.evaluate` + `fetch(credentials:'include')`. Meta store: Studio `/tmp/match_meta.jsonl` (+`/tmp/leaderboard_now.json`); extend with the meta_extend pattern (batch 25 ids until 24×404). Replays are **participant-gated** (404 unless we played); Hermes zips land in Studio `~/Developer/competition/`.
- **Portal**: `portal/server.py` :8973 (`http://100.99.9.34:8973` tailnet; trycloudflare tunnel URL rotates — see `logs/portal_tunnel.log`). Keep GRACE/WINDOW/CULL_EVERY in sync with the ladder. Has era-slice fix for archive/resume counter overlaps.

## 4. Analysis playbook (competitor intel)
- **THE canonical meta analysis is a checked-in tool — run it, don't improvise**:
  `python3 tools/meta_report.py --extend` (refreshes the Hermes cache, then prints
  room-composition windows, our per-submission conditional performance by opp-elite
  count, and the current elite band). `--since <id>` / `--windows <n>` to reshape.
  Its docstring carries the full data schema and gotchas; it pauses/resumes Studio
  sims itself. To compare an old vs new submission: run it, read the per-sub blocks,
  and judge ONLY same-composition cells (opp-E conditional rows), never headline
  averages across different mixes.
- Data lives on the STUDIO (not the laptop): `/tmp/match_meta.jsonl` (one match per
  line; `participants[].ranking` 0=win; `createdDate` UTC), `/tmp/leaderboard_now.json`
  (avgMass is per CURRENT submission), extended by `/tmp/meta_extend.py` via Hermes.
  Replays are participant-gated (404 unless we played) — metadata is the workhorse.
- Reporting tiers by CURRENT leaderboard avg: E>20 / C 10–20 / G<10 (Chris 2026-07-16). Bucket by exact counts; big samples; per-cell n; ⚠ small cells; win% from metadata (all games), masses only from replays (shared rooms only — conditioned on our presence). **Mode-switch elite is separate**: only current-sub hard-room survivors passing the gate printed by `meta_report.py`.
- Cross-validate any claim across ≥2 windows before believing it; a fixed bot's step-change is noise/curse until a verified MECHANISM (engine source, worker code) says otherwise. Do not build causal stories from timing coincidences (see Jul-13/14 retractions in JOURNAL).
- Field facts that matter (as of Jul 15): finals scoring = avg mass; >4-elite rooms ≈ never occur live; farm skill ⊥ fight skill; Washed = only rising-curve fighter; leaderboard leaders are mostly farm-inflated.

## 5. State snapshot (2026-07-16 15:50 AEST) + endgame checklist
- **Running**: `v3campaign-5:TRAIN-2E` world (60% 2E+2C+3F / 25% 1E+2C+4F / 15% 3E+1C+3F — mirrors the post-freeze live meta ~2E/2C/4G). Two injection waves queued (wave1 archive-derived, wave2 hypothesis-driven h1–h10); first wave-1 winner e3r10-j09 already leads the pool and is the bundle's 2E model.
- **Live meta (refreshed through match 31413, 2026-07-16 16:57 AEST)**: reporting E remains current avg>20. Latest sub 1810: 28% wins, mean rank 2.72@n264. Current-first n300 real mode elites: Bot Battle 5 (22%@243, rank 2.37), team 15 (21%@164, 2.84; current 5 + prior 295), Washed 1 (29%@242, 2.92), Banana 9 (31%@231, 2.37), Ninja 73 (22%@246, 2.46). Corrected future tuple `(5,15,1,9,73)`.
- **Staged for upload (observed concurrent rev3, not rebuilt by the current-first correction)**: `BUNDLE_v3_CODEGEN.py` sha `38c7f13d…`, elite ids `(5,1,9,37,73)`. It implements the superseded current-sub-only survivor set and therefore does **not** yet match the corrected future tuple. Live upload state was not verified.
- **To July 19 (freeze = 2026-07-19T14:00:00Z)**:
  1. Let TRAIN-2E mature; re-pick 2E (and possibly 1E/base) champions at deep-n; 3E upgrade possible by resuming `3e-archive-1`; 7E upgrade by resuming `elite-archive-1` with LA seeds.
  2. Rebuild bundle when better mode champions exist (make_bundle → codegen → gates → stage).
  3. **At freeze −1 day**: refresh reporting candidates from the leaderboard, run the current-sub hard-room survivor gate, then rebuild + restage with only passing `ELITE_TEAM_IDS`; Chris uploads. NO uploads on deadline day if avoidable (faulty upload = frozen out of finals).
  4. Verify cutover behavior once more with a post-cutover witness before the final upload.
  5. Mine live submission.log `[mode] tick N` lines to measure real elite-sighting latency; tune `_MODE_0E_COMMIT` (150) with data.
- **PLANNER program (2026-07-17)**: all planner variants failed selection; PC_ON contained; full failure analysis + proper-planner spec in PLANNER_REDESIGN.md (post-freeze work). Validated assets retained: hazard table, EV/VL books, replay pipeline, gate harnesses.
- **Known open items**: gym still on engine .13 (live is .14 — migration flagged 2026-07-15, needs node kit upgrades + WORLD_TAG bump); timeout-attack vector unexplored (someone froze most of the field Jul 15 — understand before finals); "procfs is not mounted! Aborting" seen in live submission.err (server-side runner fallout — reported context in JOURNAL); win-size metric on portal (offered, not built).

## 6. Incident lessons (paid for in blood, don't repeat)
- `docker ps` empty-with-no-header = CLI error, not "no containers" (killed production once).
- Bounds gene added ⇒ old genomes lack it ⇒ breeding KeyError (fixed by `_fill`, but backfill state too).
- ssh `tail -f` block-buffers → progress watchers must poll with fresh ssh execs; watchers need double-confirmed end anchors (ssh flakes false-fire `until` loops).
- Restarting the ladder from a shell without the engine venv on PATH used to kill local sims silently (self-fixed in ladder; symptom: remote-only throughput).
- The wedged external drive (`/Volumes/MacStudioExternal`) hangs ls/python listdir in D-state — probe with a 5s-kill wrapper, never bare.
- Timeout economics: 2s/move, 8s/match cumulative, banned matches never enter records, bans now score 0 mass. We run ~100× under budget; keep it that way (codegen = margin).

## Delta 2026-07-19 midday
- Shared body bots/omni_mixer_v3.py now CONTAINS PL4 (option-MPC organ), ledger _PLEDGER_HARD=6.5s,
  degrade PL4->PL3->reactive. Inert at PL4_ON=0 (equiv-gated).
- Gym world: v3campaign-8:TRAIN-FINAL-PL4 (finals mix 4E+1C+2farmers), population carried from
  TRAIN-PRE1E, windows flushed. Registry 193 genes (6 PL4 added).
- Ship staging: BUNDLE_v11_4471base_CODEGEN.py = base g4471 + elite list "everyone above spaghetti"
  (1,5,9,15,24,31,37,44,53,56,73,88) + budgets PC 5.5/PL3 1.0. v9/v10 remain as fallbacks.
