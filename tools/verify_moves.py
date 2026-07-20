#!/usr/bin/env python3
"""EMERGENCY MOVE VERIFIER: replay a recorded game through the REAL bot binary
via the engine's own protocol; diff every reply against the recorded moves.
Usage: verify_moves.py <workspace_dir> <bot_file>"""
import json, os, stat, subprocess, sys, tempfile, time
from pathlib import Path

WS = Path(sys.argv[1]); BOT = Path(sys.argv[2]).resolve()
TMP = Path(tempfile.mkdtemp(prefix="verify_"))
(TMP/"input").mkdir(); (TMP/"submission0"/"io").mkdir(parents=True)
os.mkfifo(TMP/"submission0"/"io"/"to_engine.pipe")
os.mkfifo(TMP/"submission0"/"io"/"from_engine.pipe")
cat = json.load(open(WS/"input"/"catalog.json"))
json.dump(cat, open(TMP/"input"/"catalog.json","w"))
os.environ["GAME_ENGINE_CORE_DIRECTORY"] = str(TMP)

from engine.state.game_state import GameState
from engine.state.player_state import PlayerState
from engine.state.blob_state import BlobState
from engine.interface.io.input_validator import MoveValidator
from engine.interface.io.censor_event import CensorEvent
from lib.interact.map import Map
from lib.models.food_model import FoodModel
from lib.models.virus_model import VirusModel
from lib.interface.events.event_game_started import EventGameStarted
from lib.interface.events.event_player_moved import EventPlayerMoved
from lib.interface.events.event_player_eaten import EventPlayerEaten
from lib.interface.events.moves.move_player import MovePlayer

events = json.load(open(WS/"output"/"game.json"))
gs = object.__new__(GameState)
gs.catalog = cat
gs.round = 0
gs.players = {i: PlayerState(i, cat[i]["team_id"]) for i in range(8)}
gs.map = object.__new__(Map)
gs.map.foods = []; gs.map.viruses = []
gs.event_history = []; gs.private_event_history = []
gs.turn_order = []

started = next(e for e in events if e.get("event_type")=="event_game_started")
gs.turn_order = started["turn_order"]
gs.max_rounds = started["max_rounds"]
gs.map.size = started["arena_size"]
for p in started["players"]:
    ps = gs.players[p["player_id"]]
    ps.blobs = {b["blob_id"]: BlobState(b["blob_id"], b["pos"][0], b["pos"][1], b["radius"], b.get("merge_cooldown",0)) for b in p["blobs"]}
gs.event_history.append(EventGameStarted.model_validate(started))

# spawn the REAL bot
venv_py = "/Users/chrisli/Developer/competition/evolution-2/.venv/bin/python"
botlog = open(TMP/"bot.log","w")
proc = subprocess.Popen([venv_py, str(BOT)], cwd=TMP/"submission0", stdout=botlog, stderr=botlog)
gs.players[0].connect()
conn = gs.players[0].connection
validator = MoveValidator(gs); censor = CensorEvent(gs)

foods = {}; viruses = {}
def sync_map():
    gs.map.foods = list(foods.values()); gs.map.viruses = list(viruses.values())

checked = mismatches = 0
first_mm = None
i = 0; n = len(events)
while i < n:
    e = events[i]
    et = e.get("event_type")
    if et == "move_player":
        # round boundary: collect the contiguous move block
        block = []
        while i < n and events[i].get("event_type") == "move_player":
            block.append(events[i]); i += 1
        gs.round += 1
        rec0 = next((m for m in block if m["player_id"]==0), None)
        if rec0 is not None:
            sync_map()
            reply = conn.query_move_player(gs, validator, censor)
            rd, pd = reply.direction, rec0["direction"]
            ok = (reply.split == rec0["split"]
                  and abs((rd.x or 0)-(pd["x"] or 0)) < 1e-9
                  and abs((rd.y or 0)-(pd["y"] or 0)) < 1e-9)
            checked += 1
            if not ok:
                mismatches += 1
                if first_mm is None:
                    first_mm = (gs.round, (rd.x, rd.y, reply.split), (pd["x"], pd["y"], rec0["split"]))
        for m in block:
            gs.event_history.append(MovePlayer.model_validate(m))
        continue
    if et == "event_food_spawned":
        for f in e["foods"]: foods[f["food_id"]] = FoodModel.model_validate(f)
    elif et == "event_food_eaten":
        for fid in e["food_ids"]: foods.pop(fid, None)
    elif et == "event_virus_spawned":
        for v in e["viruses"]: viruses[v["virus_id"]] = VirusModel.model_validate(v)
    elif et == "event_virus_consumed":
        viruses.pop(e["virus_id"], None)
    elif et == "event_player_eaten":
        gs.event_history.append(EventPlayerEaten.model_validate(e))
    elif et == "event_player_moved":
        ps = gs.players[e["player_id"]]
        ps.blobs = ({b["blob_id"]: BlobState(b["blob_id"], b["pos"][0], b["pos"][1], b["radius"], b.get("merge_cooldown",0)) for b in e["blobs"]}
                    if e["alive"] else {})
        gs.event_history.append(EventPlayerMoved.model_validate(e))
    i += 1

proc.kill()
print(f"{WS.name}: rounds checked {checked} | MISMATCHES {mismatches}")
if first_mm:
    r,(ax,ay,asp),(bx,by,bsp) = first_mm
    print(f"  first mismatch at round {r}:")
    print(f"    replayed: ({ax}, {ay}) split={asp}")
    print(f"    recorded: ({bx}, {by}) split={bsp}")
