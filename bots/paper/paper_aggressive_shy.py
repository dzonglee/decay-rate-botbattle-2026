"""AgarCL 'Aggressive-Shy' bot clone (The Cell Must Go On, arXiv:2505.18347).

Paper spec: like Aggressive, but "if a larger opponent approaches within its
'shy' radius, it immediately flees and only returns to hunting once the
threat has passed." Flee takes priority over hunt, hunt over pellets.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "HUNT_RADIUS": 12.0,
    "SHY_RADIUS": 7.0,
    "EAT_RATIO": 1.2,
    "THREAT_RATIO": 1.1,
}


def choose_direction(game: Game) -> tuple[float, float]:
    me = game.state.me
    my_r = max((b.radius for b in me.blobs.values()), default=me.radius)

    nearest_threat, threat_d = None, float("inf")
    nearest_prey, prey_d = None, float("inf")
    for b in game.state.visible_blobs:
        if b.player_id == me.player_id:
            continue
        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
        if b.radius >= my_r * CONFIG["THREAT_RATIO"]:
            if d < threat_d:
                nearest_threat, threat_d = b, d
        elif my_r >= b.radius * CONFIG["EAT_RATIO"]:
            if d < prey_d:
                nearest_prey, prey_d = b, d

    if nearest_threat is not None and threat_d < CONFIG["SHY_RADIUS"]:
        return (me.x - nearest_threat.pos[0], me.y - nearest_threat.pos[1])
    if nearest_prey is not None and prey_d < CONFIG["HUNT_RADIUS"]:
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
