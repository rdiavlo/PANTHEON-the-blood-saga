import threading
from fastapi import FastAPI
from datetime import datetime
from starlette.responses import HTMLResponse

from data_model import DataFeed
from game import run_game_server


GAME_IS_RUNNING = False

print(f"starting server at {datetime.now()}")
data_feed_main = DataFeed()


# create fastapi entry point
app = FastAPI()


@app.get("/")
async def root():
    return {"message": f"Hello World. This is the beginning of the apocalypse. all hail the new epoch of armageddonn!!"
                       "Say hello boyos.. 😈⚔️⚔️⚔️⚔️"}


def start_game():
    # create game play thread
    global GAME_IS_RUNNING
    if not GAME_IS_RUNNING:
        x = threading.Thread(target=run_game_server, args=(data_feed_main,))
        x.start()
        GAME_IS_RUNNING = True

@app.get("/get_mothership_position")
async def get_mothership_position():
    if not GAME_IS_RUNNING:
        start_game()
    else:
        pass
    return data_feed_main.position

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
