import threading
from typing import Annotated

from annotated_types import Len
from fastapi import FastAPI
from fastapi.responses import Response

from datetime import datetime
import pickle

from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse


GAME_IS_RUNNING = False

print(f"starting server at {datetime.now()}")

# create fastapi entry point
app = FastAPI()


@app.get("/")
async def root():
    return {"message": f"Hello World. This is the beginning of the apocalypse. all hail the new epoch of armageddonn!!"
                       "Say hello boyos.. 😈⚔️⚔️⚔️⚔️"}


# def start_game():
#     # create game play thread
#     global GAME_IS_RUNNING
#     if not GAME_IS_RUNNING:
#         x = threading.Thread(target=run_game_server, args=(data_feed_main,))
#         x.start()
#         GAME_IS_RUNNING = True

# @app.get("/get_mothership_position")
# async def get_mothership_position():
#     if not GAME_IS_RUNNING:
#         start_game()
#     else:
#         pass
#     return data_feed_main.position

@app.get("/home", response_class=HTMLResponse)
async def read_items():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma, no hands! </h1>
        </body>
    </html>
    """


# class RootClientData(BaseModel):
#     client_name: str = "root"
#     battleship_position: str | None = None
#     player_color: str
#
#     def __str__(self):
#         return f"{self.client_name} is at position {self.battleship_position}"



# all_clients = {}
#
#
# @app.post("/data")
# async def create_item(client_data: ClientData):
#     client_name, battleship_position = client_data.client_name, client_data.battleship_position
#
#     if client_name not in all_clients:
#         print(f"client {client_name} has joined the game!\nCurrent players {all_clients}")
#     all_clients[client_name] = client_data
#     # print(f"data sent by client {all_clients}")
#
# @app.get("/get_data")
# async def root():
#     return {"all_clients_data": all_clients}
#










from game import *


data_interface = ServerDataInterface()
objects_interface = data_interface.world_to_players_interface
players_interface = data_interface.world_to_players_interface


@app.get("/enter")
async def create_player(player_name: str):
    operation_status = players_interface.add_player_by_name(player_name)
    if operation_status:
        print(f"Player {player_name} has joined the game!\n")
        return {"player_data": f"successfully joined the game!"}
    return {"player_data": f"player name already exists. please choose a new name."}



@app.get("/exit")
async def player_exit(player_name: str):
    operation_status = players_interface.remove_player_by_name(player_name)
    if operation_status:
        print(f"Player {player_name} has left the game!\n")
        return "successfully exited from the game"
    return "player does not exist."


# normal client requests starts here

class NormalClientData(BaseModel):
    client_name: str
    battleship_position: list[int] | None = Field(default=None, min_length=2, max_length=2)
    player_color: str

    def __str__(self):
        return f"{self.client_name} is at position {self.battleship_position}"


@app.post("/send_data")
async def process_data_from_client(client_data: NormalClientData):
    # for now client sends safe data and not pickled objects for server security
    client_name, battleship_position, color = client_data.client_name, client_data.battleship_position, client_data.player_color
    operation_status = players_interface.update_player(client_name, {"battleship position": battleship_position,
                                                                     "color": color})
    if operation_status:
        print(operation_status)
        return "successfully sent player data"
    else:
        return "player does not exist. please create a new player"


@app.get("/get_my_data")
async def get_normal_client_self_data(player_name: str):
    player_object = players_interface.get_player_by_name(player_name)
    if player_object is not None:
        player_object_bytes = pickle.dumps(player_object)
        return Response(content=player_object_bytes, media_type="application/octet-stream")
    else:
        return "player does not exist. please create a new player"


@app.get("/get_world_data")
async def get_normal_client_world_data(player_name: str):
    all_players = players_interface.get_all_players()

    opponent_player_data = {}
    # return only opponent player positions and colors
    for p_o in all_players:
        opponent_name = p_o.name
        if opponent_name != player_name:
            opponent_player_data[opponent_name] = {"name": opponent_name,
                                                   "battleship_position": p_o.world_battleship.position,
                                                   "color": p_o.color}
    return {"opponent_player_data": opponent_player_data}

