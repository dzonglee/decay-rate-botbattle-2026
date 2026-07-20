"""AgarCL 'Aggressive' bot clone (The Cell Must Go On, arXiv:2505.18347).

Paper spec: "first looks for any smaller opponent within a defined radius and
attempts to consume it; if no suitable target is found, it switches to pellet
collection." No fear whatsoever.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "HUNT_RADIUS": 12.0,  # only chase prey within this distance
    "EAT_RATIO": 1.2,     # engine absorption rule (radius)
}


def choose_direction(game: Game) -> tuple[float, float]:
    me = game.state.me
    my_r = max((b.radius for b in me.blobs.values()), default=me.radius)

    nearest_prey, nearest_d = None, float("inf")
    for b in game.state.visible_blobs:
        if b.player_id == me.player_id:
            continue
        if my_r >= b.radius * CONFIG["EAT_RATIO"]:
            d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
            if d < nearest_d:
                nearest_prey, nearest_d = b, d
    if nearest_prey is not None and nearest_d < CONFIG["HUNT_RADIUS"]:
        return (nearest_prey.pos[0] - me.x, nearest_prey.pos[1] - me.y)

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
