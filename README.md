# Decay Rate — SYNCS Bot Battle 2026

Team **Decay Rate** (team id 35) — Cheng LI (SID 560186806).

Final submission: `submissions/BUNDLE_v20_4471base_escalationfix_CODEGEN.py`
(sha256 `7b7eeb1c6f6ba246f7775b4c12927c53f479c664a3c2831293868975a416beef`, see `submissions/.sha_log.txt` for the full provenance chain of every uploaded artifact).

## Architecture (the shipped bot)

One uploadable file, generated from `bots/omni_mixer_v3.py` by `tools/make_bundle.py` + `tools/codegen.py`:

- **Reactive core** — a CGP-style sensor-mixer (~300 evolved genes): threat/prey/food force fields, virus feast cycles, wall/corner handling, split gating with an engine-faithful lookahead veto (`LA_*`).
- **PL3 planner organ** — a budgeted rollout planner (candidates x adversarial scenarios over an engine-exact world model in `tools/sim_engine.py`) that safety-overrides the reactive heading when its search dominates. Wall-clock self-governed to survive the server's cumulative time cap.
- **Multi-mode bundle** — base genome + per-mode gene overlays (`MODE_OVERLAYS`), switched at runtime by counting sighted elite team ids: farming chassis for 0-3 elite rooms, a finals-world-evolved champion for 4+ elite rooms, and a dedicated finals model (7E) that engages only on genuine finals signals (team-id anomaly or the announced cutover time).

## Evolution infrastructure

- `tools/ladder_v3.py` — steady-state ladder gym: 40 persistent genomes, curated opponent rooms ("worlds") matched to the live meta, windowed fitness (last-300 masses), cull/breed cycles, hand-seeded injection queue.
- `tools/make_bundle.py`, `tools/codegen.py` — bundle assembly and constant-folding for upload.
- `tools/sim_engine.py` — bit-exact reimplementation of the engine transition (differentially verified 7200/7200 states vs engine v2026.1.13-.16), used by planners and offline graders.
- `tools/shadow_grade.py` + replay miners — counterfactual grading of planner candidates on real server replays.
- `config/exposed_genes_ACTIVE.json` — the evolvable gene registry (bounds per gene).

## Docs

`ALGORITHM.md`, `TUNING.md`, `OPERATOR.md`, `PLANNER_REDESIGN.md`, `PREY_ECOLOGY.md`, and `CAMPAIGN_JOURNAL.md` record the day-by-day campaign, experiments, and post-mortems.
