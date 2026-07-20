"""OMNI-2 evolvable-gene BOUNDS addendum (deliverable 1 support).
Merge into evolve_v2.BOUNDS before evolving omni_feaster2.py, e.g.:

    import evolve_v2 as E
    from omni2_bounds_addendum import OMNI2_BOUNDS, OMNI2_SCATTER
    E.BOUNDS.update(OMNI2_BOUNDS)
    # optional: let --seed-scatter kick the new organs too
    E.SCATTER_ORGANS = list(set(getattr(E, "SCATTER_ORGANS", [])) | set(OMNI2_SCATTER))

All organs are neutral at 0.0 (or exp 0.0) — a zeroed genome plays exactly like
base omni_feaster. Bounds chosen wide enough to matter, narrow enough to stay sane.
"""
OMNI2_BOUNDS = {
    # W1 wealth preservation
    "W_WEALTH_FEAR": (0.0, 6.0),
    "WEALTH_START":  (15.0, 120.0),
    "WEALTH_EXP":    (0.3, 3.0),
    # W2 respawn camping (engine respawn ~30 rounds)
    "W_CAMP":        (0.0, 4.0),
    "CAMP_WINDOW_LO": (5.0, 28.0),
    "CAMP_WINDOW_HI": (30.0, 60.0),
    "CAMP_MAX_MASS": (10.0, 150.0),
    # W3 grudge memory
    "W_GRUDGE":      (0.0, 3.0),
    "GRUDGE_DECAY":  (0.98, 0.9995),
    # W4 rank posture
    "W_RANK_GUARD":  (0.0, 3.0),
    "W_RANK_AGGRO":  (0.0, 3.0),
    # W5 virus slot timing
    "VIRUS_SLOT_EXP": (0.0, 3.0),
}
# ===== OMNI-2.1 additions (PROFILER + corner refuge) =====
OMNI2_BOUNDS.update({
    "PROF_ON":                 (0.0, 1.0),
    "PROF_ELITE_T":            (0.5, 0.85),
    "PROF_STUPID_T":           (0.15, 0.5),
    "PROF_RADIUS":             (6.0, 25.0),
    "PROF_PREY_STUPID":        (0.0, 3.0),
    "PROF_PREY_ELITE_DISC":    (0.0, 0.9),
    "PROF_THREAT_STUPID_DISC": (0.0, 0.8),
    "PROF_THREAT_ELITE_MULT":  (0.0, 3.0),
    "PROF_FEAST_BOLD":         (0.0, 4.0),
    "W_CORNER_REFUGE":         (0.0, 4.0),
})
OMNI2_SCATTER = ["W_WEALTH_FEAR", "W_CAMP", "W_GRUDGE", "W_RANK_GUARD", "W_RANK_AGGRO", "VIRUS_SLOT_EXP",
                 "PROF_ON", "W_CORNER_REFUGE"]
