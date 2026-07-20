"""Sluggish: forages like oblivious, but flees when a bigger blob is within
3 units — too late against a committed chase, enough against a distracted one.
The half-competent middle of the incompetence band."""
import math
from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

PANIC = 3.0


def main():
    game = Game()
    while True:
        q = game.get_next_query()
        match q:
            case QueryMovePlayer():
                st, me = game.state, game.state.me
                largest = max((b.radius for b in me.blobs.values()), default=me.radius)
                threat, td = None, 1e9
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if b.radius >= largest * 1.2:
                        d = math.hypot(b.pos[0]-me.x, b.pos[1]-me.y)
                        if d < td:
                            threat, td = b, d
                if threat is not None and td < PANIC:
                    dx, dy = me.x - threat.pos[0], me.y - threat.pos[1]
                elif st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0]-me.x)**2 + (f.pos[1]-me.y)**2)
                    dx, dy = f.pos[0]-me.x, f.pos[1]-me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y
                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                game.send_move(MovePlayer(player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy), split=False))
            case _:
                raise RuntimeError("unsupported")


if __name__ == "__main__":
    main()
