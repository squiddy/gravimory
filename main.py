import enum
import random
import pyxel
import pyxel_utils
from dataclasses import dataclass, field

pyxel.init(300, 340)
pyxel.load("main.pyxres")

player_x = 0
player_y = -1


@enum.unique
class Sprite(enum.Enum):
    COYOTE = (0, 96, 64, 32, 48 + 1, 0)
    PLATE = (0, 96, 16, 32, 16, 0)
    CLOUD_5 = (0, 64, 0, 32, 16, 0)
    CLOUD_4 = (0, 64, 16, 32, 16, 0)
    CLOUD_3 = (0, 64, 32, 32, 16, 0)
    CLOUD_2 = (0, 64, 48, 32, 16, 0)
    CLOUD_1 = (0, 96, 48, 32, 16, 0)


@dataclass
class Tile:
    @enum.unique
    class State(enum.Enum):
        HIDDEN = 0
        PLATE = 1
        DISSOLVING = 2

    grid: "Grid"
    x: int = 0
    y: int = 0
    state = State.HIDDEN
    is_walkable: bool = False
    frame = 0

    def update(self):
        if self.state == self.State.DISSOLVING:
            self.frame += 1
            if self.frame >= 25:
                self.state = self.State.PLATE

    def draw(self):
        x, y = self.grid.get_xy_for_tile(self.x, self.y)

        if self.state == self.State.HIDDEN:
            sprite = Sprite.CLOUD_5
            pyxel_utils.blt_topleft(x, y, *Sprite.CLOUD_5.value)
            return

        if self.state == self.State.DISSOLVING:
            sprite = [
                Sprite.CLOUD_5,
                Sprite.CLOUD_4,
                Sprite.CLOUD_3,
                Sprite.CLOUD_2,
                Sprite.CLOUD_1,
            ][self.frame // 5]
            if self.is_walkable:
                pyxel_utils.blt_topleft(x, y, *Sprite.PLATE.value)
            pyxel_utils.blt_topleft(x, y, *sprite.value)
            return

        if self.is_walkable:
            pyxel_utils.blt_topleft(x, y, *Sprite.PLATE.value)


@dataclass
class Grid:
    tiles: list[Tile] = field(default_factory=list, init=False)
    width: int = 0
    height: int = 0
    x: int = field(default=0, init=False)

    def __post_init__(self):
        for y in range(self.height):
            for x in range(self.width):
                self.tiles.append(Tile(self, x, y, random.choice([True, False])))

        self.x = (pyxel.width - self.width * 32) // 2

    def update(self):
        for tile in self.tiles:
            tile.update()
            if player_x == tile.x and player_y == tile.y:
                if tile.state == Tile.State.HIDDEN:
                    tile.state = Tile.State.DISSOLVING

    def draw(self):
        for tile in self.tiles:
            tile.draw()

    def get_xy_for_tile(self, x, y):
        return (x * 32 + self.x, y * 16 + 60)


@enum.unique
class GameState(enum.Enum):
    TITLE = 0
    PLAYING = 1


game_state = GameState.PLAYING
grid = Grid(7, 11)


def update_playing_scene():
    global player_x, player_y

    if pyxel.btnp(pyxel.KEY_LEFT):
        player_x -= 1
        player_x = max(0, player_x)
    elif pyxel.btnp(pyxel.KEY_RIGHT):
        player_x += 1
        player_x = min(grid.width - 1, player_x)
    elif pyxel.btnp(pyxel.KEY_UP) and player_y >= 0:
        player_y -= 1
        player_y = max(0, player_y)
    elif pyxel.btnp(pyxel.KEY_DOWN):
        player_y += 1
        player_y = min(grid.height - 1, player_y)

    grid.update()


def draw_playing_scene():
    pyxel.rect(0, 0, 300, 55, 9)
    pyxel.rect(0, 250, 300, pyxel.height - 200, 9)
    grid.draw()

    player_height = Sprite.COYOTE.value[4]
    x, y = grid.get_xy_for_tile(player_x, player_y)
    pyxel_utils.blt_topleft(x, y - player_height + 10, *Sprite.COYOTE.value)


def update_title_scene():
    pass


def draw_title_scene():
    pyxel_utils.blt_topleft(160, 160, *Sprite.CLOUD_2.value, scale=5)
    pyxel_utils.blt_topleft(-40, 200, *Sprite.CLOUD_5.value, scale=10)
    pyxel_utils.blt_topleft(50, 75, *Sprite.COYOTE.value, scale=4)


def update():
    match game_state:
        case GameState.TITLE:
            update_title_scene()
        case GameState.PLAYING:
            update_playing_scene()


def draw():
    pyxel.cls(12)

    match game_state:
        case GameState.TITLE:
            draw_title_scene()
        case GameState.PLAYING:
            draw_playing_scene()


pyxel.run(update, draw)
