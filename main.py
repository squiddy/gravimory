import enum
import pyxel
import pyxel_utils
from dataclasses import dataclass, field

pyxel.init(300, 400)
pyxel.images[0].load(0, 0, "sprites.png", incl_colors=True)
font18 = pyxel.Font("font-18.bdf")
font32 = pyxel.Font("font-32.bdf")


@enum.unique
class Sprite(enum.Enum):
    COYOTE = (0, 96, 64, 32, 48, 0)
    COYOTE_FALLING = (0, 128, 64, 48, 48, 0)
    COYOTE_FOOT_UP = (0, 176, 64, 32, 48, 0)
    PLATE = (0, 96, 16, 32, 16, 0)
    CLOUD_5 = (0, 64, 0, 32, 16, 0)
    CLOUD_4 = (0, 64, 16, 32, 16, 0)
    CLOUD_3 = (0, 64, 32, 32, 16, 0)
    CLOUD_2 = (0, 64, 48, 32, 16, 0)
    CLOUD_1 = (0, 96, 48, 32, 16, 0)


def animate(*parts) -> Sprite:
    total_frames = sum(frame for frame, _ in parts)
    frame_number = pyxel.frame_count % total_frames
    for f, sprite in parts:
        frame_number -= f
        if frame_number <= 0:
            return sprite

    return parts[-1][1]


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
        global player_state

        if self.state == self.State.DISSOLVING:
            self.frame += 1
            if self.frame >= 10:
                self.state = self.State.PLATE
                if not self.is_walkable:
                    player_state = PlayerState.FALLING

    def hide(self):
        self.frame = 0
        self.state = self.State.HIDDEN

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
            ][self.frame // 2]
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
        self.x = (pyxel.width - self.width * 32) // 2

    def add_tile(self, x: int, y: int, walkable: bool):
        self.tiles.append(Tile(self, x, y, walkable))

    def update(self):
        for tile in self.tiles:
            tile.update()
            if player_x == tile.x and player_y == tile.y:
                if tile.state == Tile.State.HIDDEN:
                    tile.state = Tile.State.DISSOLVING

    def draw(self):
        for tile in self.tiles:
            tile.draw()

    def get_xy_for_tile(self, x: int, y: int):
        return (x * 32 + self.x, y * 16 + 120)

    def is_dissolving(self):
        return any(tile.state == Tile.State.DISSOLVING for tile in self.tiles)

    def hide_all_tiles(self):
        for tile in self.tiles:
            tile.hide()


@enum.unique
class GameState(enum.Enum):
    TITLE = 0
    PLAYING = 1


@enum.unique
class PlayerState(enum.Enum):
    DEFAULT = 0
    FALLING = 1
    WON = 2


levels = [
    """
x-
""",
    """
xx
-x
""",
    """
--x
xxx
x--
""",
    """
x--x
--xx
xxx-
x---
""",
]


def load_level(nr: int) -> Grid:
    rows = levels[nr].strip().split("\n")
    grid = Grid(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, tile in enumerate(row):
            grid.add_tile(x, y, tile == "x")

    return grid


game_state = GameState.TITLE
player_state = PlayerState.DEFAULT
player_falling_frames = 0
current_level = 0
grid = load_level(current_level)
steps_taken = 0
player_x = grid.width // 2
player_y = -1


def retry_level():
    global player_state, player_falling_frames, player_x, player_y, steps_taken
    player_state = PlayerState.DEFAULT
    player_falling_frames = 0
    player_x = grid.width // 2
    player_y = -1
    grid.hide_all_tiles()


def level_won():
    global player_state, player_y, player_x, current_level, grid
    player_state = PlayerState.DEFAULT
    player_y = grid.height + 2
    current_level += 1
    grid = load_level(current_level)
    player_x = grid.width // 2
    player_y = -1


def update_playing_scene():
    global player_x, player_y, player_falling_frames, player_state, steps_taken

    can_player_move = not grid.is_dissolving() and player_state == PlayerState.DEFAULT
    if can_player_move:
        if pyxel.btnp(pyxel.KEY_LEFT):
            player_x -= 1
            if player_x >= 0:
                steps_taken += 1
            player_x = max(0, player_x)
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            player_x += 1
            if player_x <= grid.width - 1:
                steps_taken += 1
            player_x = min(grid.width - 1, player_x)
        elif pyxel.btnp(pyxel.KEY_UP) and player_y >= 0:
            player_y -= 1
            if player_y >= 0:
                steps_taken += 1
            player_y = max(0, player_y)
        elif pyxel.btnp(pyxel.KEY_DOWN):
            player_y += 1
            if player_y <= grid.height - 1:
                steps_taken += 1

            if player_y == grid.height:
                level_won()

    if player_state == PlayerState.FALLING:
        player_falling_frames = max(1, player_falling_frames)
        player_falling_frames *= 1.2
        if player_falling_frames >= 90:
            retry_level()

    grid.update()


def blt_number(x, y, number, scale=1):
    digits = [
        (0, 0, 0, 6, 8, 0),
        (0, 7, 0, 3, 8, 0),
        (0, 10, 0, 6, 8, 0),
        (0, 16, 0, 6, 8, 0),
        (0, 22, 0, 7, 8, 0),
        (0, 29, 0, 6, 8, 0),
        (0, 35, 0, 6, 8, 0),
        (0, 41, 0, 6, 8, 0),
        (0, 47, 0, 6, 8, 0),
        (0, 53, 0, 6, 8, 0),
    ]
    for i, digit in enumerate(str(number)):
        d = digits[int(digit)]
        pyxel_utils.blt_topleft(x, y, *d, scale=scale)
        x += d[3] * scale


def draw_player():
    if player_state == PlayerState.FALLING:
        sprite = Sprite.COYOTE_FALLING.value
    else:
        sprite = animate((60, Sprite.COYOTE), (15, Sprite.COYOTE_FOOT_UP)).value

    x, y = grid.get_xy_for_tile(player_x, player_y)
    pyxel_utils.blt_topleft(x, y - 40 + player_falling_frames, *sprite)


def draw_playing_scene():
    pyxel.rect(0, 0, pyxel.width, 100, 3)
    pyxel_utils.blt_topleft(0, 98, 0, 16, 64, 64 + 16, 32, 0, scale=2)
    pyxel_utils.blt_topleft((64 + 16) * 2, 98, 0, 16, 64, 64 + 16, 32, 0, scale=2)

    grid.draw()
    draw_player()

    y = 100 + (grid.height + 1) * 16
    pyxel.rect(0, y + 20, 300, pyxel.height, 3)
    pyxel_utils.blt_topleft(0, y, 0, 16, 64 + 32, 64 + 16, 32, 0, scale=2)
    pyxel_utils.blt_topleft((64 + 16) * 2, y, 0, 16, 64 + 32, 64 + 16, 32, 0, scale=2)

    pyxel_utils.text_centered(pyxel.width // 2, 330, str(steps_taken), 5, font32)
    pyxel_utils.text_centered(pyxel.width // 2, 360, "steps taken", 7, font18)

    if current_level == 0:
        pyxel_utils.text_centered(
            pyxel.width // 2, 180, "Use arrow keys to reach", 5, font18
        )
        pyxel_utils.text_centered(pyxel.width // 2, 200, "the other side.", 5, font18)
        pyxel_utils.text_centered(pyxel.width // 2, 240, "Watch your step.", 5, font18)


def update_title_scene():
    if pyxel.btnp(pyxel.KEY_SPACE):
        global game_state
        game_state = GameState.PLAYING


def draw_title_scene():
    pyxel_utils.blt_topleft(0, 200, *Sprite.PLATE.value, scale=3)
    pyxel_utils.blt_topleft(20, 180, *Sprite.PLATE.value, scale=2)
    pyxel_utils.blt_topleft(10, 170, *Sprite.PLATE.value, scale=1)
    pyxel_utils.blt_topleft(160, 150, *Sprite.CLOUD_2.value, scale=5)
    pyxel_utils.blt_topleft(-30, 210, *Sprite.CLOUD_5.value, scale=10)

    sprite = animate((60, Sprite.COYOTE), (15, Sprite.COYOTE_FOOT_UP))
    pyxel_utils.blt_topleft(60, 90, *sprite.value, scale=4)

    pyxel_utils.text_centered(pyxel.width // 2 - 70 + 2, 8 - 1, "Falling", 5, font32)
    pyxel_utils.text_centered(pyxel.width // 2 - 70, 8, "Falling", 7, font32)
    pyxel_utils.text_centered(pyxel.width // 2 + 2, 36 - 1, "is learning", 5, font32)
    pyxel_utils.text_centered(pyxel.width // 2, 36, "is learning", 7, font32)
    pyxel_utils.text_centered(
        pyxel.width // 2, 370, "Press [SPACE] to start", 5, font18
    )


def update():
    match game_state:
        case GameState.TITLE:
            update_title_scene()
        case GameState.PLAYING:
            update_playing_scene()


def draw():
    pyxel.cls(9)

    match game_state:
        case GameState.TITLE:
            draw_title_scene()
        case GameState.PLAYING:
            draw_playing_scene()


pyxel.run(update, draw)
