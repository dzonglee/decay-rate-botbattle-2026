"""P4-mimic: the leaderboard meta. Relentless chase of nearest edible player,
splits on every opportunity, eats food only when no prey visible. Dumb on
purpose — this is the sparring partner, modelled on observed winner behaviour."""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

EAT = 1.2


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
                # nearest edible enemy blob
                prey, best_d = None, 1e9
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if largest >= b.radius * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < best_d:
                            prey, best_d = b, d
                split = False
                if prey is not None:
                    dx, dy = prey.pos[0] - me.x, prey.pos[1] - me.y
                    # split-lunge whenever halves would still eat them and in reach
                    half_r = largest / math.sqrt(2)
                    if best_d < 8.5 and half_r >= prey.radius * EAT and largest * largest >= 4.0:
                        split = True
                elif st.visible_food:
                    t = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = t.pos[0] - me.x, t.pos[1] - me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y
                    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                        dx = 1.0
                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=split,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
