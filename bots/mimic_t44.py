"""T15-mimic: Team-15's sub-784 apex — the CURRENT competition #1 (24.50 rating,
189-match DEEP window; surged +4.3 today). Replaces mimic_t44/Engorgio (#4,
falling) in the gym so the room always holds the current #1's shape.

PROVENANCE — Hermes block, MAGNITUDE UNVERIFIED.
  rival_replays_t15.zip has NOT landed, so the sub-784 magnitude could NOT be
  recomputed from raw events (the standard recompute that caught the 837 block's
  48-mass/100%-win inflation). Built to Hermes's block; RE-VERIFY (win rate via
  event_player_won only, avg mass, cons profile) when the zip arrives.

  The block's SHAPE self-verifies: it is a near-twin of Engorgio sub-751, which I
  DID decode from raw events (rival_replays_1288_1448, team_id 44) —
    metric        Team-15 sub-784 (Hermes)   Engorgio sub-751 (raw-verified)
    cons/match         17.98                      ~18
    mass@cons          46.3  (49% at 40+)         46.8  (49% at 40+)
    kills/match        18.3                       ~18
  Two independent apex feasters converging on the same doctrine — so the SHAPE is
  credible even though the sub-784 RATING (24.50) is not yet raw-confirmed.

Hermes block (sub-784 era / i19 co-lobbies, n=46, matches ~1449+):
  - avg mass 30.69, cons 17.98/match, kills 18.3/match
  - mass@cons 46.3 (49% of cons at 40+ mass — heavy feaster), blobs@cons 7.2
  - win rate 32.6% (15/46, event_player_won); H2H vs us 15-13-18 (dead even)

Doctrine: heavy virus-feast (~18 cons) + hunt-to-grow (~18 kills), barely flees —
identical structure to Engorgio, PORTED to the .12 MASS-rule eat (mimic_t44 was
still radius-miscalibrated, so it fled edible blobs and mis-priced lethal ones on
.12). Dumb on purpose — tuned to BE Team-15, not to win.
Engine: agario-kit 2026.1.12 (MASS-rule eat: eater.mass >= target.mass * 1.2).

IN-GYM VERIFICATION (this build, uncontested n=8, gen-31 swap):
  mass@cons 45.7 (target 46.3) and 54% of cons at 40+ (target 49%) — the defining
  heavy-feast signature reproduces DEAD-ON and is stable across PREY_DIST/VIRUS_BIAS
  sweeps. Absolute cons/kills run high in the sterile lobby (25 cons / 35 kills)
  because incompetence prey respawn and get farmed — that count is an ENVIRONMENT
  artifact, not a doctrine number, and no gene monotonically controls it. Kept the
  Engorgio-verified genes (PREY_DIST 16, VIRUS_BIAS 1.6) rather than over-fit the
  farm noise to an unverified magnitude. True contested cons/kills magnitude awaits
  rival_replays_t15.zip for a raw-event recompute.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

EAT = 1.2            # .12 MASS eat ratio (mass, not radius)
FEAST_GATE = 20.0    # feast once moderately big -> consumptions center 40+ (mass@cons ~46)
FLEE_DIST = 2.5      # very brave: stays in the fray to feast (Engorgio-brave)
VIRUS_RANGE = 26.0   # crosses the arena for a virus (apex feast priority)
PREY_DIST = 16.0     # moderate hunter (~18 kills/match) — grows to feed the feast
VIRUS_BIAS = 1.6     # prefer a virus unless a prey is much closer (keeps cons/match ~18)


def mass(r: float) -> float:
    return r * r


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                st = game.state
                me = st.me
                my_blobs = list(me.blobs.values())
                largest = max((b.radius for b in my_blobs), default=me.radius)
                lm = mass(largest)
                total_mass = sum(mass(b.radius) for b in my_blobs) if my_blobs else lm

                # nearest lethal threat (MASS rule: enemy eats me if enemy.mass >= my.mass * EAT)
                threat, td = None, 1e9
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if mass(b.radius) >= lm * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < td:
                            threat, td = b, d
                # nearest virus
                nv, nvd = None, 1e9
                for v in st.visible_viruses:
                    d = math.hypot(v.pos[0] - me.x, v.pos[1] - me.y)
                    if d < nvd:
                        nv, nvd = v, d
                # nearest edible prey (MASS rule: I eat if my.mass >= prey.mass * EAT)
                prey, pd = None, PREY_DIST
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if lm >= mass(b.radius) * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < pd:
                            prey, pd = b, d

                virus_ok = total_mass >= FEAST_GATE and nv is not None and nvd <= VIRUS_RANGE
                dx, dy = 0.0, 0.0
                # 1. flee only a very close lethal blob
                if threat is not None and td < FLEE_DIST:
                    dx, dy = me.x - threat.pos[0], me.y - threat.pos[1]
                # 2. APEX FEAST vs HUNT: prefer the virus unless a prey is much closer
                elif virus_ok and (prey is None or nvd <= pd * VIRUS_BIAS):
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                elif prey is not None:
                    dx, dy = prey.pos[0] - me.x, prey.pos[1] - me.y
                elif virus_ok:
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                # 3. forage
                elif st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y

                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=False,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
