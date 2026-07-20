"""PROBE: dump what the event feed + rankings actually deliver to a live bot."""
import json, sys
from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

def main():
    game = Game()
    seen = {}
    n = 0
    while True:
        q = game.get_next_query()
        if isinstance(q, QueryMovePlayer):
            n += 1
            st = game.state
            if n in (5, 100, 400):
                far_virus_events = 0
                eaten_events = 0
                for e in st.event_history[-200:]:
                    et = getattr(e, "event_type", "?")
                    seen[et] = seen.get(et, 0) + 1
                    if et == "event_virus_consumed":
                        vx, vy = e.virus_pos
                        import math
                        if math.hypot(vx - st.me.x, vy - st.me.y) > st.vision_size:
                            far_virus_events += 1
                    if et == "event_player_eaten":
                        eaten_events += 1
                print(f"PROBE r{st.round} rankings={st.rankings} evtypes={seen} "
                      f"far_virus={far_virus_events} eaten_seen={eaten_events}", file=sys.stderr)
            game.send_move(MovePlayer(player_id=st.me.player_id,
                                      direction=DirectionModel(x=30.0 - st.me.x, y=30.0 - st.me.y),
                                      split=False))
        else:
            raise RuntimeError(str(type(q)))

if __name__ == "__main__":
    main()
