import time
import pickle
import pygame
import requests
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

    # load client config details
    client_name, player_color = client_config_data["client_name"], client_config_data["player_color"]
    print(f"Kicking off client script. Welcome {client_name}!")


    # 1. request server to enter the game
    # server creates a new player with given name
    path_v = f"enter?player_name={client_name}"
    response_v = client_2_server_interface.get_request(path_v)
    if not response_v:
        raise requests.exceptions.ConnectionError('Cannot connect to server. Server may be down.')
    print("You have entered the game.")


    # 2. get newly created player object from the server
    path_v = f"get_my_data?player_name={client_name}"
    player_as_bytes = client_2_server_interface.get_request(path_v).content
    player_as_object = pickle.loads(player_as_bytes)
    print("Player data has been fetched from the server.")


    # 3. now with the data pulled from server, load it into the game engine
    # then run the game, periodically communicating with the server for updates
    def run_game():
        # create time handler
        class TimeHandler:
            def __init__(self):
                self.server_contact_interval = 0.2
                self.time_handler = {"contact_server_interval": [time.time(), self.server_contact_interval],
                                     "battleship_rotate_interval": [time.time(), 0.1],
                                     "battleship_velocity_change_interval": [time.time(), 0.1],
                                     "help_screen_display_interval": [time.time(), 0.4]
                                     }

            def check_for_time_constraint(self, event_key):
                last_activated_time, minimum_wait_duration = tuple(self.time_handler[event_key])
                if time.time() - last_activated_time > minimum_wait_duration:
                    self.time_handler[event_key][0] = time.time()
                    return True
                return False

        # use this to make the world_battleship respond to user events
        def world_battleship_event_handler(world_battleship: WorldBattleship, key_pressed_dict_p,
                                           time_handle: TimeHandler):

            velocity_change = 0.3
            angle_increment = 8

            if key_pressed_dict_p[pygame.K_UP]:
                if time_handle.check_for_time_constraint("battleship_velocity_change_interval"):
                    current_velocity = world_battleship.get_velocity()
                    world_battleship.set_velocity(current_velocity + velocity_change)
            elif key_pressed_dict_p[pygame.K_DOWN]:
                if time_handle.check_for_time_constraint("battleship_velocity_change_interval"):
                    current_velocity = world_battleship.get_velocity()
                    world_battleship.set_velocity(current_velocity - velocity_change)

            elif key_pressed_dict_p[pygame.K_RIGHT]:
                if time_handle.check_for_time_constraint("battleship_rotate_interval"):
                    world_battleship.rotate_yourself(-angle_increment)
            elif key_pressed_dict_p[pygame.K_LEFT]:
                if time_handle.check_for_time_constraint("battleship_rotate_interval"):
                    world_battleship.rotate_yourself(angle_increment)

            # battleship shoots bullet if space is pressed
            if key_pressed_dict_p[pygame.K_SPACE]:
                world_battleship.shoot_bullet()

        pygame.init()

        SCREEN_WIDTH, SCREEN_HEIGHT = (600, 400)
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"{client_name} 🍍🍍🍍")
        font = pygame.font.Font('freesansbold.ttf', 10)


        # game settings
        display_help_screen = False

        # create a time_handler
        time_handler = TimeHandler()

        # create a help screen
        def create_help_screen_surface():
            help_screen_surface = pygame.surface.Surface((SCREEN_WIDTH * 0.6, SCREEN_HEIGHT * 0.6))
            help_screen_surface.fill("white")

            help_text = ("welcome to the help menu:[n]"
                         "press up/down keys to increase/decrease speed.[n]"
                         "press left/right keys to rotate battleship[n]")
            help_text_list = help_text.split("[n]")
            help_text_start_position = [10, 20]
            offset = [0, 10]
            for index, line in enumerate(help_text_list):
                f_obj = font.render(line, True, "black")

                line_position = [help_text_start_position[0] + (index * offset[0]),
                                 help_text_start_position[1] + (index * offset[1])]
                help_screen_surface.blit(f_obj, line_position)

            return help_screen_surface
        help_screen = create_help_screen_surface()

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

            # respond to user events
            keys_pressed_dict = pygame.key.get_pressed()
            world_battleship_event_handler(battleship_o, keys_pressed_dict, time_handler)

            # if ESC key pressed toggle help screen display
            if keys_pressed_dict[pygame.K_ESCAPE]:
                if time_handler.check_for_time_constraint("help_screen_display_interval"):
                    display_help_screen = not display_help_screen

            # update the battleship state
            battleship_o.update()

            # <-------- this starts the data communication with server for updates section-------->

            # logic to update data cache and periodically send updated player data to server (ever 2 second)
            # also receive other player (opponents) and world data
            # todo: limit the rate of this time check. it runs at 30 fps and is a waste
            if time_handler.check_for_time_constraint("contact_server_interval"):
                # periodically send updated player data to the server
                updated_player_data_to_sent = {
                    "client_name": client_name,
                    "battleship_position": battleship_o.position,
                    "player_color": player_color,
                    "battleship_angle": battleship_o.angle,
                    "battleship_velocity_magnitude": battleship_o.get_velocity()
                }
                path_val = f"send_data?player_name={client_name}"
                client_2_server_interface.post_request(path_val, updated_player_data_to_sent)

                # periodically request server for updated world data
                path_val = f"get_world_data?player_name={client_name}"
                world_data = client_2_server_interface.get_request(path_val).json()
                # print("this is the opponent data pulled by server", world_data)
                client_data_cache.world_data = world_data


            # <-------- this starts the display section v-------->

            # display opponents in the world
            if client_data_cache.world_data is not None:
                opponents_data = client_data_cache.world_data["opponent_player_data"]
                for opponent_name, data_v in opponents_data.items():
                    opp_player_name, opp_player_position, opp_player_color = (data_v["name"], data_v["battleship_position"],
                                                                              data_v["color"])
                    pygame.draw.circle(screen, opp_player_color, opp_player_position, 5)

                    my_name = font.render(opp_player_name, True, "red")
                    text_position = [opp_player_position[0] + 10, opp_player_position[1] - 20]
                    screen.blit(my_name, text_position)

            # display the player in the world
            my_battleship_position = battleship_o.position
            pygame.draw.circle(screen, player_color, my_battleship_position, 5)
            my_name = font.render(client_name, True, "white")
            text_position = [my_battleship_position[0] + 10, my_battleship_position[1] - 20]
            screen.blit(my_name, text_position)

            # display player velocity indicator
            starting_node = my_battleship_position
            scaling_factor = 20
            velocity_vector = battleship_o.get_velocity_components()
            velocity_vector_scaled = [i * scaling_factor for i in velocity_vector]
            ending_node = [starting_node[0] + velocity_vector_scaled[0], starting_node[1] + velocity_vector_scaled[1]]
            pygame.draw.line(screen, "white", starting_node, ending_node)


            # display help screen is enabled
            if display_help_screen:
                screen.blit(help_screen, [20, 20])


            pygame.display.flip()
            screen.fill("black")
            clock.tick(30)

        # request server to exit the game
        path_val = f"exit?player_name={client_name}"
        client_2_server_interface.get_request(path_val)
        print("Leaving the game run.")

        pygame.quit()

    print("Starting the game run.")
    run_game()


if __name__ == "__main__":
    print(f"\n{'#' * 30}\n\nSTART OF CLIENT GAMEPLAY\n\n{'#' * 30}\n")

    # parse the command line arguments
    parser = argparse.ArgumentParser(description="Run the client game",)
    # parser.add_argument("-n", "--name", help="Player Name")
    parser.add_argument("player_name")
    parser.add_argument("player_color")

    args = parser.parse_args()

    # create an internal config for client settings
    client_config_data_v = {"client_name": args.player_name, "player_color": args.player_color}

    # create client to server interface
    client_2_server_interface_v = Client2ServerInterface()

    # create client data cache
    client_data_cache_v = DataCache()

    # run game with player object
    run_game_client(client_config_data_v, client_2_server_interface_v, client_data_cache_v)

    print(f"\n{'#' * 30}\n\nEND OF CLIENT GAMEPLAY\n\n{'#' * 30}\n")
