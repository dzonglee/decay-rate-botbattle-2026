"""Short-horizon lookahead veto gate — faithful to agario-kit 2026.1.x physics.

Pure-python, zero imports beyond math: drops into the bot body with no import
cost. Simulates the ballistic trajectory of SPLIT HALVES and the pursuit/flee
geometry of threats and targets, a few ticks ahead, to VETO unsafe commits the
reactive force-field policy cannot see:

  1. virus_split_veto  — a pop-capable launched half whose path clips a visible
     virus (assumption-free: viruses are visible + stationary).
  2. split_miss_veto   — after splitting, a half is eatable by worst-case pursuit
     (assume every bigger threat drives straight at it).
  3. attack_lands      — a launched half actually reaches a target that flees
     optimally (so we only commit kills that beat perfect defense).

The gate is advisory: policy proposes (dir, split); gate returns a possibly
de-escalated (dir, split). It never invents aggression, only removes unsafe
aggression — so the worst case is a passed-up kill, never a new death.
"""
import math

# --- engine constants (lib/config, 2026.1.x) ---
BASE_SPEED = 1.1
SPEED_RADIUS_FACTOR = 0.08
MIN_SPEED = 0.25
SPLIT_MIN_MASS = 2.0
SPLIT_EJECT_SPEED = 1.6
SPLIT_EJECT_DRAG = 0.82
SPLIT_COOLDOWN = 18
EAT_RATIO = 1.2
VIRUS_RADIUS = 1.5
VIRUS_POP_MASS = (VIRUS_RADIUS ** 2) * EAT_RATIO   # blob.mass must EXCEED this to pop (2.7)
ARENA = 60.0
_EPS = 1e-9


def _speed(r):
    return max(MIN_SPEED, BASE_SPEED / (1.0 + r * SPEED_RADIUS_FACTOR))


def _unit(dx, dy):
    d = math.hypot(dx, dy)
    return (dx / d, dy / d) if d > _EPS else (0.0, 0.0)


def _child_after_split(bx, by, mass, sx, sy):
    """Return (x, y, radius, mass, vx, vy) for the launched half of a splitting blob."""
    child_r = math.sqrt(mass / 2.0)
    x = bx + sx * (child_r + child_r)           # parent_r == child_r after even split
    y = by + sy * (child_r + child_r)
    return x, y, child_r, mass / 2.0, sx * SPLIT_EJECT_SPEED, sy * SPLIT_EJECT_SPEED


def _step_ballistic(x, y, vx, vy, r, steer_x, steer_y):
    """One engine tick of a blob under a steering unit-vector + decaying eject velocity."""
    sp = _speed(r)
    x += steer_x * sp + vx
    y += steer_y * sp + vy
    vx *= SPLIT_EJECT_DRAG
    vy *= SPLIT_EJECT_DRAG
    if abs(vx) < 1e-4: vx = 0.0
    if abs(vy) < 1e-4: vy = 0.0
    x = min(ARENA, max(0.0, x)); y = min(ARENA, max(0.0, y))
    return x, y, vx, vy


def _path_hits_virus(x, y, r, vx, vy, sx, sy, viruses, horizon):
    """Step a blob (steering sx,sy + eject vx,vy) forward; True if a virus enters its disk."""
    for _ in range(horizon):
        for (vx0, vy0) in viruses:
            if (x - vx0) ** 2 + (y - vy0) ** 2 <= r * r:
                return True
        x, y, vx, vy = _step_ballistic(x, y, vx, vy, r, sx, sy)
    return False


def virus_split_veto(my_blobs, sx, sy, viruses, horizon=5):
    """True => splitting here drives a pop-capable PARENT or CHILD through a visible
    virus. Checks both: the child is flung ballistically ahead; the parent (now half
    mass) keeps steering in the split direction. my_blobs: (x, y, mass); viruses: (x, y)."""
    if not viruses:
        return False
    for (bx, by, mass) in my_blobs:
        if mass < SPLIT_MIN_MASS:
            continue
        half = mass / 2.0
        if half <= VIRUS_POP_MASS:         # both halves too small to pop — safe
            continue
        hr = math.sqrt(half)
        # parent stays at bx,by (half mass) and steers forward, no eject
        if _path_hits_virus(bx, by, hr, 0.0, 0.0, sx, sy, viruses, horizon):
            return True
        # child launches ahead with eject velocity
        cx, cy, cr, _cm, evx, evy = _child_after_split(bx, by, mass, sx, sy)
        if _path_hits_virus(cx, cy, cr, evx, evy, sx, sy, viruses, horizon):
            return True
    return False


def split_miss_veto(my_blobs, sx, sy, threats, horizon=4):
    """True => after splitting, a half is caught by worst-case pursuit. VETO.
    threats: list of (x, y, mass) of blobs that could eat a half (bigger)."""
    if not threats:
        return False
    for (bx, by, mass) in my_blobs:
        if mass < SPLIT_MIN_MASS:
            continue
        cx, cy, cr, cmass, vx, vy = _child_after_split(bx, by, mass, sx, sy)
        for (tx, ty, tmass) in threats:
            if tmass <= cmass * EAT_RATIO:        # can't eat this half
                continue
            hx, hy = cx, cy; hvx, hvy = vx, vy; ex, ey = tx, ty
            tr = math.sqrt(tmass); ts = _speed(tr)
            for _ in range(horizon):
                # threat drives straight at the half (worst case)
                ux, uy = _unit(hx - ex, hy - ey)
                ex += ux * ts; ey += uy * ts
                hx, hy, hvx, hvy = _step_ballistic(hx, hy, hvx, hvy, cr, sx, sy)
                if (hx - ex) ** 2 + (hy - ey) ** 2 <= (math.sqrt(tmass) + cr) ** 2:
                    return True
    return False


def attack_lands(bx, by, mass, target, sx, sy, horizon=5):
    """True => a launched half reaches a target that flees optimally, and can eat it.
    target: (x, y, mass)."""
    tx, ty, tmass = target
    cx, cy, cr, cmass, vx, vy = _child_after_split(bx, by, mass, sx, sy)
    if cmass <= tmass * EAT_RATIO:            # can't eat it even on contact
        return False
    tr = math.sqrt(tmass); ts = _speed(tr)
    for _ in range(horizon):
        fx, fy = _unit(tx - bx, ty - by)      # target flees away from our origin
        tx += fx * ts; ty += fy * ts
        cx, cy, vx, vy = _step_ballistic(cx, cy, vx, vy, cr, sx, sy)
        if (cx - tx) ** 2 + (cy - ty) ** 2 <= (cr + tr) ** 2:
            return True
    return False


def gate(dir_x, dir_y, split, my_blobs, viruses, threats, target=None):
    """Veto layer over the policy's proposed move. Returns (dir_x, dir_y, split).
    Removes unsafe splits; never adds aggression."""
    if not split:
        return dir_x, dir_y, split
    sx, sy = _unit(dir_x, dir_y)
    if sx == 0.0 and sy == 0.0:
        return dir_x, dir_y, split
    if virus_split_veto(my_blobs, sx, sy, viruses):
        return dir_x, dir_y, False            # would clip a virus -> don't split
    if split_miss_veto(my_blobs, sx, sy, threats):
        return dir_x, dir_y, False            # miss-case is fatal -> don't split
    if target is not None and my_blobs:
        bx, by, mass = my_blobs[0]
        if not attack_lands(bx, by, mass, target, sx, sy):
            return dir_x, dir_y, False        # won't land vs optimal flee -> hold
    return dir_x, dir_y, split
