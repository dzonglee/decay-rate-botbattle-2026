"""Opponent archetype: AGGRESSIVE — chases the nearest edible enemy blob,
falls back to nearest food. Reconstruction of a common leaderboard style for
anti-meta tuning (instructions/02-TUNING-PLAN.md §5). Not a submission."""

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

EAT_RATIO = 1.2


def choose_direction(game: Game) -> tuple[float, float]:
    st = game.state
    me = st.me
    my_largest = max((b.radius for b in me.blobs.values()), default=me.radius)

    prey = [
        b for b in st.visible_blobs
        if b.player_id != me.player_id and my_largest >= b.radius * EAT_RATIO
    ]
    if prey:
        target = min(prey, key=lambda b: (b.pos[0] - me.x) ** 2 + (b.pos[1] - me.y) ** 2)
        return (target.pos[0] - me.x, target.pos[1] - me.y)

    if st.visible_food:
        target = min(
            st.visible_food,
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
