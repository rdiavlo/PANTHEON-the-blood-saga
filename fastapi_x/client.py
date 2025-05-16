import requests
from game import run_game_client
from data_model import DataFeed


MOTHERSHIP_SERVER_URL = "http://127.0.0.1:8000/"

# create data feed object
data_feed_main = DataFeed()


def get_mothership_data():
    print("Contacting the mothership...")
    try:
        response = requests.get(MOTHERSHIP_SERVER_URL + "get_mothership_position")
        return response
    except requests.exceptions.ConnectionError:
        print("Connection down. Mothership may be unavailable.")
    return None

def get_mothership_fresh_position(data_feeder):
    mothership_position = get_mothership_data().json()
    data_feeder.position = mothership_position
    print(mothership_position)


run_game_client(data_feed_main, get_mothership_fresh_position)