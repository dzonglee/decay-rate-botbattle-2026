"""GoBigger level-3 scripted bot clone (OpenDILab, ICLR 2023;
gobigger/agents/bot_agent.py), adapted to the SYNCS engine.

Original priority ladder, evaluated on the LARGEST balls only:
  1. If the biggest visible enemy ball can eat my biggest ball -> flee
     straight away from it (center-to-center, no prediction).
  2. Else chase the nearest *consumable* thorn (here: virus, if our biggest
     blob is over the pop threshold — in SYNCS a virus adds +1.5 mass but
     fragments us, same trade as GoBigger thorns).
  3. Else chase the nearest pellet.
  4. 2% chance per decision of a random split (original also had 2% eject;
     this engine has no eject action). 10% directional noise throughout.

The original's canned "7 idles + 8 splits" reproduce macro relies on
GoBigger merge timings and is omitted; the random splits keep its flavor.
"""

import math
import random

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

CONFIG = {
    "EAT_RATIO": 1.2,          # engine absorption rule (radius)
    "VIRUS_MIN_MASS": 1.8,     # engine: blob.mass > 1.5 * 1.2 to consume a virus
    "RANDOM_SPLIT_P": 0.02,
    "NOISE_RATIO": 0.1,
}


def choose(game: Game) -> tuple[float, float, bool]:
    me = game.state.me
    my_r = max((b.radius for b in me.blobs.values()), default=me.radius)

    enemies = [b for b in game.state.visible_blobs if b.player_id != me.player_id]
    if enemies:
        biggest = max(enemies, key=lambda b: b.radius)
        if biggest.radius >= my_r * CONFIG["EAT_RATIO"]:
            return (me.x - biggest.pos[0], me.y - biggest.pos[1], False)

    if my_r * my_r > CONFIG["VIRUS_MIN_MASS"] and game.state.visible_viruses:
        v = min(
            game.state.visible_viruses,
            key=lambda v: (v.pos[0] - me.x) ** 2 + (v.pos[1] - me.y) ** 2,
        )
        return (v.pos[0] - me.x, v.pos[1] - me.y, random.random() < CONFIG["RANDOM_SPLIT_P"])

    if game.state.visible_food:
        f = min(
            game.state.visible_food,
            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2,
        )
        return (f.pos[0] - me.x, f.pos[1] - me.y, random.random() < CONFIG["RANDOM_SPLIT_P"])

    return (30.0 - me.x, 30.0 - me.y, False)


def add_noise(dx: float, dy: float) -> tuple[float, float]:
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return (1.0, 0.0)
    return (
        dx / d + (random.random() * 2 - 1) * CONFIG["NOISE_RATIO"],
        dy / d + (random.random() * 2 - 1) * CONFIG["NOISE_RATIO"],
    )


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                dx, dy, split = choose(game)
                dx, dy = add_noise(dx, dy)
                game.send_move(
                    MovePlayer(
                        player_id=game.state.me.player_id,
                        direction=DirectionModel(x=dx, y=dy),
                        split=split,
                    )
                )
            case _:
                raise RuntimeError(f"Unsupported query type: {type(query)}")


if __name__ == "__main__":
    main()
