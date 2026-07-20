"""
SCAV_FIX - close the fragment-scavenger blind spot in feast clearance.

Decoded from T1's kill anatomy (54 kills, matches 1294/1318/1319, era I2):
T1 is a fragment scavenger. It never contests the feast itself - 89% of
its kills land >20 rounds AFTER our last virus consumption, against our
9-15 blob confetti, eating ~0.7-mass pieces one by one as they drift
back to merge. Its own mass at kill: 1.4-7. It waits out the shatter
and harvests the re-merge.

Why the champion is blind to it: the threat classifier tests
    b.radius >= my_smallest * SAFETY_RATIO
which is correct AFTER the shatter (T1 outclasses every piece) but the
FEAST DECISION happens BEFORE it, when my_smallest is a big blob and a
3-mass scavenger passes far under the ratio. The bot evaluates clearance
against the body it is about to trade away.

Fix - one source-derived condition. The engine gives the post-shatter
piece count exactly: piece_count = 16 - blobs + 1. So anticipated piece
mass and radius are known BEFORE consuming:

    piece_mass   = total_mass / (16 - len(my_blobs) + 1)
    piece_radius = sqrt(piece_mass)          # mass ~ radius^2
    scavenger    = any enemy blob within SCAV_CLEAR whose
                   radius >= piece_radius * EAT_RATIO * SCAV_MARGIN

If a scavenger is present, feast posture is suppressed: the virus is
treated as the hazard branch treats it (exactly the pre-feast behavior).
Big blobs that shatter into big pieces are unaffected - a 40-mass blob's
pieces (~2.5 mass each) still outclass T1, so it keeps feasting. It is
the SMALL-shatter feast (the i19 deleted-gate habit, and feast's own
low-mass slot-saturation entries) that gets vetoed, precisely the ones
T1 farms.

New genes (both evolvable, fix vetoable by bounds -> the population can
honestly vote the organ off if the gym says so):
    SCAV_CLEAR   9.0   scan radius for scavengers (T1 engages from close;
                       ~ lunge reach 8.9 rounded)
    SCAV_MARGIN  1.0   multiplier on the eat ratio; >1 = more paranoid,
                       <1 = only fear clearly-lethal scavengers

Usage: python3 tools/scav_patch.py bots/gen51_feast.py bots/gen51_scav.py
       python3 tools/scav_patch.py bots/gen099_i19.py bots/gen099_scav.py
"""

import ast
import re
import sys

NEW_GENES = {
    "SCAV_CLEAR": 9.0,
    "SCAV_MARGIN": 1.0,
}

src_path, dst_path = sys.argv[1], sys.argv[2]
s = open(src_path).read()

m = re.search(r'CONFIG\s*=\s*\{(.*?)\n\}', s, re.S)
cfg = ast.literal_eval('{' + m.group(1) + '}')
for k, v in NEW_GENES.items():
    cfg.setdefault(k, v)
rendered = "CONFIG = {\n" + "".join(f'    "{k}": {v!r},\n' for k, v in cfg.items()) + "}"
s = s[:m.start()] + rendered + s[m.end():]

# graft: extend the clearance test with the post-shatter scavenger check
old = '''    hunter_near = any(d < CONFIG["VIRUS_FEAST_CLEAR"] for _, d in info["threats"])'''
assert old in s, "clearance anchor missing (bot not feast-family?)"

new = '''    hunter_near = any(d < CONFIG["VIRUS_FEAST_CLEAR"] for _, d in info["threats"])
    # SCAV_FIX: clearance must be judged against the body we will have
    # AFTER the shatter, not the one we have now. Engine arithmetic:
    # piece_count = 16 - blobs + 1; piece_mass = total/pieces. Any enemy
    # blob near enough to harvest and big enough to eat those pieces is
    # a scavenger - invisible to the threat list (it keys off my_smallest
    # PRE-shatter) but lethal to the confetti. T1 doctrine, decoded from
    # 54 kills: it waits out the shatter and eats the re-merge.
    _pieces = max(1, 16 - len(my_blobs) + 1)
    _piece_r = math.sqrt(max(total_mass, EPS) / _pieces)
    _scav_r = _piece_r * CONFIG["EAT_RATIO"] * CONFIG["SCAV_MARGIN"]
    for _b in st.visible_blobs:
        if _b.player_id == me.player_id:
            continue
        if _b.radius >= _scav_r and \\
                math.hypot(_b.pos[0] - cx, _b.pos[1] - cy) < CONFIG["SCAV_CLEAR"]:
            hunter_near = True
            break'''

s = s.replace(old, new)
open(dst_path, "w").write(s)

check = ast.parse(open(dst_path).read())
n_keys = len(re.search(r'CONFIG\s*=\s*\{(.*?)\n\}', open(dst_path).read(), re.S).group(1).split('\n')) - 1
print(f"{dst_path}: syntax OK, ~{n_keys} CONFIG lines, SCAV_CLEAR={cfg['SCAV_CLEAR']}, SCAV_MARGIN={cfg['SCAV_MARGIN']}")
