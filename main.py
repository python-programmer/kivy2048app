from kivy.animation import Animation
import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import BorderImage, Color
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import NumericProperty, ListProperty
from kivy.core.window import Keyboard
from kivy.vector import Vector
from kivy.core.text import LabelBase

NUMBER_OF_CELL = 4

SPACING = 7
COLORS = ('00bcd4', '0097a7', '006064', '009688',
          '00796b', '004d40', '3f51b5', '303f9f',
          '1a237e', '673ab7', '512da8')

KEYCODE_VECTORES = {
    Keyboard.keycodes['up']: (0, 1),
    Keyboard.keycodes['down']: (0, -1),
    Keyboard.keycodes['left']: (-1, 0),
    Keyboard.keycodes['right']: (1, 0)
}

TILE_COLORS = {2 ** i: color for i, color in enumerate(COLORS, start=1)}


class Board(Widget):
    b = [[None for i in range(NUMBER_OF_CELL)]
         for j in range(NUMBER_OF_CELL)]
    cell_size = None
    moving = False
    score = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self.resize()

    def resize(self, *args):
        self.cell_size = [(self.width - (NUMBER_OF_CELL+1)*SPACING)/NUMBER_OF_CELL] * 2
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex('81d4fa'))
            BorderImage(pos=self.pos, size=self.size, source='data/img/board.png')
            for x, y in self.all_cell():
                Color(*get_color_from_hex('FFFFFF'))
                BorderImage(pos=self.cell_pos(x, y),
                            size=self.cell_size,
                            source='data/img/cell.png')

        for x, y in self.all_cell():
            tile = self.b[x][y]
            if tile:
                tile.resize(size=self.cell_size, pos=self.cell_pos(x, y))

    @staticmethod
    def all_cell(flip_x=False, flip_y=False):
        for i in reversed(range(NUMBER_OF_CELL)) if flip_x else range(NUMBER_OF_CELL):
            for j in reversed(range(NUMBER_OF_CELL)) if flip_y else range(NUMBER_OF_CELL):
                yield (i, j)

    def cell_pos(self, x, y):
        return (self.x + x*(self.cell_size[0] + SPACING) + SPACING,
                self.y + y*(self.cell_size[1] + SPACING) + SPACING)

    def reset(self):
        self.moving = False
        self.b = [[None for i in range(NUMBER_OF_CELL)]
                  for j in range(NUMBER_OF_CELL)]

        self.new_tile()
        self.new_tile()

    @staticmethod
    def valid_cell(x, y):
        return 0 <= x < NUMBER_OF_CELL and 0 <= y < NUMBER_OF_CELL

    def can_move(self, x, y):
        return self.valid_cell(x, y) and self.b[x][y] is None

    def new_tile(self, *args):
        empty_cell = [(x, y) for x, y in self.all_cell() if self.b[x][y] is None]
        x, y = random.choice(empty_cell)
        tile = Tile(size=self.cell_size, pos=self.cell_pos(x, y))
        self.b[x][y] = tile
        self.add_widget(tile)
        if len(empty_cell) == 1 and self.is_deadlock():
            self.lose()
        self.moving = False

    def on_key_down(self, window, key, *args):
        if key in KEYCODE_VECTORES:
            self.move(*KEYCODE_VECTORES[key])

    def move(self, dir_x, dir_y):
        if self.moving:
            return

        self.reset_is_tile_combined()

        dir_x = int(dir_x)
        dir_y = int(dir_y)
        for board_x, board_y in self.all_cell(dir_x > 0, dir_y > 0):
            tile = self.b[board_x][board_y]
            if tile is None:
                continue

            x, y = board_x, board_y
            while self.can_move(x + dir_x, y + dir_y):
                self.b[x][y] = None
                x += dir_x
                y += dir_y
                self.b[x][y] = tile

            if self.can_combine(x + dir_x, y + dir_y, tile.number) and\
                            self.b[x + dir_x][y + dir_y].is_current_combined is False:

                self.b[x][y] = None
                x += dir_x
                y += dir_y
                self.remove_widget(self.b[x][y])
                self.b[x][y] = tile
                tile.number *= 2
                tile.update_color()
                tile.is_current_combined = True
                self.score += tile.number / 2

                if tile.number == 2048:
                    self.win()

            if board_x == x and board_y == y:
                continue

            anim = Animation(pos=self.cell_pos(x, y), duration=0.2, transition='in_cubic')

            if not self.moving:
                anim.on_complete = self.new_tile
                self.moving = True

            anim.start(tile)

    def reset_is_tile_combined(self):
        for i, j in self.all_cell():
            tile = self.b[i][j]
            if tile:
                tile.is_current_combined = False

    def can_combine(self, x, y, number):
        return self.valid_cell(x, y) and self.b[x][y] is not None and self.b[x][y].number == number

    def on_touch_up(self, touch):
        v = Vector(touch.pos) - Vector(touch.opos)
        if v.length() < 20:
            return

        if abs(v.x) > abs(v.y):
            v.y = 0
        elif abs(v.x) < abs(v.y):
            v.x = 0

        self.move(*v.normalize())

    def win(self):
        print('you win')

    def lose(self):
        print('you lose')

    def is_deadlock(self):
        for x, y in self.all_cell():
            if self.b[x][y] is None:
                return False

            if self.can_combine(x + 1, y, self.b[x][y].number) or self.can_combine(x, y + 1, self.b[x][y]):
                return False

        return True


    on_size = resize
    on_pos = resize


class Tile(Widget):
    font_size = NumericProperty(16)
    number = NumericProperty(2)
    color = ListProperty(get_color_from_hex(TILE_COLORS[2]))
    number_color = ListProperty(get_color_from_hex('#FFFFFF'))
    is_current_combined = False

    def __init__(self, number=2, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.number = number
        self.font_size = 0.5 * self.width
        self.update_color()

    def update_color(self):
        self.color = get_color_from_hex(TILE_COLORS[self.number])
        text = str(self.number)

    def resize(self, pos, size):
        self.size = size
        self.pos = pos
        self.font_size = 0.5 * self.width


class GameApp(App):
    def on_start(self):
        board = self.root.ids.board
        board.reset()
        Window.bind(on_key_down=board.on_key_down)


if __name__ == '__main__':
    Window.clearcolor = get_color_from_hex('607d8b')
    LabelBase.register('Roboto',
                       fn_regular='data/font/Roboto-Thin.ttf',
                       fn_bold='data/font/Roboto-Medium.ttf')
    GameApp().run()