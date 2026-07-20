# SCAVTRIALS BUNDLE — complete, self-sufficient Studio handover

One archive, everything the trial session needs. Supersedes the split
decayrate_kit_gymv2 / _evov2 / _scavfix delivery that stranded the
first session. Verify EVERY file against MANIFEST.sha256 before use:

    shasum -a 256 -c MANIFEST.sha256

All eight hashes must say OK, or STOP.

## Contents
bots/  gen51_feast.py, gen099_i19.py        (certified champions)
       gen51_scav.py, gen099_scav.py        (SCAV_FIX-patched bodies)
       mimic_t59.py, mimic_t1.py            (gym predators)
tools/ scav_patch.py, evolve_v2.py
docs:  SCAV_FIX.md (trials + GYM_V3), EVOLVE_V2.md (launch + v1 bug),
       GYM_V2.md (superseded by GYM_V3; kept for the record)

## ENGINE — the Studio is STALE and must upgrade first
Installed 2026.1.9 = the dead-virus-economy engine (consumption grants
ZERO mass). Any feast trial run on .9 is fiction; the version gate that
stopped the session was correct. Upgrade in the trial venv:

    pip install --upgrade 'agario-kit==2026.1.11'
    pip show agario-kit | grep Version     # must print 2026.1.11

2026.1.11 is confirmed LATEST on PyPI as of 2026-07-08. Pin exactly;
do not float. Then: python3 tools/speed_patch.py set 0.01

## Resume point
Re-run the trial prompt from Step 1 (unpack = this bundle; hash gate =
MANIFEST.sha256; Step 2 engine gate now passes after the upgrade).
Steps 3–7 unchanged: GYM_V3 validation gate, scav 3×n=20, i19-scav
bench, evolve_v2 detached launch, report with no verdicts.
