"""T1-mimic: Washed CS (team_id 1) — the #2 apex. REBUILT 2026-07-09 to SPLIT.

The prior build was split=False -- WRONG. Recent raw replays (matches 1719-1724,
elite_g30_replays_1449_1724.zip) show Washed-CS (team 1) SPLITS ~24.8 moves/match
(even more than Team-15's 14.5) and hunts ~39 kills/match -- a heavy split-hunter.
A non-splitting mimic misrepresents the #2 in the room; this rebuild adds the
split cycle so the gym prices real Washed-CS pressure.

Recent-era profile (team 1, matches 1719-1724, n=6 co-lobbies):
  - splits ~24.8/match, kills ~39/match (heaviest hunter in the field)
  - cons ~14.8/match (feeds the hunt more than the virus economy)
  - avg mass ~42.7, win rate ~20% (2nd only to Team-15's 56.7 / 50%)

Prior 837-era note (still the feast signature): ~17 cons, feast ~44 (52% at 40+),
grows to ~43 mass. Hermes's block claimed 48-mass/100%-win; raw events showed
43-mass/56% -- built to the VERIFIED behavior, never the inflated headline.

Doctrine: split aggressively to spread the hunt, chase prey relentlessly (~39
kills), feast viruses between kills. Dumb on purpose -- tuned to BE Washed-CS.
Engine: agario-kit 2026.1.12 (MASS-rule eat: eater.mass >= target.mass * 1.2).
"""

import math

from helper.game import Game
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.queries.query_move import QueryMovePlayer
from lib.models.penguin_model import DirectionModel

EAT = 1.2            # .12 MASS eat ratio (mass, not radius)
FEAST_GATE = 20.0    # feast once moderately big -> consumptions center 40+ as it grows
FLEE_DIST = 3.5      # brave: stays in the fray to feast/hunt
VIRUS_RANGE = 26.0   # crosses the arena for a virus
PREY_DIST = 16.0     # heavy hunter (~39 kills/match)
VIRUS_BIAS = 1.5     # prefer a virus unless a prey is much closer
# --- SPLIT CYCLE (raw-decoded from Washed-CS/team1, matches 1719-1724) ---
SPLIT_GATE = 5.0     # low gate -> splits readily (~24.8/match, heaviest in field)
SPLIT_CLEAR = 3.0    # brave: split even with a threat just outside flee range


def mass(r: float) -> float:
    return r * r


def main() -> None:
    game = Game()
    while True:
        query = game.get_next_query()
        match query:
            case QueryMovePlayer():
                st = game.state
                me = st.me
                my_blobs = list(me.blobs.values())
                largest = max((b.radius for b in my_blobs), default=me.radius)
                lm = mass(largest)
                total_mass = sum(mass(b.radius) for b in my_blobs) if my_blobs else lm

                # nearest lethal threat (MASS rule: enemy eats me if enemy.mass >= my.mass * EAT)
                threat, td = None, 1e9
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if mass(b.radius) >= lm * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < td:
                            threat, td = b, d
                # nearest virus
                nv, nvd = None, 1e9
                for v in st.visible_viruses:
                    d = math.hypot(v.pos[0] - me.x, v.pos[1] - me.y)
                    if d < nvd:
                        nv, nvd = v, d
                # nearest edible prey (MASS rule: I eat if my.mass >= prey.mass * EAT)
                prey, pd = None, PREY_DIST
                for b in st.visible_blobs:
                    if b.player_id == me.player_id:
                        continue
                    if lm >= mass(b.radius) * EAT:
                        d = math.hypot(b.pos[0] - me.x, b.pos[1] - me.y)
                        if d < pd:
                            prey, pd = b, d

                virus_ok = total_mass >= FEAST_GATE and nv is not None and nvd <= VIRUS_RANGE
                dx, dy = 0.0, 0.0
                chasing = False  # True when moving toward a virus or prey (split-worthy)
                # 1. flee only a very close lethal blob
                if threat is not None and td < FLEE_DIST:
                    dx, dy = me.x - threat.pos[0], me.y - threat.pos[1]
                # 2. APEX FEAST vs HUNT: prefer the virus unless a prey is much closer
                elif virus_ok and (prey is None or nvd <= pd * VIRUS_BIAS):
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                    chasing = True
                elif prey is not None:
                    dx, dy = prey.pos[0] - me.x, prey.pos[1] - me.y
                    chasing = True
                elif virus_ok:
                    dx, dy = nv.pos[0] - me.x, nv.pos[1] - me.y
                    chasing = True
                # 3. forage
                elif st.visible_food:
                    f = min(st.visible_food,
                            key=lambda f: (f.pos[0] - me.x) ** 2 + (f.pos[1] - me.y) ** 2)
                    dx, dy = f.pos[0] - me.x, f.pos[1] - me.y
                else:
                    dx, dy = 30.0 - me.x, 30.0 - me.y

                if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                    dx = 1.0

                # SPLIT CYCLE: split toward a virus/prey when big enough, safe, room
                # remains -> spreads the hunt (Washed-CS is the heaviest splitter, ~24.8).
                split = (chasing
                         and total_mass >= SPLIT_GATE
                         and len(my_blobs) < 16
                         and mass(largest) >= 4.0
                         and (threat is None or td >= SPLIT_CLEAR))

                game.send_move(MovePlayer(
                    player_id=me.player_id,
                    direction=DirectionModel(x=dx, y=dy),
                    split=split,
                ))
            case _:
                raise RuntimeError(f"Unsupported query: {type(query)}")


if __name__ == "__main__":
    main()
