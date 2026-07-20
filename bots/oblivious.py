"""Oblivious: forages competently (nearest-pellet beeline, the field's own
policy), never evades anything. Calibration target: the live corpus's median
victim — reaches established mass then dies mid-graze to a marginal hunter."""
import math
from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel


def main():
    game = Game()
    while True:
        q = game.get_next_query()
        match q:
            case QueryMovePlayer():
                st, me = game.state, game.state.me
                dx, dy = 30.0 - me.x, 30.0 - me.y
                if st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0]-me.x)**2 + (f.pos[1]-me.y)**2)
                    dx, dy = f.pos[0]-me.x, f.pos[1]-me.y
                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                game.send_move(MovePlayer(player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy), split=False))
            case _:
                raise RuntimeError("unsupported")


if __name__ == "__main__":
    main()
