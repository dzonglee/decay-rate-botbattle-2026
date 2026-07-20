"""AgarCL 'Hungry' bot clone (The Cell Must Go On, arXiv:2505.18347).

Paper spec: "ignores other players entirely and chases the closest pellet
at every step." Identical in spirit to the official template bot; kept as a
separate faithful clone so the paper field is self-contained.
"""

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {}  # Hungry has no parameters: nearest pellet, always.


def choose_direction(game: Game) -> tuple[float, float]:
    me = game.state.me
    if game.state.visible_food:
        target = min(
            game.state.visible_food,
            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2,
        )
        return (target.pos[0] - me.x, target.pos[1] - me.y)
    return (30.0 - me.x, 30.0 - me.y)


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                dx, dy = choose_direction(game)
                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                game.send_move(
                    MovePlayer(
                        player_id=game.state.me.player_id,
                        direction=DirectionModel(x=dx, y=dy),
                    )
                )
            case _:
                raise RuntimeError(f"Unsupported query type: {type(query)}")


if __name__ == "__main__":
    main()
