"""AgarCL 'Hungry-Shy' clone, timid tuning: flees much earlier (radius 10 vs 6)
and from anything even equal-sized. Second tuning of the same archetype so the
field probes both a bold and a paranoid forager.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "SHY_RADIUS": 10.0,
    "THREAT_RATIO": 1.0,
}


def choose_direction(game: Game) -> tuple[float, float]:
    me = game.state.me
    my_r = max((b.radius for b in me.blobs.values()), default=me.radius)

    nearest_threat, nearest_d = None, float("inf")
    for b in game.state.visible_blobs:
        if b.player_id == me.player_id:
            continue
        if b.radius >= my_r * CONFIG["THREAT_RATIO"]:
            d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
            if d < nearest_d:
                nearest_threat, nearest_d = b, d
    if nearest_threat is not None and nearest_d < CONFIG["SHY_RADIUS"]:
        return (me.x - nearest_threat.pos[0], me.y - nearest_threat.pos[1])

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
