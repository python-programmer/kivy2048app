from kivy.animation import Animation
from kivy.factory import Factory
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
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.button import Button

NUMBER_OF_CELL = 4

SPACING = 7
COLORS = ('26c6da', '29b6f6', '2196f3', '5c6bc0',
          'd4e157', '9ccc65', '66bb6a', '009688',
          'ffb300', 'ff9800', 'ff7043', 'ec407a',
          'bdbdbd', '78909c', '8d6e63', 'ab47bc')

NUMBERS = [2] * 4 + [4]

KEY_VECTORS = {
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
    has_combination = False
    score = NumericProperty(0)
    storage = JsonStore('db.json')
    best_score = NumericProperty(0)
    win_flag = False
    is_stoped_background_music = False

    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)
        self.moveSound = SoundLoader.load('data/audio/move.mp3')
        self.backgroundSound = SoundLoader.load('data/audio/background.mp3')
        self.winSound = SoundLoader.load('data/audio/win.mp3')
        self.loseSound = SoundLoader.load('data/audio/lose.mp3')
        # self.backgroundSound.loop = True change volume to default on start
        self.backgroundSound.on_stop = self.play_background_sound
        Clock.schedule_once(self.play_background_sound)

    def play_background_sound(self, dt=None):
        if self.is_stoped_background_music is False:
            self.backgroundSound.play()
            self.backgroundSound.volume = 0.1

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
        self.win_flag = False
        self.b = [[None for i in range(NUMBER_OF_CELL)]
                  for j in range(NUMBER_OF_CELL)]

        self.clear_widgets()
        self.stop_lose_sound()
        self.score = 0

        self.new_tile()
        self.new_tile()

    @staticmethod
    def valid_cell(x, y):
        return 0 <= x < NUMBER_OF_CELL and 0 <= y < NUMBER_OF_CELL

    def can_move(self, x, y):
        return self.valid_cell(x, y) and self.b[x][y] is None

    def new_tile(self, *args):
        if self.moveSound.state is 'play':
            self.moveSound.stop()

        self.has_combination = False
        empty_cell = [(x, y) for x, y in self.all_cell() if self.b[x][y] is None]
        x, y = random.choice(empty_cell)
        self.add_tile(x, y, number=random.choice(NUMBERS))
        if len(empty_cell) == 1 and self.is_deadlock():
            self.lose()
        self.moving = False

    def add_tile(self, x, y, number=2):
        tile = Tile(number=number, size=self.cell_size, pos=self.cell_pos(x, y))
        self.b[x][y] = tile
        self.add_widget(tile)

    def on_key_down(self, window, key, *args):
        if key in KEY_VECTORS:
            self.move(*KEY_VECTORS[key])

    def move(self, dir_x, dir_y):
        if self.moving:
            return

        self.reset_tile_combined_flag()

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
                            self.b[x + dir_x][y + dir_y].is_recently_combined is False:

                self.b[x][y] = None
                x += dir_x
                y += dir_y
                self.remove_widget(self.b[x][y])
                self.b[x][y] = tile
                tile.number *= 2
                tile.update_color()
                tile.is_recently_combined = True
                self.score += tile.number / 2
                self.has_combination = True

                if tile.number == 16 and self.win_flag is False:
                    self.win_flag = True
                    self.win()

                if self.best_score < self.score:
                    self.best_score = self.score

            if board_x == x and board_y == y:
                continue

            self.moveSound.play()
            animate = Animation(pos=self.cell_pos(x, y), duration=0.2, transition='in_cubic')

            if not self.moving:
                animate.on_complete = self.new_tile
                self.moving = True

            animate.start(tile)

    def reset_tile_combined_flag(self):
        for i, j in self.all_cell():
            tile = self.b[i][j]
            if tile:
                tile.is_recently_combined = False

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
        self.winSound.play()
        if self.is_stoped_background_music is False:
            self.toggle_music()
            self.winSound.on_stop = self.toggle_music
        popup = Factory.WinPopup()
        popup.open()

    def lose(self):
        self.loseSound.play()
        if self.is_stoped_background_music is False:
            self.toggle_music()
            self.loseSound.on_stop = self.toggle_music
        popup = Factory.LosePopup()
        popup.open()

    def stop_win_sound(self):
        if self.winSound.state is 'play':
            self.winSound.stop()

    def stop_lose_sound(self):
        if self.loseSound.state is 'play':
            self.loseSound.stop()

    def is_deadlock(self):
        for x, y in self.all_cell():
            if self.can_combine(x + 1, y, self.b[x][y].number) or self.can_combine(x, y + 1, self.b[x][y].number):
                return False

        return True

    on_size = resize
    on_pos = resize

    def store_cell_data(self):
        data = [[self.b[i][j].number if self.b[i][j] else None
                 for j in range(NUMBER_OF_CELL)]
                for i in range(NUMBER_OF_CELL)]

        self.storage.put('storage', cells=data, score=self.score, best_score=self.best_score,
                         win_flag=self.win_flag, is_stoped_background_music=self.is_stoped_background_music)

    def restore_cell_data(self):
        global NUMBER_OF_CELL
        btn_sound = GameApp.get_running_app().root.ids.btn_sound
        if self.storage.exists('storage'):
            data = self.storage.get('storage')['cells']
            NUMBER_OF_CELL = len(data[0])
            for x, y in self.all_cell():
                if data[x][y]:
                    self.add_tile(x, y, number=data[x][y])
            self.score = self.storage.get('storage')['score']
            self.best_score = self.storage.get('storage')['best_score']
            self.win_flag = self.storage.get('storage')['win_flag']
            self.is_stoped_background_music = self.storage.get('storage')['is_stoped_background_music']
            if self.is_stoped_background_music:
                btn_sound.source = 'data/img/stop-sound.png'
            else:
                btn_sound.source = 'data/img/sound.png'
        else:
            self.reset()

    @staticmethod
    def show_popup():
        popup = Factory.ResetPopup()
        popup.open()

    def toggle_music(self):
        btn_sound = GameApp.get_running_app().root.ids.btn_sound
        if self.backgroundSound.state is 'play':
            # is required for play_background_sound method because self.backgroundSound.on_stop = self.play_background_sound
            self.is_stoped_background_music = True
            self.backgroundSound.stop()
            btn_sound.source = 'data/img/stop-sound.png'
        else:
            self.is_stoped_background_music = False
            self.backgroundSound.play()
            self.backgroundSound.volume = 0.1
            btn_sound.source = 'data/img/sound.png'
    


class Tile(Widget):
    font_size = NumericProperty(14)
    number = NumericProperty(2)
    color = ListProperty(get_color_from_hex(TILE_COLORS[2]))
    number_color = ListProperty(get_color_from_hex('FFFFFF'))
    is_recently_combined = False

    def __init__(self, number=2, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.number = number
        self.font_size = 0.36 * self.width
        self.update_color()

    def update_color(self):
        self.color = get_color_from_hex(TILE_COLORS[self.number])
        text = str(self.number)

    def resize(self, pos, size):
        self.size = size
        self.pos = pos
        self.font_size = 0.36 * self.width


class BaseButton(Button):
    def __init__(self, **kwargs):
        super(BaseButton, self).__init__(**kwargs)
        self.touchSound = SoundLoader.load('data/audio/touch.mp3')


class GameApp(App):
    def on_start(self):
        board = self.root.ids.board
        board.restore_cell_data()
        Window.bind(on_key_down=board.on_key_down)

    def on_stop(self):
        board = self.root.ids.board
        board.store_cell_data()


if __name__ == '__main__':
    Window.clearcolor = get_color_from_hex('607d8b')
    LabelBase.register('Roboto',
                       fn_regular='data/font/Roboto-Thin.ttf',
                       fn_bold='data/font/Roboto-Medium.ttf')
    GameApp().run()