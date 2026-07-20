"""Groningen 'Greedy' bot clone (Wiehe et al. 2018, arXiv:1809.05763).

Paper spec: "preprogrammed to move towards the cell with the highest
cell_mass / distance ratio. It ignores cells with a mass above its biggest
own cell's absorption threshold. The bot also has no splitting or ejecting
behavior." Note: it never flees — its documented weakness is no path
planning / no fear, yet it beat every RL agent they trained at fighting.

Pellets and edible enemy blobs compete on the same mass/distance scale.
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "EAT_RATIO": 1.2,      # absorption threshold (engine, on radius)
    "FOOD_MASS": 0.0225,   # engine: one pellet adds ~0.0225 mass (r 0.9 -> 0.9124)
}


def choose_direction(game: Game) -> tuple[float, float]:
    me = game.state.me
    my_r = max((b.radius for b in me.blobs.values()), default=me.radius)

    best_ratio, best_target = -1.0, None
    for f in game.state.visible_food:
        d = math.hypot(f.pos[0] - me.x, f.pos[1] - me.y)
        if d < 1e-9:
            continue
        ratio = CONFIG["FOOD_MASS"] / d
        if ratio > best_ratio:
            best_ratio, best_target = ratio, f.pos
    for b in game.state.visible_blobs:
        if b.player_id == me.player_id:
            continue
        if my_r < b.radius * CONFIG["EAT_RATIO"]:
            continue  # above absorption threshold: ignored entirely
        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
        if d < 1e-9:
            continue
        ratio = (b.radius * b.radius) / d
        if ratio > best_ratio:
            best_ratio, best_target = ratio, b.pos

    if best_target is not None:
        return (best_target[0] - me.x, best_target[1] - me.y)
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
