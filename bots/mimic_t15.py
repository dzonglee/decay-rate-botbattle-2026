"""T15-mimic: Team-15's sub-784 apex — the CURRENT competition #1. Replaces
mimic_t44/Engorgio in the gym so the room holds the current #1's shape.

REBUILT 2026-07-09 from RAW REPLAYS (matches 1719-1724, decoded from
elite_g30_replays_1449_1724.zip). The prior build was split=False — WRONG on the
single defining behavior: the real Team-15 SPLITS aggressively (~21 split-moves in
match 1721) and oscillates blob count 1<->16 to run the .12 virus economy. This
rebuild adds the split cycle.

Raw-decoded profile (matches 1719/1721/1723 = its 100-mass WINS):
  - splits ~21/match; blob count oscillates 1<->16
  - virus consumptions 32-43/match, +2.25 each (CONSERVED through the shatter) ->
    ~90% of a 100-mass game comes from viruses; 26% of cons land at >=15 blobs
    (pieces=1, free mass), 46% at 1 blob (max shatter) -- BIMODAL, shatter embraced
  - kills 33-42/match (split-spread also spreads the hunt)
  - HIGH-VARIANCE: in 1720/1722/1724 the snowball fizzled (3-13 cons, <25 mass).
    That volatility is the real doctrine -- it snowballs to 100 or fizzles.
  - win rate 32.6% (event_player_won) still holds; magnitude now RAW-VERIFIED.

Doctrine: split to spread, vacuum respawning viruses, hunt the pieces, barely flee.
Dumb on purpose -- tuned to BE Team-15, not to win.
Engine: agario-kit 2026.1.12 (MASS-rule eat; virus grants +2.25, shatter into
max(1, 16-blobs+1) pieces).
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
PREY_DIST = 16.0     # moderate hunter -> grows to feed the feast
VIRUS_BIAS = 1.6     # prefer a virus unless a prey is much closer
# --- SPLIT CYCLE (raw-decoded from Team-15 matches 1719/1721/1723) ---
SPLIT_GATE = 6.0     # total mass before it starts splitting to spread/feast
SPLIT_CLEAR = 3.0    # no lethal threat within this dist to split (brave)


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

                # nearest lethal threat (MASS rule)
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
                # nearest edible prey (MASS rule)
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
                chasing = False  # True when moving toward a virus or prey (split-worthy)
                # 1. flee only a very close lethal blob
                if threat is not None and td < FLEE_DIST:
                    dx, dy = me.x - threat.pos[0], me.y - threat.pos[1]
                # 2. APEX FEAST vs HUNT: prefer the virus unless a prey is much closer
                elif virus_ok and (prey is None or nvd <= pd * VIRUS_BIAS):
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                    chasing = True
                elif prey is not None:
                    dx, dy = prey.pos[0] - me.x, prey.pos[1] - me.y
                    chasing = True
                elif virus_ok:
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                    chasing = True
                # 3. forage
                elif st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y

                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0

                # SPLIT CYCLE: split toward a virus/prey when big enough, safe, and
                # blob slots remain -> spreads to hunt AND lands virus cons at high
                # blob count (pieces=1, free mass). Regroup (no split) when a threat
                # is close or nothing to chase.
                split = (chasing
                         and total_mass >= SPLIT_GATE
                         and len(my_blobs) < 16
                         and mass(largest) >= 4.0            # halves stay above engine split-min
                         and (threat is None or td >= SPLIT_CLEAR))

                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=split,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
