"""simple_bot: dumb NEAREST-FOOD WANDERER — a trivial dumb-bot seat for OMNI-EVO
self-play (NOT a mimic, NOT the old prey band). Seeks the nearest food pellet,
drifts to centre if none; never splits, never flees.

NOTE: OMNI_ARCHITECTURE.md referenced simple_bot.py as 'provided' but it was
absent on disk (2026-07-09); built here to the documented behaviour.
Engine: agario-kit 2026.1.12.
"""
from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                st = game.state
                me = st.me
                if st.visible_food:
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
