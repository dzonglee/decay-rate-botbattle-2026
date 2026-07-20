"""naive_splitter: dumb FRAGMENT-PRONE SPLITTER — the dissimilar second dumb-bot
seat for OMNI-EVO self-play (maximally unlike simple_bot's food-seeker). Splits
every tick a blob is viable, so it fragments itself relentlessly and supplies
high-blob-count targets (exercises the population's fragment-hunt / piece-guard
organs). Drifts toward nearest food otherwise. NOT a mimic, NOT the old prey band.
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
                my_blobs = list(me.blobs.values())
                largest = max((b.radius for b in my_blobs), default=me.radius)
                if st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y
                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                # split relentlessly: any tick a half stays above the engine split-min
                split = (largest * largest >= 4.0) and (len(my_blobs) < 16)
                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=split,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
