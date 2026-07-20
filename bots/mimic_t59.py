"""T59-mimic: the rival virus-competitor missing from the gym that
wrongly certified gen099_i19 (+6.12 gym vs -2.6 live, matches 1165-1284).

Modelled on the decoded Team 59 (SUNMO) live profile:
  - feasts viruses from ~3 mass (barely above the 2.7 consume gate)
  - no hunter-clearance check, no slot discipline -> heavy shatter tax
  - boom-bust: compounds when unmolested, confettis when crowded
  - observed live rate ~7 consumptions/match in our lobbies

Purpose: gym ecology upgrade. This bot COMPETES FOR THE VIRUS ECONOMY,
so patient-feast doctrines pay the contested-resource price inside the
yardstick instead of discovering it live. Dumb on purpose - do not tune
it to be good; tune it to be T59.

Engine: agario-kit 2026.1.11 (consume gate mass>2.7, grant +2.25,
shatter piece_count = 16 - blobs + 1).
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

EAT = 1.2            # engine eat ratio (radius)
FEAST_MASS = 3.0     # T59 signature: feast from ~3 mass, right at the gate
FLEE_DIST = 5.0      # minimal self-preservation so it survives long enough to feast
PREY_DIST = 6.0      # opportunistic only - viruses come first (observed priority)


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
                # BlobModel exposes radius only; mass ~ radius^2
                total_mass = sum(b.radius ** 2 for b in my_blobs) if my_blobs else largest * largest

                dx, dy = 0.0, 0.0

                # 1. crude flight - only from very close, larger blobs
                threat, td = None, 1e9
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if b.radius >= largest * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < td:
                            threat, td = b, d
                if threat is not None and td < FLEE_DIST:
                    dx, dy = me.x - threat.pos[0], me.y - threat.pos[1]

                # 2. THE SIGNATURE: beeline to nearest virus once feast-capable.
                #    No clearance check, no blob-count discipline - T59 pays the
                #    shatter tax and does not care.
                elif total_mass >= FEAST_MASS and st.visible_viruses:
                    v = min(st.visible_viruses,
                            key=lambda v: (v.pos[0] - me.x) ** 2 + (v.pos[1] - me.y) ** 2)
                    dx, dy = v.pos[0] - me.x, v.pos[1] - me.y

                # 3. opportunistic prey if it is practically adjacent
                elif (p := _near_prey(st, me, largest)) is not None:
                    dx, dy = p.pos[0] - me.x, p.pos[1] - me.y

                # 4. otherwise forage
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
                    split=False,   # T59 does not split-lunge; it shatters instead
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


def _near_prey(st, me, largest):
    best, best_d = None, PREY_DIST
    for b in st.visible_blobs:
        if b.player_id == me.player_id:
            continue
        if largest >= b.radius * EAT:
            d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
            if d < best_d:
                best, best_d = b, d
    return best


if __name__ == "__main__":
    main()
