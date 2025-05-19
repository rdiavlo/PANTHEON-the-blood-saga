import pickle
import threading
from typing import Annotated
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse

from game import ServerDataInterface



print(f"Starting game server at {datetime.now()}!")

# create fastapi entry point
app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Gamia</title>
        </head>
        <body>
            <h1>Look ma, no hands!</h1>
            This is the beginning of the apocalypse. all hail the new epoch of armageddonn!!<br><br>
                       
            <h2>Gameplay storyline</h2><br>
            you wake up on an unknown terrain with an opponent in similar straits. your objective is to defeat the enemy. 
            <span style="color:red;"> there is no other path to your liberation.</span><br>
            good luck soldier, may the best man win!⚔️😈⚔️<br><br>
        </body>
    </html>
    """


# initialize the main game objects
data_interface = ServerDataInterface()
objects_interface = data_interface.world_to_players_interface
players_interface = data_interface.world_to_players_interface

# define server variables here
game_run_has_started = False


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
    battleship_position: list[float] | None = Field(default=None, min_length=2, max_length=2)
    player_color: str
    battleship_angle: float
    battleship_velocity_magnitude: float

    # def __str__(self):
    #     return f"{self.client_name} is at position {self.battleship_position}"



@app.post("/send_data")
async def process_data_from_client(client_data: NormalClientData, player_name: str):
    # for now client sends safe data and not pickled objects for server security
    # pickled objects can contain malicious cose [WARNING]
    operation_status = players_interface.update_player(client_data.client_name,
                                                       {"battleship position": client_data.battleship_position,
                                                         "color": client_data.player_color,
                                                         "battleship_angle": client_data.battleship_angle,
                                                         "battleship_velocity_magnitude": client_data.battleship_velocity_magnitude
                                                       })
    if operation_status:
        print(client_data)
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

