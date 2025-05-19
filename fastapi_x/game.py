import math
import time
import pygame



#############################################################################

# this starts the implementation of game objects

#############################################################################

class ObjectBase:
    pass


class Bullet:
    def __init__(self, velocity=None):
        self.activated = False
        self.position = None
        if velocity is None:
            self.velocity = [0.5, 0.5]

    def set_position(self, position):
        self.position = position

    def activate_bullet(self):
        self.activated = True

    def move(self):
        x, y = tuple(self.position)
        dx, dy = tuple(self.velocity)
        self.position = [x + dx, y + dy]

    def update(self):
        if self.activated:
            self.move()

    def __str__(self):
        return "bullet"

class Battleship:

    def __init__(self):
        self.position = [40, 40]
        self.bullets = Battleship.initialize()

        self.angle = 0
        self._natural_deceleration = 0.00
        self._max_velocity_magnitude = 3
        self._velocity_magnitude = 0.6
        self._velocity_components = self.compute_velocity_components(self.angle, self._velocity_magnitude)


    @staticmethod
    def compute_velocity_components(angle, velocity_magnitude):
        x, y = (velocity_magnitude * math.cos(math.radians(angle)),
                velocity_magnitude * math.sin(math.radians(angle)))
        x, y = round(x, 2), round(y, 2)
        return [x, y]


    def set_velocity(self, new_velocity):
        if abs(new_velocity) <= self._max_velocity_magnitude:
            self._velocity_magnitude = round(new_velocity, 2)

            # when velocity_magnitude is updated, it should automatically update velocity components
            x, y = self.compute_velocity_components(self.angle, new_velocity)
            self._velocity_components = [x, y]

    def get_velocity(self):
        return self._velocity_magnitude

    def get_velocity_components(self):
        return self._velocity_components

    def get_angle(self):
        return self.angle

    @staticmethod
    def initialize():
        # give the battleship 10 bullets
        number_of_bullets = 10
        bullet_list = [Bullet() for _ in range(number_of_bullets)]
        return bullet_list


    def rotate_yourself(self, angle_to_rotate_by):
        new_angle = self.angle  + angle_to_rotate_by
        new_angle = round(new_angle % 360, 2)
        self.angle = new_angle

        # update velocity components to face the new angle. velocity magnitude remains the same
        self._velocity_components = self.compute_velocity_components(new_angle, self._velocity_magnitude)


    def move(self):
        # slow down the player naturally
        self.set_velocity(abs(self._velocity_magnitude) - self._natural_deceleration)

        x, y = tuple(self.position)
        dx, dy = tuple(self._velocity_components)
        self.position = [x + dx, y + dy]


    def shoot_bullet(self):
        # take a bullet out
        bullet_to_shoot = self.bullets.pop()

        # assign it bullet position which is battleship position. activate it
        bullet_to_shoot.set_position(self.position)
        bullet_to_shoot.activate_bullet()

        return bullet_to_shoot


    def update(self):
        self.move()


    def __str__(self):
        return "battleship"


#############################################################################

# this starts the world implementation of game objects

#############################################################################

class WorldToObjectsInterface:

    def __init__(self):
        self.objects_list = []

    def get_objects(self):
        return self.objects_list

    def add_game_object(self, object_to_add):
        if object_to_add not in self.objects_list:
            self.objects_list.append(object_to_add)
            print(f"Adding object to world: {object_to_add}.\n\t{self}")

    def remove_game_object(self, object_to_remove):
        if object_to_remove in self.objects_list:
            self.objects_list.remove(object_to_remove)
            print(f"Removing object from world: {object_to_remove}.\n\t{self}")

    def __str__(self):
        str_v = "[" + ", ".join([str(p) for p in self.objects_list]) + "]"
        return f"List of objects: {str_v}"


class WorldBullet(Bullet):
    def __init__(self, world_interface: WorldToObjectsInterface, velocity=None):
        super().__init__(velocity=velocity)
        self.world_interface = world_interface
        self.world_interface.add_game_object(self)

    def __del__(self):
        self.world_interface.remove_game_object(self)


class WorldBattleship(Battleship):
    def __init__(self, world_interface: WorldToObjectsInterface):
        super().__init__()
        self.world_interface = world_interface
        self.world_interface.add_game_object(self)

    def shoot_bullet(self):
        # when bullet is shot in world, it runs battleship shoot code then adds bullet object to game objects list
        bullet_to_shoot = super().shoot_bullet()
        self.world_interface.add_game_object(bullet_to_shoot)
        return bullet_to_shoot

    def __del__(self):
        self.world_interface.remove_game_object(self)


#############################################################################

# this starts the client wrapper for objects

#############################################################################

class Player:
    def __init__(self, name: str,
                 world_to_objects_interface: WorldToObjectsInterface,
                 world_to_players_interface):

        # link the external data feeds
        self.world_to_objects_interface = world_to_objects_interface
        self.world_to_players_interface = world_to_players_interface

        # assign the default player attributes
        self.name : str = name
        self.world_battleship: WorldBattleship | None = None

        # initialize the attributes
        self.initialize()

        # graphics attributes
        self.color = "red"

    def initialize(self):
        world_to_objects_interface = self.world_to_objects_interface
        world_to_players_interface = self.world_to_players_interface

        # create a battleship object
        self.world_battleship = WorldBattleship(world_to_objects_interface)

        # add player to players list
        world_to_players_interface.players_list.append(self)

    def get_player_objects(self):
        return [self.world_battleship]

    def __del__(self):
        world_to_players_interface = self.world_to_players_interface

        # remove player object reference

        # prevent multiple del calls
        if self in world_to_players_interface.players_list:
            world_to_players_interface.players_list.remove(self)

            # when a player is deleted all its child objects should be deleted as well
            for player_object_o in self.get_player_objects():
                player_object_o.__del__()

    def __str__(self):
        return self.name


class WorldToPlayersInterface:
    def __init__(self, world_to_objects_interface: WorldToObjectsInterface):
        self.players_list: list[Player] = []
        self.world_to_objects_interface = world_to_objects_interface

    def get_all_players(self):
        return self.players_list

    def get_player_by_name(self, player_name):
        for player_o in self.players_list:
            if player_o.name == player_name:
                return player_o

    def create_player(self,  player_name: str):
        # check if player already exists. if so do not create a new one
        op_check = self.get_player_by_name(player_name)
        if op_check is None:
            player_o = Player(player_name, self.world_to_objects_interface, self)
            return player_o
        return None

    def add_player_by_name(self,  player_name: str):
        # create a player object
        player_o = self.create_player(player_name)
        if player_o is not None:
            print(f"Adding player to game: {player_o}.\n\t{self}")
            return 1
        else:
            print(f"Player with name {player_name} already exists.")
            return 0

    def remove_player_by_name(self, player_name: str):
        # get the player object by name
        player_to_remove: Player = self.get_player_by_name(player_name)
        if player_to_remove in self.players_list:
            player_to_remove.__del__()
            print(f"Removing player from game: {player_name}.\n\t{self}")
            return 1
        return 0

    def update_player(self, player_name, updated_player_data):
        player_to_update = self.get_player_by_name(player_name)

        if player_to_update is not None:
            # update the battleship position
            player_to_update.world_battleship.position = updated_player_data["battleship position"]
            player_to_update.color = updated_player_data["color"]
            player_to_update.world_battleship.angle = updated_player_data["battleship_angle"]
            player_to_update.world_battleship.set_velocity(updated_player_data["battleship_velocity_magnitude"])
            return 1
        return 0


    def __str__(self):
        str_v = "[" +  ", ".join([str(p) for p in self.players_list]) + "]"
        return f"List of players: {str_v}"


#############################################################################

# this starts the main server world

#############################################################################


class ServerDataInterface:
    def __init__(self):

        self.world_to_objects_interface = WorldToObjectsInterface()
        self.world_to_players_interface = WorldToPlayersInterface(self.world_to_objects_interface)

    def get_player_object(self, player_name: str):
        return self.world_to_players_interface.get_player_by_name(player_name)

    def __str__(self):
        return f"{self.world_to_objects_interface} \n {self.world_to_players_interface}"


class ServerWorld:
    def __init__(self, server_data_interface: ServerDataInterface):
        # plug in external data interface
        self.server_data_interface = server_data_interface

    def initialize(self):
        server_data_interface = self.server_data_interface

        game_objects = []
        for game_object_x in game_objects:
            server_data_interface.world_to_objects_interface.add_game_object(game_object_x)


    def update(self):
        server_data_interface = self.server_data_interface

        # update all objects
        for world_object_o in server_data_interface.world_to_objects_interface.get_objects():
            world_object_o.update()

        # todo game mechanics goes here
        pass




#############################################################################

# use this for testing

#############################################################################


if __name__ == "__main__":
    print("[INFO] (TESTING) - Starting the server game run")

    # create data interface
    data_interface = ServerDataInterface()
    p_interface = data_interface.world_to_players_interface

    player_names = ["goggins", "toronaga", "maverick", "parashurama"]

    for p_name in player_names:
        p_interface.add_player_by_name(p_name)
        print("-"*40)

    p_interface.remove_player_by_name("maverick")

    # print(p_interface.get_all_players())
    # print(data_interface.world_to_objects_interface.get_objects())

    print(f"\n{'#'*30}\n\nEND OF PROGRAM\n\n{'#'*30}\n")

