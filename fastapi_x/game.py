import time
import pygame

class Battleship:

    def __init__(self):
        self.position = [40, 40]

    def event_handler(self, key_pressed_dict_p):
        current_x, current_y = tuple(self.position)
        displacement = 3
        if key_pressed_dict_p[pygame.K_UP]:
            self.position = [current_x, current_y - displacement]
        elif key_pressed_dict_p[pygame.K_DOWN]:
            self.position = [current_x, current_y + displacement]
        elif key_pressed_dict_p[pygame.K_RIGHT]:
            self.position = [current_x + displacement, current_y]
        elif key_pressed_dict_p[pygame.K_LEFT]:
            self.position = [current_x - displacement, current_y]

    def update(self, key_pressed_dict_p):
        self.event_handler(key_pressed_dict_p)


def run_game_server(data_feed_to_main):
    print("starting server game thread...")
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = (600, 400)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mothership ⚔️⚔️⚔️")
    font = pygame.font.Font('freesansbold.ttf', 32)

    def write_text_at_position(display_surface, text_to_write, position):

        # create a text surface object, on which text is drawn on it.
        text = font.render(text_to_write, True, "white")

        display_surface.blit(text, position)

    # initialize server battleship
    battleship_1 = Battleship()

    clock = pygame.time.Clock()
    game_over = False
    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                break

        # if game mode is server take input from user and update battleship position
        # server responds to user event and updates battleship
        keys_pressed_dict = pygame.key.get_pressed()
        battleship_1.update(keys_pressed_dict)
        pygame.draw.circle(screen, "red", battleship_1.position, 5)

        # drop a letter at battleship position
        if keys_pressed_dict[pygame.K_a]:
            write_text_at_position(screen, "a", battleship_1.position)

        # update data feed in mothership
        data_feed_to_main.position = battleship_1.position

        pygame.display.flip()
        screen.fill("black")
        clock.tick(30)

    pygame.quit()


def run_game_client(data_feed, update_datafeed_with_server_data_function):
    print("starting client game thread...")
    pygame.init()

    SCREEN_WIDTH, SCREEN_HEIGHT = (600, 400)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Client Vassal 🍍🍍🍍")

    # initialize client battleship
    battleship_1 = Battleship()

    # create time handler
    time_handler = {"get position": [time.time(), 0.5]}
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

        # logic to update datafeed with fresh server data, ever 2 second
        if check_for_time_constraint("get position"):
            update_datafeed_with_server_data_function(data_feed)

        # client update battleship from server data feed
        battleship_1.position = data_feed.position

        # draw the battleship
        pygame.draw.circle(screen, "red", battleship_1.position, 5)


        pygame.display.flip()
        screen.fill("black")
        clock.tick(30)

    pygame.quit()



if __name__ == "__main__":

    class DataFeed:
        def __init__(self):
            self.position = None
    data_feed_test = DataFeed()
    run_game_server(data_feed_test)



