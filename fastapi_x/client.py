import requests
import pickle
import time
import pygame

import argparse

from game import Player, WorldBattleship, WorldToObjectsInterface

class DataCache:

    def __init__(self):
        self.world_data = None

    def update_world_data(self, world_data):
        self.world_data = world_data

class Client2ServerInterface:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8000/"

    def get_request(self, path_p):
        server_url = self.server_url
        try:
            response = requests.get(server_url + path_p)
            return response
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server. Server may be down.")
            return 0

    def post_request(self, path_p, json_data):
        server_url = self.server_url
        try:
            response = requests.post(server_url + path_p, json=json_data)
            return response
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server. Server may be down.")
            return 0


def run_game_client(client_config_data, client_2_server_interface: Client2ServerInterface,
                    client_data_cache: DataCache):
    # use this to make the world_battleship respond to user events
    def world_battleship_event_handler(world_battleship: WorldBattleship, key_pressed_dict_p):

        current_x, current_y = tuple(world_battleship.position)
        displacement = 3
        if key_pressed_dict_p[pygame.K_UP]:
            world_battleship.position = [current_x, current_y - displacement]
        elif key_pressed_dict_p[pygame.K_DOWN]:
            world_battleship.position = [current_x, current_y + displacement]
        elif key_pressed_dict_p[pygame.K_RIGHT]:
            world_battleship.position = [current_x + displacement, current_y]
        elif key_pressed_dict_p[pygame.K_LEFT]:
            world_battleship.position = [current_x - displacement, current_y]

        # battleship shoots bullet if space is pressed
        if key_pressed_dict_p[pygame.K_SPACE]:
            world_battleship.shoot_bullet()


    # load client config details
    client_name, player_color = client_config_data["client_name"], client_config_data["player_color"]

    print(f"starting client script. Welcome {client_name}")

    # request server to enter the game
    # server creates a new player with given client_name
    path_v = f"enter?player_name={client_name}"
    response_v = client_2_server_interface.get_request(path_v)
    if not response_v:
        raise requests.exceptions.ConnectionError('Cannot connect to server. Server may be down.')
    print("You have entered the game..")


    # get player object and add to interface
    path_v = f"get_my_data?player_name={client_name}"
    player_as_bytes = client_2_server_interface.get_request(path_v).content
    player_as_object = pickle.loads(player_as_bytes)
    print(player_as_object)


    # now with the data pulled from server, load it into the game engine
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = (600, 400)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"{client_name} 🍍🍍🍍")
    # font = pygame.font.Font('freesansbold.ttf', 32)

    # create time handler
    SERVER_CONTACT_INTERVAL = 0.8
    time_handler = {"get_server_data": [time.time(), SERVER_CONTACT_INTERVAL]}
    def check_for_time_constraint(event_key):
        last_activated_time, minimum_wait_duration = tuple(time_handler[event_key])
        if time.time() - last_activated_time > minimum_wait_duration:
            time_handler[event_key][0] = time.time()
            return True
        return False

    clock = pygame.time.Clock()
    game_over = False
    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                break
        if game_over:
            break

        # get the world battleship
        battleship_o = player_as_object.world_battleship

        # todo if game mode is client take input from user and update battleship
        # then send updated battleship to server
        keys_pressed_dict = pygame.key.get_pressed()
        world_battleship_event_handler(battleship_o, keys_pressed_dict)
        pygame.draw.circle(screen, player_color, battleship_o.position, 5)


        # logic to update data cache and periodically send updated player data to server (ever 2 second)
        # also receive other player (opponents) and world data
        # todo: limit the rate of this time check. it runs at 30 fps and is a waste
        if check_for_time_constraint("get_server_data"):
            # send updated player data to the server
            updated_player_data_to_sent = {
                "client_name": client_name,
                "battleship_position": player_as_object.world_battleship.position,
                "player_color": player_color
            }
            path_v = f"send_data?player_name={client_name}"
            client_2_server_interface.post_request(path_v, updated_player_data_to_sent)

            # todo periodically request server for updated world data
            path_v = f"get_world_data?player_name={client_name}"
            world_data = client_2_server_interface.get_request(path_v).json()
            print(world_data)
            client_data_cache.world_data = world_data

        # display opponents in the world
        if client_data_cache.world_data is not None:
            opponents_data = client_data_cache.world_data["opponent_player_data"]
            for opponent_name, data_v in opponents_data.items():
                opp_player_name, opp_player_position, opp_player_color = (data_v["name"], data_v["battleship_position"],
                                                                          data_v["color"])
                pygame.draw.circle(screen, opp_player_color, opp_player_position, 5)

        pygame.display.flip()
        screen.fill("black")
        clock.tick(30)

    # request server to exit the game
    path_v = f"exit?player_name={client_name}"
    response_v = client_2_server_interface.get_request(path_v)
    print(response_v.text)
    print("You have left the game..")

    pygame.quit()


if __name__ == "__main__":

    # Initialize parser
    parser = argparse.ArgumentParser(description="Run the client game",)
    # parser.add_argument("-n", "--name", help="Player Name")
    parser.add_argument("player_name")
    parser.add_argument("player_color")

    args = parser.parse_args()

    # create a config for client settings
    client_config_data_v = {"client_name": args.player_name, "player_color": args.player_color}

    # create client to server interface
    client_2_server_interface_v = Client2ServerInterface()

    # create client data cache
    client_data_cache_v = DataCache()

    # run game with player object
    run_game_client(client_config_data_v, client_2_server_interface_v, client_data_cache_v)

    print(f"\n{'#' * 30}\n\nEND OF CLIENT GAMEPLAY\n\n{'#' * 30}\n")
