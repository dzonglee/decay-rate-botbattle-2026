"""AgarCL 'Hungry-Shy' bot clone (The Cell Must Go On, arXiv:2505.18347).

Paper spec: focused on pellet foraging like Hungry, but "monitors for larger
opponents: if one comes too close, it retreats before resuming its hunt."
Retreat is the classic straight-line flee from the nearest dangerous blob.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "SHY_RADIUS": 6.0,    # flee when a larger blob is within this distance
    "THREAT_RATIO": 1.1,  # 'larger' = radius >= ours * this
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
