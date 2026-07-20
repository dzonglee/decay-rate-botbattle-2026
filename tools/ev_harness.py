#!/usr/bin/env python3
"""ev_harness.py — continuous-state evasion trial (the 'best immediate
experiment' per the 2026-07-16 review). Paired-seed comparison of escape
policies against a pursuer with ENGINE-EXACT movement physics (divisive speed
law, [r, size-r] wall clamp, center-in-eater-radius capture, split-strike
kinematics with eject 1.6 / drag 0.82).

Policies:
  deadaway   flee directly away from the pursuer
  field      reactive repulsion (threat + wall), the force-field baseline
  ev_raw     solved EV table heading, hard override
  ev_blend   field + EV table as a weighted force (current body integration)
  ev_mpc     EV table candidate + 2 neighbors, 6-tick rollout picks (EV-guided MPC)
  hz_mpc     ev_mpc but rollout risk term = MINED HAZARD leaf (survival-discounted)

Randomized per episode: our radius, pursuer radius, positions (wall/corner
biased), pursuer split availability, approach angle. Pursuer plays pure
pursuit + opportunistic split-strike. Same seeds across all policies.
Metrics: survival rate to T=80 and mean survival ticks.
"""
import math, random, sys, importlib.util

spec = importlib.util.spec_from_file_location(
    "body", "/Users/chrisli/Developer/competition/botbattle/bots/omni_mixer_v3.py")
try:
    body = importlib.util.module_from_spec(spec); spec.loader.exec_module(body)
except Exception:
    sys.path.insert(0, "/Users/chrisli/Developer/competition/botbattle/tools")
    raise

ARENA = 60.0
EJECT, DRAG, EAT = 1.6, 0.82, 1.2

def speed(r):
    return max(0.25, 1.1 / (1.0 + 0.08 * r))

def unit(dx, dy):
    m = math.hypot(dx, dy)
    return (dx / m, dy / m) if m > 1e-9 else (0.0, 0.0)

def clamp(x, r):
    return min(max(x, r), ARENA - r)

def ev_heading(px, py, tx, ty, cls, sp):
    sgx = 1.0 if px <= ARENA / 2 else -1.0
    sgy = 1.0 if py <= ARENA / 2 else -1.0
    wx = px if sgx > 0 else ARENA - px
    wy = py if sgy > 0 else ARENA - py
    a = body._ev_lookup(wx, wy, (tx - px) * sgx, (ty - py) * sgy, cls, sp)
    hx, hy = body._EV_DIRS[a]
    return hx * sgx, hy * sgy

def field_heading(px, py, tx, ty, tr):
    ux, uy = unit(px - tx, py - ty)
    d = math.hypot(px - tx, py - ty)
    fx = ux * (tr * tr) / (d * d + 1.0) * 12.0
    fy = uy * (tr * tr) / (d * d + 1.0) * 12.0
    for wall, toward in ((px, (1, 0)), (ARENA - px, (-1, 0)), (py, (0, 1)), (ARENA - py, (0, -1))):
        if wall < 6.0:
            fx += toward[0] * (6.0 - wall) * 0.6
            fy += toward[1] * (6.0 - wall) * 0.6
    return unit(fx, fy)

def rollout_score(px, py, hx, hy, tx, ty, tr, our_r, sp, H=6, hz=False):
    s, qx, qy, ex, ey = 0.0, px, py, tx, ty
    ts = speed(tr)
    for h in range(H):
        qx = clamp(qx + hx * speed(our_r), our_r)
        qy = clamp(qy + hy * speed(our_r), our_r)
        ux, uy = unit(qx - ex, qy - ey)
        ex += ux * ts; ey += uy * ts
        d = math.hypot(qx - ex, qy - ey)
        if d <= tr:
            return -1000.0 + h
        if sp and d <= 2.0 * math.sqrt(tr * tr / 2.0) + 4.0:
            s -= 50.0 / (h + 1)
        if hz:
            h1, sup = body._plan_hz_step(qx, qy, [(ex, ey, 0.0, 0.0, tr, tr * tr)],
                                         our_r, 0, 1, speed(our_r))
            s -= 120.0 * sup * h1
        else:
            s += d * 0.1
    return s

def episode(seed, policy):
    rng = random.Random(seed)
    our_r = rng.uniform(1.2, 2.5)
    tr = rng.uniform(3.0, 7.0)
    corner = rng.random() < 0.5
    if corner:
        px = rng.uniform(our_r, 8.0); py = rng.uniform(our_r, 8.0)
        if rng.random() < 0.5: px = ARENA - px
        if rng.random() < 0.5: py = ARENA - py
    else:
        px = rng.uniform(5, 55); py = rng.uniform(5, 55)
    ang = rng.uniform(0, 2 * math.pi)
    dist = rng.uniform(5.0, 9.0)
    tx = clamp(px + math.cos(ang) * dist, tr)
    ty = clamp(py + math.sin(ang) * dist, tr)
    sp = rng.random() < 0.6
    piece = None                         # (x, y, vx, vy, r)
    cls = 1 if (tr * tr) / 2.0 > (our_r * our_r) * EAT else 0
    for t in range(1, 81):
        if policy == "deadaway":
            hx, hy = unit(px - tx, py - ty)
        elif policy == "field":
            hx, hy = field_heading(px, py, tx, ty, tr)
        elif policy == "ev_raw":
            hx, hy = ev_heading(px, py, tx, ty, cls, 1 if sp else 0)
        elif policy == "ev_blend":
            fx0, fy0 = field_heading(px, py, tx, ty, tr)
            ex0, ey0 = ev_heading(px, py, tx, ty, cls, 1 if sp else 0)
            hx, hy = unit(fx0 + 2.0 * ex0, fy0 + 2.0 * ey0)
        elif policy == "hz_mpc":
            base = ev_heading(px, py, tx, ty, cls, 1 if sp else 0)
            ba = math.atan2(base[1], base[0])
            best, hx, hy = -1e18, base[0], base[1]
            for off in (0.0, 0.79, -0.79):
                cx_, cy_ = math.cos(ba + off), math.sin(ba + off)
                s = rollout_score(px, py, cx_, cy_, tx, ty, tr, our_r, sp, hz=True)
                if s > best:
                    best, hx, hy = s, cx_, cy_
        else:                            # ev_mpc
            base = ev_heading(px, py, tx, ty, cls, 1 if sp else 0)
            ba = math.atan2(base[1], base[0])
            best, hx, hy = -1e18, base[0], base[1]
            for off in (0.0, 0.79, -0.79):
                cx_, cy_ = math.cos(ba + off), math.sin(ba + off)
                s = rollout_score(px, py, cx_, cy_, tx, ty, tr, our_r, sp)
                if s > best:
                    best, hx, hy = s, cx_, cy_
        px = clamp(px + hx * speed(our_r), our_r)
        py = clamp(py + hy * speed(our_r), our_r)
        ux, uy = unit(px - tx, py - ty)
        tx = clamp(tx + ux * speed(tr), tr)
        ty = clamp(ty + uy * speed(tr), tr)
        d = math.hypot(px - tx, py - ty)
        if d <= tr:
            return t
        if sp and piece is None:
            pr = math.sqrt(tr * tr / 2.0)
            if pr * pr > (our_r * our_r) * EAT and d < 2 * pr + 5.0:
                piece = [tx + ux * (pr + pr), ty + uy * (pr + pr), ux * EJECT, uy * EJECT, pr]
                sp = False
        if piece is not None:
            bx, by, vx, vy, pr = piece
            bs = speed(pr)
            pux, puy = unit(px - bx, py - by)
            vx = vx * DRAG + pux * bs * (1 - DRAG)
            vy = vy * DRAG + puy * bs * (1 - DRAG)
            bx += vx; by += vy
            piece = [bx, by, vx, vy, pr]
            if (px - bx) ** 2 + (py - by) ** 2 <= pr * pr:
                return t
    return 81                            # survived

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    pols = ["deadaway", "field", "ev_raw", "ev_blend", "ev_mpc", "hz_mpc"]
    res = {p: [] for p in pols}
    for s in range(N):
        for p in pols:
            res[p].append(episode(s, p))
    print(f"paired episodes: {N} (randomized radii/positions/walls/split; T=80)")
    print(f"{'policy':<10} {'survival%':>9} {'mean ticks':>10}")
    for p in pols:
        v = res[p]
        surv = 100 * sum(1 for x in v if x > 80) / len(v)
        print(f"{p:<10} {surv:>8.1f}% {sum(v)/len(v):>10.1f}")

if __name__ == "__main__":
    main()
