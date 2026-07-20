"""lunger: CURRICULUM PREDATOR for ARCH-1 (Chris-approved protocol, 2026-07-11).

Distills the mechanic behind 49% of our autopsied live deaths (526-event study):
chase the nearest split-killable player and SPLIT-FINISH when inside lunge reach
and aligned. Exists so anti-lunge architecture has a real fitness gradient —
the old room never lunged, so lunge defenses always decayed to zero.

Behaviour: eat food to grow; flee bigger players; chase blobs our split-half can
eat (mass >= 2.4x theirs); split when target center within 8.9*0.85 + half-radius
and we are moving toward it. No cycle, no feast — a pure lunge specialist.
Engine: agario-kit 2026.1.13 (.12 mass-space eat rule: eater.mass >= 1.2x target).
"""
import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

LUNGE_TRAVEL = 8.9          # engine: eject 1.6 / (1 - 0.82)
EAT_RATIO = 1.2


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                st = game.state
                me = st.me
                blobs = list(me.blobs.values())
                my_mass = sum(b.radius ** 2 for b in blobs) or me.radius ** 2
                largest_r = max((b.radius for b in blobs), default=me.radius)
                largest_m = largest_r ** 2
                dx, dy, split = 0.0, 0.0, False

                # 1) survival: flee any player who can eat our largest blob
                threat = None
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if b.radius ** 2 >= largest_m * EAT_RATIO:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < 14.0 and (threat is None or d < threat[1]):
                            threat = (b, d)
                if threat is not None:
                    dx, dy = me.x - threat[0].pos[0], me.y - threat[0].pos[1]
                elif my_mass < 15.0 and st.visible_food:
                    # 2a) bulk up first: a lunger under ~15 mass has no killable halves
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                else:
                    # 2b) hunt: nearest player blob our split-half can eat
                    prey = None
                    for b in st.visible_blobs:
                        if b.player_id == me.player_id:
                            continue
                        if largest_m / 2.0 >= (b.radius ** 2) * EAT_RATIO and largest_m / 2.0 >= 2.0:
                            d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                            if prey is None or d < prey[1]:
                                prey = (b, d)
                    if prey is not None:
                        b, d = prey
                        dx, dy = b.pos[0] - me.x, b.pos[1] - me.y
                        half_r = largest_r / math.sqrt(2)
                        if len(blobs) < 8 and d <= LUNGE_TRAVEL * 0.85 + half_r:
                            split = True
                    elif st.visible_food:
                        f = min(st.visible_food,
                                key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                        dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                    else:
                        dx, dy = 30.0 - me.x, 30.0 - me.y
                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0
                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=split,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
