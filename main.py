# _*_ coding: utf-8 _*_
# ------------------------- Review 2 ------------------------- #
# 1. لود آهنگ موفقیت داخل متد win انجام شد
# 2. لود آهنگ شکست داخل متد lose انجام شد
# 3. متد ثبت کاربر در یک thread جداگانه انجام شد
# 4. ابتدا بررسی می شود که کاربر قبلا ثبت نام کرده است اگر قبلا ثبت نام کرده باشد توکن
# اعتبارسنجی او باز گردانده می شود در غیر این صورت کاربر ثبت نام می شود
# ------------------------------------------------------------ #
# ------------------------- Review 1 ------------------------- #
# 1. کامل کردن و اضافه کردن توضیحات کدها
# 2.  اضافه کردن docstring ها
# 3. بررسی بهینه سازی  و اضافه کردن FIXME, TODO و ؟؟؟ جهت تغییر و بررسی
# 4. اضافه کردن تابع dynamic_popup برای popup های مختلف
# 5. حذف کدهای اضافی. مانند return True متد on_resume متعلق به کلاس GameApp, ...
# ------------------------------------------------------------ #

import json
import random
from kivy.animation import Animation
from kivy.factory import Factory
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import BorderImage, Color
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.core.window import Keyboard
from kivy.vector import Vector
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from jnius import cast
from jnius import autoclass
from bidi.algorithm import get_display
from lepl.apps.rfc3696 import Email
import arabic_reshaper

# نسخه ی برنامه
__version__ = '0.1.32'

# تعداد خانه های برنامه را 4 در نظر گرفته ایم که می توانیم آن را بیشتر یا کمتر کنیم
NUMBER_OF_CELL = 4

# متناسب با اعداد خانه ها  16 رنگ انتخاب نموده ایم که می توانیم آن ها در این جا تغییر دهیم
COLORS = ('26c6da', '29b6f6', '2196f3', '5c6bc0', 'd4e157', '9ccc65', '66bb6a', '009688',
          'ffb300', 'ff9800', 'ff7043', 'ec407a', 'bdbdbd', '78909c', '8d6e63', 'ab47bc')

# اعداد تصادفی که بعد از هر حرکت به بورد  بازی اضافه می شوند 2و 4 هستند که بایستی احتمال آمدن عدد تصادفی 2 بیشتر از 4
# باشد به همین دلیل لیست انتخاب اعداد تصادفی زیر، تعداد 2 بیشتری دارد
NUMBERS = [2] * 10 + [4]

# نگاشت اعداد خانه ها به رنگ ها
TILE_COLORS = {2 ** i: color for (i, color) in enumerate(COLORS, start=1)}

# برای صفحات با اندازه های مختلف، به جای استفاده از یک اندازه ی ثابت برای فونت، از مقداری دینامیک استفاده می کنیم. حاصل
# ضرب عرض بورد در ضریب ثابت. ما این ضریب ثابت را 0.36 در نظر گرفته ایم. شما می توانید بسته به نیازتان آن را تغییر دهید
FONT_SIZE_COEFFICIENT = 0.36

# نگاشت کلیدهای کیبورد به حرکت ها. مثلا فشردن کلید بالا x را تغییر نمی دهد اما یک واحد به y اضافه می کند
KEY_VECTORS = {Keyboard.keycodes['up']: (0, 1),
               Keyboard.keycodes['down']: (0, -1),
               Keyboard.keycodes['left']: (-1, 0),
               Keyboard.keycodes['right']: (1, 0)}

# میزان صدای آهنگ پس زمینه
VOLUME = 0.2

# از آنجایی که نمی توان در فایل kv متغییر تعریف کرد این متغییر ها را در اینجا تعریف کرده ایم  که به ترتیب برای padding و
#  spacing مورد نیاز برای ترازبندی به کار می روند
PADDING = dp(10)
SPACING = dp(5)

# آدرس سرور مورد نیاز برای ثبت امتیازات و اطلاعات کاربران
SERVER = 'http://yourserver-address/{0}'

# Header درخواست های ارسال شده به سرور
HEADERS = {'Content-type': 'application/json'}

# Token کاربر وارد شده به سرور
TOKEN = None

# برای مشخص کردن پلتفرمی که برنامه روی آن اجرا شده است از دستور زیر استفاده می کنیم. مثلا سیستم عامل اندروید است یا
# ویندوز
_platform = platform()

def get_user_email():
    """
 ایمیل کاربر را از حساب کاربریش دریافت می کند و آنرا بر می گرداند
برای پلتفرم های مختلف، متفاوت است. در اینجا ما تنها از پلتفرم اندروید برای گرفتن ایمیل حساب کاربری استفاده کرده ایم
مقادیر بازگشتی:
ایمیل حساب کاربری را بر می گرداند
    """
    email = None
    if _platform == 'android':

        # در 4 خط کد زیر از pyjnius (اجرای دستورات جاوا)  برای گرفتن حساب های کاربری، استفاده کرده ایم
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        AccountManager = autoclass('android.accounts.AccountManager')
        accounts = AccountManager.get(currentActivity.getApplicationContext()).getAccounts()

        # در کدهای باقیمانده ی داخل if برای بدست آوردن ایمیل کاربر استفاده کرده ایم
        # تابع زیر برای بررسی ایمیل بودن ورودی داده شده به آن به کار می رود
        email_validator = Email()
        for account in accounts:
            if email_validator(account.name):
                email = account.name
                break

    return email

def post_request(url, data, headers, success_func, error_func, failure_func):
    """
    درخواستی با متد POST  رابرای سرور ارسال می کند
    آرگومان ها:
url:  آدرسی که می خواهیم اطلاعاتی را برای آن ارسال کنیم
data: اطلاعات ارسالی به سرور
headers: هدر در خواست ارسالی. مثلا محتوای ارسالی دارای فرمت json است
success_func: بعد از درخواست موفقیت آمیز این تابع  اجرا شود
error_func: اگر در ارتباط با سرور مشکلاتی مانع ارسال درخواست شد این تابع اجرا شود. اینترنت قطع است
failure_func: اگر در سرور مشکلاتی مانع اجرای پاسخ به درخواست ارسال شده، شد این تابع اجرا
 شود. مثلا فرمت ایمیل نامعتبر است
    """

    UrlRequest(url, req_body=json.dumps(data), req_headers=headers, on_success=success_func,
               on_error=error_func, on_failure=failure_func)

def get_request(url, headers, success_func, error_func, failure_func):
    """
    درخواستی با متد GET را به سرور ارسال می کند
    آرگومان ها:
url:  آدرسی که می خواهیم اطلاعاتی را برای آن ارسال کنیم
headers: هدر در خواست ارسالی. مثلا محتوای ارسالی دارای فرمت json است
success_func: بعد از درخواست موفقیت آمیز این تابع  اجرا شود
error_func: اگر در ارتباط با سرور مشکلاتی مانع ارسال درخواست شد این تابع اجرا شود. اینترنت قطع است
failure_func: اگر در سرور مشکلاتی مانع اجرای پاسخ به درخواست ارسال شده، شد این تابع اجرا
 شود. مثلا فرمت ایمیل نامعتبر است
    """

    UrlRequest(url, req_headers=headers, on_success=success_func, on_error=error_func, on_failure=failure_func)

def set_bidi_text(text):
    """
    متنی فارسی را دریافت می کند و آنرا با فرمتی مناسب برای برنامه بر می گرداند
kivy از زبان فارسی پشتیبانی نمی کند برای حل این مشکل از دو module به نام های python-bidi و arabic_reshaper استفاده کرده ایم
آرگومان ها:
text: متن فارسی
مقادیر بازگشتی:
متن فارسی فرمت بندی شده را بر می گرداند
    """

    # کلمه 'بله' وقتی به این تابع ارسال می شود به صورت 'ه ل ب'  است
    text = unicode(text, 'utf-8')

    # کد زیر آن را به شکل 'هلب' در می آورد
    result = arabic_reshaper.reshape(text)

    # در نهایت با استفاده از تابع زیر به شکل صحیح کلمه یعنی 'بله' در می آید
    return get_display(result)

def dynamic_popup(title, message, buttons):
    """
    این تابع عنوان، پیام و اطلاعات مربوط به دکمه یا دکمه های مورد نیاز را دریافت می کند و یک
 popup را با استفاده از این اطلاعات می سازد سپس آن را اجرا کرده و آن را بر می گرداند
هدف از عمومی سازی این قابلیت، کم کردن کدهای استفاده شده برای ایجاد popup های متفاوت برای
 عملیات متفاوت است که طی این عمومی سازی تقریبا 150 خط کد حذف شد
    آرگومان ها:
title: عنوان popup
message: پیام popup
buttons: لیست دکمه هایی که می خواهیم کاربر با آن ها تعامل داشته باشد. مثلا دکمه
 'خروج وبررسی'  برنامه را می بندد
    مقادیر بازگشتی:
popup اجرا شده را برمی گرداند. این popup در متدهای win و lose کلاس board کاربرد دارد
    """

    # شی برنامه ی فعلی اجرا شده را برمی گرداند
    app = GameApp.get_running_app()

    # کلاس BasePopup موجود در فایل game.kv برنامه را برمی گرداند و یک شی از آن را ایجاد می کند
    popup = Factory.BasePopup()
    popup.title = set_bidi_text(title)
    content = Factory.PopupContent()
    content.text = set_bidi_text(message)
    for button in buttons:

        # با استفاده از ids می توان به سایر widget هایی که دارای id  و روی container فعلی هستند، دسترسی پیدا کرد
        content.ids.btn_container.add_widget(make_button(button, app, popup))

    popup.add_widget(content)
    popup.open()
    return popup

def make_button(btn, app, popup):
    """
    در این تابع یک دیکشنری از اطلاعات دریافت و براساس این اطلاعات دکمه ای ایجاد و برگرداننده می شود
آرگومان ها:
btn: یک دیکشنری حاوی اطلاعات زیر است
    text: متن دکمه
    type: نوع دکمه که را مشخص می کند مثلا DefaultButton موجود در فایل game.kv
    on_press: متد یا تابعی که هنگام کلیک کردن فراخوانی می شود
app: شی برنامه فعلی
popup: popup ای که این دکمه بر روی آن قرار می گیرد
    مقادیر بازگشتی:
دکمه ای را بر می گرداند
    """

    # از تابع getattr برای گرفتن کلاس دکمه استفاده می کنیم
    button = getattr(Factory, btn.get('type'))()
    button.text = set_bidi_text(btn.get('text'))

    # کد زیر expression داخل on_press را به event on_press  دکمه ی ایجاد شده متصل می کند
    # توجه داشته باشید که وجود app, popup الزامی است
    button.bind(on_press=eval(btn.get('on_press', 'popup.dismiss')))
    return button

class Board(Widget):
    """
    این کلاس در برگیرنده ی صفحه ی خانه هاست. خانه های جدید به این board اضافه می شوند  و روی این board به حرکت در می آیند
    """

    # این لیست یک لیست دوبعدی است که در برگیرنده خانه های دارای اعداد برنامه است
    b = [[None for i in range(NUMBER_OF_CELL)]
         for j in range(NUMBER_OF_CELL)]

    # در برگیرنده ی اندازه هر خانه ی برنامه است
    cell_size = None

    # آیا انیمیشی در حال اجراست یا نه؟
    moving = False

    # امتیاز اجرای فعلی را ذخیره می کند
    score = NumericProperty(0)

    # بیشترین امتیاز کاربر را ذخیره می کند
    best_score = NumericProperty(0)

    # بررسی می کند که آیا در اجرای فعلی به 2048 رسیده ایم یا نه. اگر رسیده باشیم نباید در برای 2048 بعدی پیام موفقیت
    # نمایش داده شود
    win_flag = False

    # بررسی می کند که آیا آهنگ پس زمینه خاموش است یا نه
    is_stopped_background_music = False

    # در برگیرنده ی اجرای فعلی از امتیاز صفر است. اگر اجرای فعلی باقیمانده ی اجرای قبلی باشد مقدار این متغییر False
    # خواهد بود در غیر اینصورت مقدار آن True خواهد بود. برای ثبت امتیاز به صورت آنلاین بایستی این مقدار True باشد
    is_current_session = True

    # مکان و نوع ذخیره سازی را تعیین می کند
    storage = JsonStore('db.json')

    # آهنگ موفقیت را نگه می دارد
    winSound = None

    # آهنگ شکست را نگه می دارد
    loseSound = None

    def __init__(self, **kwargs):
        super(Board, self).__init__(**kwargs)

        #‌ ???: آیا می توان صدای حرکت مهره ها را در کلاس  tile لود و اجرا نمود
        # در اینجا صدای حرکت خانه ها را لود می کنیم
        self.moveSound = SoundLoader.load('data/audio/move.mp3')

        # در اینجا آهنگ پس زمینه را لود می کنیم
        self.backgroundSound = SoundLoader.load('data/audio/background.mp3')

        # در اینجا آهنگ موفقیت را لود می کنیم
        # FIXED: لود آهنگ موفقیت داخل متد win انجام شود
        # self.winSound = SoundLoader.load('data/audio/win.mp3')

        # در اینجا آهنگ شکست را لود می کنیم
        # FIXED: لود آهنگ شکست داخل متد lose انجام شود
        # self.loseSound = SoundLoader.load('data/audio/lose.mp3')

        # در اینجا می توانستیم از loop  خود SoundLoader استفاده کنیم اما از آنجایی که در هنگام loop بلندی صدا را به
        # میزان پیش فرض برمی گرداند به همین دلیل از روش زیر استفاده کردیم که:
        # هنگام توقف برنامه آن را دوباره اجرا نموده سپس بلندی صدا را تنظیم می کنیم
        self.backgroundSound.on_stop = self.play_background_sound

        # کد زیر هنگام اجرای سازنده فقط یکبار انجام می شود
        Clock.schedule_once(self.play_background_sound)

    def play_background_sound(self, dt=None):
        """
        در این متد آهنگ پس زمینه را (دوباره)اجرا و بلندی صدای آن را نیز تنظیم می کنیم
        آرگومان ها:
        dt: اطلاعات ارسالی توسط Clock.schedule_once
        """

        # اگر کاربر آهنگ پس زمینه را متوقف کرده باشد دیگر این متد اجرا نمی شود
        if self.is_stopped_background_music is False:
            self.backgroundSound.play()

            # تنظیم میزان صدای آهنگ پس زمینه
            self.backgroundSound.volume = VOLUME

    def resize(self, *args):
        """
        این متد اندازه ها را تعیین می کند. اندازه بورد، اندازه خانه ها و همچنین مکان خانه ها.
        آرگومان ها:
        args: اطلاعات ارسالی توسط on_size و on_pos
        """

        # اندازه هر خانه از فرمول زیر بدست می اید:
        # cell_size = (board_width - (n + 1) * spacing) / n
        # n: تعداد خانه ها
        self.cell_size = [(self.width - (NUMBER_OF_CELL + 1) * SPACING) / NUMBER_OF_CELL] * 2

        # صفحه رابرای قرار دادن بورد و خانه ها پاک می کند
        self.canvas.before.clear()

        # در پس زمینه ی بورد خانه ها را رسم می کند همچنین عکسی را به عنوان پس زمینه بورد قرار می دهد
        with self.canvas.before:

            # رنگ بورد را تنظیم می کند
            Color(*get_color_from_hex('81d4fa'))

            # عکس board.png را به عنوان پس زمینه ی بورد تنظیم می کند
            BorderImage(pos=self.pos, size=self.size, source='data/img/board.png')

            # n * n خانه ی خالی را به بورد اضافه می کند
            for (x, y,) in self.all_cell():
                Color(*get_color_from_hex('FFFFFF'))
                BorderImage(pos=self.cell_pos(x, y),
                            size=self.cell_size,
                            source='data/img/cell.png',
                            border=[10, 10, 10, 10])

        self.resize_tiles()

    def resize_tiles(self):
        """
        اندازه و مکان خانه هایی که مقدار دارند، را تنظیم می کند
        """

        for (x, y,) in self.all_cell():
            tile = self.b[x][y]
            if tile:
                tile.resize(size=self.cell_size, pos=self.cell_pos(x, y))

        self.__reset()

        # FIXME: از آنجایی که پلتفرم مورد استفاده اندروید است در نتیجه این متد فقط یکبار فراخوانی می شود
        # پس انتظار می رود که خط زیر نیز یک بار اجرا شود. اما در پلتفرم هایی که امکان تغییر اندازه ی
        # پنجره ی اجرای بازی هست برای هر تغییر در اندازه ی پنجره داده ها از  مخزن ذخیره سازی خوانده
        # می شوند پس داده از اول تنظیم می شوند که منطقی نیست
        self.restore_cell_data()

    # FIXME: متدهای استاتیک به صورت تابع تعریف شوند
    @staticmethod
    def all_cell(flip_x=False, flip_y=False):
        """
        این متد یک generator  را ایجاد می کند که با هر بار فراخوانی x, y را بر می گرداند
یعنی عملکرد آن شبیه کد زیر است
for i in range(4):
    for j in range(4):
        print(i, j)
برای جلوگیری از استفاده از این کد بارها و بارها  در جاهای مختلف، آن را در این متد تعریف کردیم.
برای استفاده از این متد:
for i, j in all_cell():
    print(i, j)

        آرگومان ها:
flip_x: جهت پیمایش محور x  را مشخص می کند
flip_x: جهت پیمایش محور y را مشخص می کند
        مقادیر بازگشتی:
x, y را بر می گرداند که هر یک مقادیری بین [0 .. n] را می پذیرند که n: تعداد خانه ها – 1 است
        """

        # اگر flip_x = True  باشد آنگاه پیمایش از انتها به ابتدا است یعنی مقادیر i برابر است با:
        # 3, 2, 1, 0   واین بدان دلیل است که هنگام ترکیب خانه های هم مقدار حفره های خالی در صفحه ایجاد نشود
        for i in reversed(range(NUMBER_OF_CELL)) if flip_x else range(NUMBER_OF_CELL):
            for j in reversed(range(NUMBER_OF_CELL)) if flip_y else range(NUMBER_OF_CELL):
                yield (i, j)

    def cell_pos(self, x, y):
        """
        براساس اندیس خانه ها، مکان واقعی آن ها را برحسب پیکسل  می سازد
        آرگومان ها:
x: ردیف خانه ی مورد نظر
y: ستون خانه ی مورد نظر
        مقادیر بازگشتی
(x1, x1) مکان خانه ی مورد نظر را بر می گرداند
        """

        # محل خانه ی مورد نظر روی محور x از فرمول زیر بدست می آید:
        # اندیس ردیف + (اندیس ردیف * (عرض خانه + فضای بین دو خانه ی مجاور) + فضای بین دو خانه ی مجاور)
        # و به همین ترتیب برای محور y
        return (self.x + x * (self.cell_size[0] + SPACING) + SPACING,
                self.y + y * (self.cell_size[1] + SPACING) + SPACING)

    def reset(self):
        """
        برنامه را صفر می کند یا بازنشانی می کند(برنامه را reset می کند)
        """

        self.__reset()
        self.new_tile()
        self.new_tile()

    def __reset(self):
        """
        متغییرها ی برنامه را به حالت اولیه بر می گرداند یا صفر می کند
        """

        self.b = [[None for i in range(NUMBER_OF_CELL)]
                  for j in range(NUMBER_OF_CELL)]
        self.is_current_session = True
        self.moving = False
        self.win_flag = False
        self.clear_widgets()
        # self.stop_lose_sound()
        self.score = 0

    @staticmethod
    def valid_cell(x, y):
        """
        بررسی می کند تا مشخص کند که خانه مورد نظر در محدوده ی معتبری هست یا خیر
اگر x , y  کوچکتر از n  و بزرگتر یا مساوی 0 باشند خانه ی مورد نظر معتبر است
n: تعداد خانه های هر ردیف یا هر ستون
        آرگومان ها:
x: اندیس ردیف خانه ی مورد نظر
y: اندیس ستون خانه ی مورد نظر

مقادیر بازگشتی:
مقدار True یا False: آیا خانه مورد نظر معتبر است یا خیر
        """

        return 0 <= x < NUMBER_OF_CELL and 0 <= y < NUMBER_OF_CELL

    def can_move(self, x, y):
        """
        آیا می توان خانه ی را در x, y  دریافتی قرار داد یا خیر
آرگومان ها:
x: اندیس ردیف خانه ی مورد نظر
y: اندیس ستون خانه ی مورد نظر
مقادیر بازگشتی:
True یا False: آیا می توان خانه ی را در x, y  دریافتی قرار داد؟
        """

        # آیا خانه ی مورد نظر معتبر است و آیا خانه ی موردنظر خالی است
        return self.valid_cell(x, y) and self.b[x][y] is None

    def new_tile(self, *args):
        """
        خانه های خالی بورد را پیدا می کند سپس عددی تصادفی بین 2و 4 را انتخاب می کند و از میان
خانه های خالی یکی را به تصادف انتخاب می کند در نهایت براساس این اطلاعات خانه ای جدید را
ایجاد و به بورد اضافه می کند
آرگومان ها:
args: اطلاعات ارسالی توسط متد on_complete
        """

        # اگر صدای حرکت در حال اجراست آن را متوقف کن
        if self.moveSound.state is 'play':
            self.moveSound.stop()

        # از آنجایی که هنگام اتمام انیمیشن حرکت این متد فراخوانی می شود باید flag انیمیشن را صفر کنیم
        self.reset_moving()

        # پیدا کردن خانه های خالی بورد
        empty_cell = [(x, y) for (x, y,) in self.all_cell() if self.b[x][y] is None]

        # انتخاب یک خانه ی خالی بورد
        (x, y) = random.choice(empty_cell)

        # ایجاد و اضافه کردن خانه ی خالی به بورد
        self.add_tile(x, y, number=random.choice(NUMBERS))

        # اگر تعداد خانه های خالی قبل از انتخاب خانه خالی 1 باشدو حرکتی وجود نداشته باشد متد lose را فراخوانی کن
        if len(empty_cell) == 1 and self.is_deadlock():

            # بعد از 2 ثانیه تاخیرمتد lose را فراخوانی کن. این کار برای دقت در دلیل شکست است
            Clock.schedule_once(self.lose, 2)

    def add_tile(self, x, y, number=2):
        """
این متد اندیس ردیف، اندیس ستون و عدد خانه را می گیرد و براساس این اطلاعات خانه ی مورد نظر را می سازد و با انیمیشن آن را به بورد اضافه می کند
آرگومان ها:
x: اندیس ردیف خانه ی مورد نظر
y: اندیس ستون خانه ی مورد نظر
number: شماره یا عدد خانه ی مورد نظر
        """

        pos = self.cell_pos(x, y)
        size = self.cell_size

        # توسط کد زیر  مرکز خانه ی مورد نظر را پیدا می کنیم
        center = (size[0] / 2 + pos[0], size[1] / 2 + pos[1])

        # خانه ی  موردنظر را بااندازه=(0, 0)  و مکان = مرکز خانه ی موردنظر، ایجاد می کنیم
        # این کار برای انیمیشن اضافه کردن خانه است
        tile = Tile(number=number, size=(0, 0), pos=center)
        self.b[x][y] = tile
        self.add_widget(tile)

        # تا زمانی که انیمیشن اضافه کردن خانه تمام نشده است نباید حرکتی صورت گیرد
        self.moving = True
        animate = tile.new_tile_animate(pos=pos, size=size, font_size=self.cell_size[0] * FONT_SIZE_COEFFICIENT)

        # بعد از اتمام انیمیشن self.moving = False می شود
        animate.on_complete = self.reset_moving

    def reset_moving(self, *args):
        """
شرایط را برای حرکت بعدی فراهم می کند
آرگومان ها:
args: اطلاعاتی ارسالی توسط متد on_complete
        """
        self.moving = False

    def on_key_down(self, window, key, *args):
        """
این متد به event on_key_down پاسخ می دهد. توجه داشته باشید که برای پلتفرم های دارای کیبورد کاربرد دارد(window, mac)
آرگومان ها:
window: اطلاعات ارسالی توسط متد on_key_down
key: کلیدی که فشرده شده است
args: اطلاعات ارسالی توسط متد on_key_down
        """

        # اگر کلید فشرده شده یکی از کلیدهای بالا، پایین، چپ و راست باشد
        if key in KEY_VECTORS:

            # مقدار تنظیم شده برای این کلید را به متد move بفرست
            self.move(*KEY_VECTORS[key])

    def move(self, dir_x, dir_y):
        """
       این متد جهت حرکت را می گیرد و خانه ها را در آن جهت به حرکت در می آورد. اگر ترکیب خانه،
 وجود داشته باشد آن را ترکیب می کند. به عبارت دیگر مغز پروژه، این متد است
آرگومان ها:
dir_x: حرکت در جهت محور x (حرکت ردیفی)
dir_y: حرکت در جهت محور y (حرکت ستونی)
توجه داشته باشید در هر حرکت فقط یکی از این دو متغییر مقدار دارند (مقدار غیر صفر) یعنی تنها حرکت های افقی و عمودی داریم

        """

        # اگر انیمیشنی در حال اجراباشد هیچ کاری انجام نمی دهد
        if self.moving:
            return

        # flag اخیرا ترکیب شده هر خانه را صفر می کند
        self.reset_tile_combined_flag()

        # وقتی که از تاچ برا ی حرکت خانه ها استفاده می شود مقدار ارسالی از نوع float است به همین دلیل باید تبدیل به int  شود
        dir_x = int(dir_x)
        dir_y = int(dir_y)

        # در این حلقه تک تک خانه ها  بررسی می شوند اگر ترکیبی یا حرکتی وجود داشته باشد/شند آن/ها را انجام می دهد/هند
        for (board_x, board_y) in self.all_cell(dir_x > 0, dir_y > 0):
            tile = self.b[board_x][board_y]

            # اگر این خانه خالی باشد به ابتدای حلقه برو  و با خانه ی بعدی شروع کن
            if tile is None:
                continue

            # برای انیمیشن به مکان اولیه نیاز خواهیم داشت
            (x, y) = (board_x, board_y)

            # در حلقه ی زیر خانه ی فعلی را آنقدر  در جهت تعیین شده حرکت می دهیم تا به وضعیت ایست/بن بست
# (خانه ای جلویش باشد یا به کناره ها برخورد کنیم) برسیم                         
            while self.can_move(x + dir_x, y + dir_y):
                self.b[x][y] = None
                x += dir_x
                y += dir_y
                self.b[x][y] = tile

            # اگر خانه ای جلوی خانه ی فعلی باشد و امکان ترکیب وجود داشته باشد و این خانه در حرکت فعلی
            # با خانه ای دیگر ترکیب نشده باشد آنگاه این دو خانه را با هم ترکیب کن
            # توجه داشته باشید در هر حرکت فقط امکان یک ترکیب برای هر خانه وجود دارد
            if self.can_combine(x + dir_x, y + dir_y, tile.number) and self.b[(x + dir_x)][(y + dir_y)].is_recently_combined is False:
                self.b[x][y] = None
                x += dir_x
                y += dir_y

                # خانه ی جلوی خانه ی فعلی را با انیمیشن حذف کن
                remove_animate = self.b[x][y].new_tile_animate(size=(0, 0), pos=self.b[x][y].center, font_size=0, duration=0.03)
                remove_animate.on_complete = self.remove_widget
                self.b[x][y] = tile

                # عدد خانه ی ترکیبی را دو برابر کن
                tile.number *= 2

                # رنگ خانه ی ترکیبی را متناسب با عدد جدید بروز رسانی کن
                tile.update_color()

                # flag اخیرا ترکیب شده ی خانه ی ترکیب شده را True کن تا در حرکت فعلی با خانه ای دیگر ترکیب نشود
                tile.is_recently_combined = True

                # نصف عدد ترکیب شده را به امتیاز اضافه کن
                self.score += tile.number / 2

                # اگر عدد ترکیب شده برابر 2048 باشد و در اجرای فعلی قبلا به 2048 نرسیده باشیم متد win را جهت
                # اجرای عملیات موفقیت اجرا کن و win_flag  را به True تنظیم کن
                if tile.number == 2048 and self.win_flag is False:
                    self.win_flag = True
                    self.win()

                # اگر بهترین امتیاز از امتیاز فعلی کمتر باشد بهترین امتیاز را به این امتیاز تنظیم کن
                if self.best_score < self.score:
                    self.best_score = self.score

            # اگر حرکتی وجود نداشته باشد به ابتدای حلقه برو و با خانه ی بعدی ادامه بده
            if board_x == x and board_y == y:
                continue

            # خانه ی فعلی را از مکان اولیه تا مکان جدید با انیمیشن حرکت بده
            animate = tile.move_animate(pos=self.cell_pos(x, y))
            if not self.moving:

                # بعد از کامل شدن انیمیشن خانه ای جدید را به صفحه اضافه کن
                animate.on_complete = self.new_tile

                # توجه داشته باشید که تنها خانه ی اول moving = True را تنظیم می کند
                self.moving = True

                # صدای حرکت را اجرا کن
                self.moveSound.play()

            # انیمیشن را اجرا کن
            animate.start(tile)

    def reset_tile_combined_flag(self):
        """
is_recently_combined را برای هر خانه به مقدار False تنظیم می کند تا برای حرکت بعدی آماده باشند
        """

        for (i, j,) in self.all_cell():
            tile = self.b[i][j]
            if tile:
                tile.is_recently_combined = False

    def can_combine(self, x, y, number):
        """
 بررسی می کند که آیا خانه ی بعدی معتبر،  دارای مقدار و عدد آن با عدد خانه ی مورد نظر یکی است                 
 آرگومان ها:         
x: اندیس ردیف خانه ی مقابل
y: اندیس ستون خانه ی مقابل
number: عدد خانه ی فعلی
مقادیر بازگشتی:         
True, False: آیا امکان ترکیب وجود دارد؟ 
        """
        return self.valid_cell(x, y) and self.b[x][y] is not None and self.b[x][y].number == number

    def on_touch_up(self, touch):
        """
        این متد به event on_touch_up پاسخ می دهد
آرگومان ها:
touch: اطلاعات مربوط به تاچ
مقادیر بازگشتی:
tuple: عددی بین (-0.1, 1.0)
        """

        # از وکتور برای تبدیل gesture  به واحد قابل فهم ریاضی استفاده می کنیم تا به راحتی با متد
        # move تعامل داشته باشیم
        # مکان نهایی – مکان ابتدایی تاچ
        v = Vector(touch.pos) - Vector(touch.opos)

        # اگر اندازه تاچ بیشتر از 20 نقطه باشد یعنی حرکتی انجام شده است در غیر این صورت  حرکتی انجام نشده است
        if v.length() < 20:
            return

        # اگر اندازه ی xها بیشتر از اندازه ی yها باشد یعنی حرکتی در جهت محور xها انجام شده است
        if abs(v.x) > abs(v.y):
            v.y = 0

        # اگر اندازه ی yها بیشتر از اندازه ی xها باشد یعنی حرکتی در جهت محور yها انجام شده است
        elif abs(v.x) < abs(v.y):
            v.x = 0

        # توجه داشته باشید که تنها در یک جهت می توان حرکت کرد
        # در نهایت مقدار ها را نرمال کن یعنی اگر عددی 0.8 است آن را به 1.0 تبدیل کن
        self.move(*v.normalize())

    def win(self):
        """
        پیام موفقیت در یک popup نمایش داده می شود و آهنگ پس زمینه اگر در حال پخش باشد متوقف
می شود و در نهایت آهنگ موفقیت پخش خواهد شد
        """

        title = 'پیروزی!'
        message = 'شما با موفقیت به 2048 رسیدید'
        btn_go_on = {'text': 'ادامه دادن', 'type': 'InfoButton', 'on_press': 'app.stop_win_sound'}
        popup = dynamic_popup(title, message, [btn_go_on])

        # اگر آهنگ پس زمینه در حال اجرا باشد آنگاه آن را متوقف کن و هنگامی که popup بسته شد آهنگ پس زمینه را اجرا کن
        if self.is_stopped_background_music is False:
            self.toggle_music()
            popup.on_dismiss = self.toggle_music

        # در اینجا آهنگ برد را لود می کنیم
        self.winSound = SoundLoader.load('data/audio/win.mp3')

        # آهنگ موفقیت را اجرا کن
        self.winSound.play()

    def lose(self, dt=None):
        """
        پیام شکست در یک popup نمایش داده می شود و آهنگ پس زمینه اگر در حال پخش باشد متوقف
می شود و امتیاز در صورت فراهم بودن شرایط به صورت آنلاین ثبت می شود  و در نهایت آهنگ شکست
 پخش خواهد شد
آرگومان ها:
dt: اطلاعات ارسالی توسط متد schedule_once
        """

        title = 'شکست!'
        message = 'تمام موفقيت هاي عظيم بر پايه ي شكست بنا شده اند'
        btn_go_on = {'text': 'شروع مجدد', 'type': 'InfoButton', 'on_press': 'app.stop_lose_sound'}
        popup = dynamic_popup(title, message, [btn_go_on])
        self.save_score()

        # اگر آهنگ پس زمینه در حال اجرا باشد آنگاه آن را متوقف کن و هنگامی که popup بسته شد آهنگ پس زمینه را اجرا کن
        if self.is_stopped_background_music is False:
            self.toggle_music()
            popup.on_dismiss = self.toggle_music

        # در اینجا آهنگ موفقیت را لود می کنیم
        self.loseSound = SoundLoader.load('data/audio/lose.mp3')

        # آهنگ شکست را اجرا کن
        self.loseSound.play()

    def stop_win_sound(self):
        """
        اگر آهنگ موفقیت در حال اجرا باشد آن را متوقف می کند
        """
        if self.winSound.state is 'play':
            self.winSound.stop()

    def stop_lose_sound(self):
        """
        اگر آهنگ شکست در حال اجرا باشد آن را متوقف می کند
        """
        if self.loseSound.state is 'play':
            self.loseSound.stop()

    def is_deadlock(self):
        """
        بررسی می کند که آیا بن بست رخ داده است یا نه
مقادیر بازگشتی:
True, False: آیا بن بست رخ داده است؟
        """

        for (x, y) in self.all_cell():

            # اگر هیچ ترکیبی پیدا نشود به بن بست برخورد کرده ایم در غیر این صورت بن بست رخ نداده است
            if self.can_combine(x + 1, y, self.b[x][y].number) or self.can_combine(x, y + 1, self.b[x][y].number):
                return False

        return True

    def store_cell_data(self):
        """
        عددهای خانه ها را همراه با سایر مشخصات بازی نظیر بهترین امتیاز، امتیاز فعلی، آیا به 2048
رسیده ایم، آیا آهنگ پس زمینه متوقف شده است را در یک فایل json ذخیره می کند
        """

        # تنها شماره ی خانه ها را ذخیره می کنیم
        data = [[self.b[i][j].number if self.b[i][j] else None
                 for j in range(NUMBER_OF_CELL)] for i in range(NUMBER_OF_CELL)]

        # اطلاعات بازی را در فایل json‌ذخیره می کنیم
        self.storage.put('storage', cells=data, score=self.score, best_score=self.best_score,
                         win_flag=self.win_flag, is_stopped_background_music=self.is_stopped_background_music)

    def restore_cell_data(self):
        """
در صورتی که مخزن ذخیره سازی وجود داشته باشد اطلاعات اجرای قبلی را لود می کند(اطلاعات
خانه ها، وضعیت اجرای آهنگ پس زمینه، امتیاز اجرای قبلی، بهترین امتیاز و …) در غیر اینصورت از صفر شروع می کند
        """

        # تعداد خانه های هر سطر را در صورت نیاز تنظیم میکند
        global NUMBER_OF_CELL

        # layout ریشه را برمی گرداند
        root = GameApp.get_running_app().root

        # اگر layout ریشه لود شده باشد
        if root:

            # می توان دکمه ی شروع/متوقف کردن آهنگ پس زمینه را برای تغییر آیکون آن دریافت کرد
            btn_sound = root.ids.btn_sound

            # اگر مخزن ذخیره سازی وجود داشته باشد
            if self.storage.exists('storage'):

                # گرفتن اطلاعات خانه ها
                data = self.storage.get('storage')['cells']

                # تنظیم تعداد خانه های هر سطر بر اساس طول خانه های ذخیره شده
                NUMBER_OF_CELL = len(data[0])

                # با استفاده از عددهای ذخیره شده و اندیس x , y هر خانه، خانه ها را ایجاد کرده و آن ها را به
# بورد اضافه می کنیم                                
                for (x, y) in self.all_cell():
                    if data[x][y]:
                        self.add_tile(x, y, number=data[x][y])

                # گرفتن امتیاز اجرای قبلی
                self.score = self.storage.get('storage')['score']

                # گرفتن بهترین امتیاز
                self.best_score = self.storage.get('storage')['best_score']

                # گرفتن وضعیت موفقیت(آیا به 2048 رسیده ایم)
                self.win_flag = self.storage.get('storage')['win_flag']

                # گرفتن وضعیت اجرای آهنگ پس زمینه (آیا آهنگ پس زمینه در اجرای قبلی متوقف شده است یا نه)
                self.is_stopped_background_music = self.storage.get('storage')['is_stopped_background_music']

                # در شرط های زیر آیکون دکمه ی آهنگ تنظیم می شود
                if self.is_stopped_background_music:
                    self.backgroundSound.stop()
                    btn_sound.source = 'data/img/stop-sound.png'
                else:
                    btn_sound.source = 'data/img/sound.png'

                # اگر اطلاعات از مخزن داده لود شده باشد پس بازی از صفر شروع نشده است
                self.is_current_session = False
            else:

                # بازی از صفر شروع شود
                self.reset()

    @staticmethod
    def show_reset_popup():
        """
یک popup را نمایش می دهد که از کاربر می پرسد آیا بازی reset شود یا خیر؟
        """
        title = 'شروع مجدد برنامه'
        message = 'آیا می خواهید از اول شروع کنید؟'
        btn_no = {'text': 'خیر', 'type': 'InfoButton'}
        btn_yes = {'text': 'بله', 'type': 'DangerButton', 'on_press': 'app.reset_board'}
        dynamic_popup(title, message, [btn_no, btn_yes])

    def toggle_music(self):
        """
        اگر آهنگ پس زمینه در حال اجرا باشد آن را متوقف می کند و اگر متوقف شده باشد آن را اجرا می کند
        """

        # از آنجایی که می خواهیم هنگام توقف آهنگ پس زمینه، آیکون دکمه ی  آن نیز تغییر کند و بلعکس
# باید به دکمه ی توقف و شروع آهنگ پس زمینه دسترسی داشته باشیم               
        btn_sound = GameApp.get_running_app().root.ids.btn_sound

        # اگر آهنگ  پس زمینه در حال اجرا باشد آن را متوقف کن و آیکون دکمه ی توقف/شروع را به آیکون توقف تنظیم کن
        if self.backgroundSound.state is 'play':
            self.is_stopped_background_music = True
            self.backgroundSound.stop()
            btn_sound.source = 'data/img/stop-sound.png'

        # اگر آهنگ  پس زمینه متوقف شده باشد آن را اجرا کن و آیکون دکمه ی توقف/شروع را به آیکون اجرا تنظیم کن
        else:
            self.is_stopped_background_music = False
            self.backgroundSound.play()

            #  هنگام اجرای دوباره ی آهنگ، اگر میزان بلندی صدا را تنظیم نکنیم، آهنگ  با مقدار پیش فرض اجرا می شود
            self.backgroundSound.volume = VOLUME
            btn_sound.source = 'data/img/sound.png'

    def save_score(self):
        """
        در صورتی که تمامی شرایط ثبت امتیاز فراهم باشد، امتیاز به صورت آنلاین ثبت خواهد شد
شرایط:
1. اینترنت وصل باشد
2. کاربر دارای ایمیل باشد
3. توکن اعتبارسنجی کاربر دریافت شده باشد
4. کاربر در یک اجرا و از صفر شروع کرده باشد یعنی اجرای فعلی، ادامه ی اجرا یا اجراهای قبلی
نباشد(امنیتی) 
        """

        # کاربر دارای ایمیل باشد
        app = GameApp.get_running_app()
        if app.email:

            # کاربر دارای توکن اعتبارسنجی باشد
            if TOKEN:

                # کاربر در یک اجرا و از صفر شروع کرده باشد یعنی اجرای فعلی، ادامه ی اجرا یا اجراهای قبلی
                # نباشد
                if self.is_current_session:

                    # ارسال توکن اعتبار سنجی به عنوان header درخواست
                    headers = {'Authorization': ' '.join(['Token', TOKEN])}
                    headers.update(HEADERS)

                    # ارسال در خواست ثبت امتیاز
                    post_request(SERVER.format('game/info'), {'pts': self.score}, headers, self.save_score_success,
                                 self.error, self.failure)
                else:
                    title = 'خطای اعتبار سنجی امتیاز'
                    message = 'از آنجایی که برنامه را بسته و سپس دوباره  اجرا \n نموده اید، امتیاز شما ثبت نخواهد شد'\
                              'فقط امتیازاتی \n ثبت خواهند شد که در یک اجرا و از صفر شروع شده باشند'
                    btn_go_on = {'text': 'ادامه دادن', 'type': 'InfoButton'}
                    dynamic_popup(title, message, [btn_go_on])

            # کاربر دارای ایمیل باشد اما توکن اعتبارسنجی را دریافت نکرده است که یکی از دلایل آن قطع بودن اینترنت است
            else:
                app = GameApp.get_running_app()
                app.user_registration(error_func=self.error)

    @staticmethod
    def save_score_success(self, req, result):
        """
        بعد از ارسال موفقیت آمیز امتیاز به سرور،  این متد فراخوانی می شود
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        pass

    @staticmethod
    def error(self, req, result):
        """
        در صورتی که در  ارسال امتیاز به سرور با مشکلاتی نظیر قطع بودن اینترنت، پایین آمدن سرور
مواجه شویم،  این متد فراخوانی می شود. در این حالت یک popup حاوی خطا یا خطاها ایجاد شده
به کاربر نمایش داده می شوند.
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        
        title = 'خطای ارتباط با سرور'
        message = 'ارتباط با سرور امکان پذیر نیست\n'\
                  'اینترنت خود را بررسی کنید\n'\
                  'پس از رفع مشکل، روی ثبت امتیاز کلیک کنید\n'\
                  'در غیر اینصورت امتیاز شما ثبت نخواهد شد'
        btn_connection = {'text': 'ثبت امتیاز', 'type': 'InfoButton', 'on_press': 'app.save_score'}
        btn_no_matter = {'text': 'مهم نیست', 'type': 'DangerButton'}
        dynamic_popup(title, message, [btn_connection, btn_no_matter])

    @staticmethod
    def failure(req, result):
        """
        در صورتی که در  ارسال امتیاز به سرور با مشکلاتی نظیر نامعتبر بودن اطلاعات ارسالی، خطا در سرور
مواجه شویم،  این متد فراخوانی می شود.
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        pass

    # هنگام تغییر مکان یا تغییر اندازه صفحه متد resize را فراخوانی کن
    on_size = resize
    on_pos = resize


class Tile(Widget):
    """
    این کلاس حاوی اطلاعات مربوط به هر خانه است
عدد، رنگ، اندازه، مکان، …  هر خانه در این کلاس تنظیم می شوند
    """

    # اندازه فونت عدد هر خانه را نگه می دارد
    font_size = NumericProperty(14)

    # عدد هر خانه را نگه می دارد
    number = NumericProperty(2)

    # رنگ هر خانه را متناسب با عدد آن خانه نگه می دارد
    color = ListProperty(get_color_from_hex(TILE_COLORS[2]))

    # رنگ عدد خانه را نگه می دارد
    number_color = ListProperty(get_color_from_hex('FFFFFF'))

    # آیا این خانه در حرکت فعلی با خانه ای دیگر ترکیب شده است
    is_recently_combined = False

    def __init__(self, number=2, **kwargs):
        super(Tile, self).__init__(**kwargs)
        self.number = number
        self.font_size = self.width * FONT_SIZE_COEFFICIENT

        # رنگ خانه را براساس عدد آن بروزرسانی می کند
        self.update_color()

    def update_color(self):
        """
        براساس عدد خانه مورد نظر، رنگ متناسب به آن را به آن اختصاص می دهد
        """

        self.color = get_color_from_hex(TILE_COLORS[self.number])

    def resize(self, pos, size):
        """
اندازه و مکان هر خانه را هنگام تغییر اندازه صفحه بروز رسانی می کند
آرگومان ها:
pos: مکان جدید خانه
size: اندازه ی جدید خانهد
        """

        self.size = size
        self.pos = pos

        # از آنجایی که اندازه ی فونت به اندازه ی عرض خانه وابسته است پس نیاز است اندازه ی فونت
       # نیز به روز رسانی شود. این وابستگی بدان دلیل است که هنگام کوچک کردن پنجره، اعداد از
       # خانه هایشان بیرون نیایند
        self.font_size = FONT_SIZE_COEFFICIENT * self.width

    def move_animate(self, pos):
        """
        خانه را با انیمیشن به مقصد جدید هدایت می کند
آرگومان ها:
pos: مکان جدید
مقادیر بازگشتی:
شی انیمیشن حرکت
        """
        animate = Animation(pos=pos, duration=0.15, transition='out_sine')
        return animate

    def new_tile_animate(self, pos, size, font_size, duration=0.05):
        """
        خانه جدید را با انیمیشن به صفحه اضافه  می کند یا خانه ای که قرار است حذف شود را با انیمیشن از صفحه خارج می کند
آرگومان ها:
pos: مکان انتهایی خانه
size: اندازه نهایی خانه
font_size: اندازه نهایی فونت عدد خانه
duration: زمان انیمیشن
مقادیر بازگشتی:
شی انیمشین 
        """
        
        self.font_size = font_size
        animate = Animation(pos=pos, size=size, duration=duration, transition='out_sine')
        animate.start(self)
        return animate


class BaseButton(Button):
    """
    این کلاس در بردارنده ی اطلاعات عمومی تمامی دکمه های به کار رفته در این برنامه است
    """

    def __init__(self, **kwargs):
        super(BaseButton, self).__init__(**kwargs)

        # صدای تاچ دکمه را لود می کند
        self.touchSound = SoundLoader.load('data/audio/touch.mp3')


class ScrollContainer(GridLayout):
    """
 در واقع ظرف در بر گیرنده المان هایی است که در صورت زیاد شدن تعداد المان ها، این ظرف اسکرول خواهد خورد.
    """

    def __init__(self, **kwargs):
        super(ScrollContainer, self).__init__(**kwargs)

        # در صورتی که ظرف اندازه نداشته باشد اسکرول نخواهد خورد
        self.bind(minimum_height=self.setter('height'))


class GameApp(App):
    """
    نقطه ی شروع و پایان برنامه در این کلاس قرار دارد
    """

    # settings پیش فرض kivy را غیر فعال کن. در موبایل با زدن دکمه ی setting گوشی و در ویندوز و لینوکس و مک با زدن دکمه ی F1
    # این صفحه پدیدار می شود
    use_kivy_settings = False

    # در بردارنده ی modal نمایش دهنده ی نفرات برتر است
    score_modal = None

    # ایمیل کاربر
    email = None

    # رمز عبور کاربر
    password = 'Strong Password'

    def on_start(self):
        """
هنگامی که برنامه شروع شد این متد اجرا می شود
بررسی: هنگام شروع برنامه اگر مخزن داده وجود داشته باشد لود می شود(البته لود داده ها در این متد انجام نمی پذیرد)
اگر کاربر ایمیل داشته باشد در سرور ثبت نام شده و توکن اعتبار سنجی باز گردانده می شود
اگر کاربر قبلا ثبت نام کرده باشد توکن او بازگردانده می شود
        """

        self.on_run()

        # FIXED: اگر این متد در یک thread دیگر اجرا شما زمان لود ابتدای برنامه کم می شود
        Clock.schedule_once(self.user_registration)

    def on_stop(self):
        """
        هنگامی که برنامه بسته می شود این متد فراخوانی می شود
در اینجا متد ذخیره کننده ی  اطلاعات مربوط به کلاس board، فراخوانی می شود تا اطلاعات را برای اجرای بعدی ذخیره کند
        """

        board = self.root.ids.board
        board.store_cell_data()

    def on_pause(self):
        """
هنگامی که برنامه pause  می شود  مثلا زنگ زده می شود و به برنامه ی پاسخ دادن به زنگ سویچ می شود. این متد فراخوانی می شود.
اگر این متد فراخوانی نشود برنامه بسته می شود
مقادیر بازگشتی:
True, False: آیا بعد از بازگشت از سوییچ این برنامه به حالت اجرا بر گردد
        """

        return True

    def on_resume(self):
        """
        هنگامی که برنامه pause  می شود:  مثلا زنگ زده می شود و به برنامه ی پاسخ دادن به زنگ سویچ
می شود. هنگام بازگشت از سویچ این متد فراخوانی می شود.
        """
        pass

    def on_run(self):
        """
        متد پاسخ دادن به فشردن کلیدهای کیبورد پنجره ی برنامه را به متد board.on_key_down تنظیم می کند
        """
        board = self.root.ids.board
        Window.bind(on_key_down=board.on_key_down)

    @staticmethod
    def rate_app():
        """
        این متد شرایط امتیاز دهی به برنامه را فراهم می کند
از آنجایی که از کافه بازار استفاده می کنیم پنل امتیاز دهی کافه بازار را نمایش می دهد
اگر کافه بازار روی دستگاه کاربر نصب نباشد از مرورگر وب استفاده می کند
        """

        # در 4 خط کد زیر activity و intent و Uri مورد نیاز برای امتیاز دادن به برنامه را دریافت
        # می کنیم
        # توجه داشته باشد که این ها متعلق به اندروید هستند و ما با استفاده از pyjnius به آن ها
    # دسترسی پیدا کردیم        
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)

        # نام این بسته را بر می گرداند مثلا com.rastalgroup.kivy2048
        package_name = currentActivity.getPackageName()

        # از مارکت بازار استفاده می کنیم
        market_url = 'bazaar://details?id={0}'.format(package_name)

        # از آدرس بازار استفاده می کنیم
        web_url = 'https://cafebazaar.ir/app/{0}/'.format(package_name)

        try:

            # اگر برنامه ی بازار روی دستگاه نصب باشد
            intent = Intent()
            intent.setAction(Intent.ACTION_EDIT)
            intent.setData(Uri.parse(market_url))
            intent.setPackage('com.farsitel.bazaar')
            currentActivity.startActivity(intent)
        except Exception:

            # اگر برنامه ی بازار روی دستگاه نصب نباشد
            intent = Intent()
            intent.setAction(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(web_url))
            currentActivity.startActivity(intent)

    def user_registration(self, dt=None, error_func=None):
        """
 این متد ابتدا بررسی می کند که کاربر ایمیل دارد. اگر داشته باشد ابتدا درخواستی را جهت
دریافت توکن اعتبار سنجی به سرور ارسال می کند در صورت نداشتن توکن اعتبار سنجی  او را در
سرور ثبت نام می کند و اگر ایمیل نداشته باشد یک پیام حاوی اطلاعات مورد نیاز برای ثبت امتیاز
به صورت آنلاین، به او نمایش داده می شود
آرگومان ها:
error_func: متد یا تابعی که هنگام بروز خطا در ارتباط با سرور،  فراخوانی می شود
        """

        # اگر ایمیل کاربر قبلا گرفته شده است دیگر نیازی به اجرای دوباره ی تابع get_user_email نیست
        if self.email is None:
            self.email = get_user_email()

        # اگر کاربر ایمیل داشته باشد
        if self.email:

            # FIXED: ابتدا توکن او را بدست بیاورد در صورت خطا او را ثبت نام کند

            # یک درخواست جهت دریافت توکن به سرور ارسال می شود
            post_request(SERVER.format('token-auth'), {'username': self.email, 'password': self.password}, HEADERS,
                         self.get_token_success, error_func if error_func else self.error, self.failure)

        # اگر کاربر ایمیل نداشته باشد        
        else:
            title = 'خطای حساب کاربری'
            message = 'هیچ ایمیلی برای حساب کاربری شما یافت نشد\n'\
                      'در صورتی که ایمیلی برای گوشی شما تنظیم نشود\n'\
                      ' امتیازات شما به صورت آنلاین ثبت نخواهد شد'
            btn_exit = {'text': 'خروج و بررسی', 'type': 'InfoButton', 'on_press': 'app.close'}
            btn_offline = {'text': 'آفلاین بازی می کنم', 'type': 'DangerButton'}
            dynamic_popup(title, message, [btn_exit, btn_offline])

    def register_user_success(self, req, result):
        """
         بعد از ارسال موفقیت آمیز اطلاعات کاربر،  این متد فراخوانی می شود
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """

        # بعد از ثبت نام کاربر بایستی توکن او بازگردانده شود پس یک درخواست جهت دریافت توکن به سرور ارسال می شود
        post_request(SERVER.format('token-auth'), {'username': self.email, 'password': self.password}, HEADERS,
                     self.get_token_success, self.error, self.failure)

    def show_score_table(self, time='day'):
        """
        نفرات برتر همراه با امتیازات آن ها را نمایش می دهد
این نمایش بسته به آرگومان time متفاوت است برای هر مقدار این آرگومان،  درخواستی به سرور
جهت دریافت اطلاعات مربوطه ارسال می شود
آرگومان ها:
time: سه مقدار می گیرد day نفرات برتر روز جاری را نمایش می دهد week نفرات برتر هفته ی
جاری را نمایش می دهد month نفرات برتر ماه جاری را نمایش می دهد
        """

        # آدرس درخواست را متناسب با آرگومان time تنظیم می کند
        url = 'game/{0}'.format(time)

        # در خواست به سرور ارسال می شود
        get_request(SERVER.format(url), HEADERS, self.get_score_data, self.score_table_error, self.failure)

# اگر modal نمایش اطلاعات مقداردهی نشده باشد  یا پنجره ی آن باز  نباشد              
        if not self.score_modal or not self.score_modal._window:
            self.score_modal = Factory.ScoreTable()
            self.score_modal.open()
        else:
            self.score_modal.ids.top_score_list.clear_widgets()
            loading = Factory.Loading()
            self.score_modal.ids.top_score_list.add_widget(loading)

    @staticmethod
    def get_token_success(req, result):
        """
        بعد از ارسال موفقیت آمیز اطلاعات کاربر برای گرفتن توکن اعتبارسنجی،  این متد فراخوانی
می شود
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """

        global TOKEN

        # مقدار TOKEN عمومی را به مقدار token بازگشتی تنظیم می کنیم
        TOKEN = result['token']

    def get_score_data(self, req, result):
        """
         بعد از درخواست موفقیت آمیز نفرات برتر،  این متد فراخوانی می شود
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """

        self.add_score_to_score_table(result)

    def add_score_to_score_table(self, data):
        """
        لیست اطلاعات نفرات برتر را دریافت می کند و آن ها تک تک به modal نمایش نفرات برتر اضافه
می کند
آرگومان ها:
data: لیستی از دیکشنری هاست که هر دیکشنری حاوی اطلاعات هر کاربر است
        """

        # ابتدا اطلاعات قبلی را پاک کن
        self.score_modal.ids.top_score_list.clear_widgets()
        for (index, item,) in enumerate(data, start=1):

            # یک شی از UserScoreRow را ایجادکن
            row = Factory.UserScoreRow()

            # در سه خط زیر اطلاعات کاربر را به شی ایجاد شده اضافه کن
            row.index = index
            row.user = self.get_user_name(item['user'])
            row.pts = item['pts']

            # شی UserScoreRow ایجاد شده را به پنل modal نمایش نفرات برتر اضافه کن
            self.score_modal.ids.top_score_list.add_widget(row)

    def get_user_name(self, email):
        """
        در این متد یک ایمیل را دریافت می کنیم و domain.com@  انتهای آن را حذف می کنیم سپس علامت های نقطه گذاری  را با space جایگزین می کنیم
        آرگومان ها:
email: رشته ای با فرمت ایمیل
مقادیر بازگشتی:
name: ایمیل ویرایش شده براساس توضیحات بالا
        """
        import re
        import string

        # پیدا کردن اندیس @
        index = email.index('@')

        # domain.com@ را از ایمیل حذف کن
        email = email[:index]

        # جایگزین کردن علامت های نقطه گذاری با space
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        return regex.sub(' ', email)

    @staticmethod
    def error(req, result):
        """
در صورتی که در  ارتباط با سرور  با مشکلاتی نظیر قطع بودن اینترنت، پایین آمدن سرور
مواجه شویم،  این متد فراخوانی می شود. در این حالت یک popup حاوی خطا یا خطاها ایجاد شده
به کاربر نمایش داده می شوند.
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        title = 'خطای ارتباط با سرور'
        message = 'ارتباط با سرور امکان پذیر نیست\nاینترنت خود را بررسی کنید'
        btn_exit = {'text': 'خروج و بررسی', 'type': 'InfoButton', 'on_press': 'app.close'}
        btn_offline = {'text': 'آفلاین بازی می کنم', 'type': 'DangerButton'}
        dynamic_popup(title, message, [btn_exit, btn_offline])

    @staticmethod
    def score_table_error(req, result):
        """
        در صورتی که در درخواست اطلاعات نفرات برتر  با مشکلاتی نظیر قطع بودن اینترنت، پایین آمدن سرور
مواجه شویم،  این متد فراخوانی می شود. در این حالت یک popup حاوی خطا یا خطاها ایجاد شده
به کاربر نمایش داده می شوند.
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        title = 'خطای ارتباط با سرور'
        message = 'ارتباط با سرور امکان پذیر نیست\nاینترنت خود را بررسی کنید'
        btn_go_on = {'text': 'ادامه دادن', 'type': 'InfoButton'}
        dynamic_popup(title, message, [btn_go_on])

    def failure(self, req, result):
        """
 در صورتی که در ارسال اطلاعات کاربر به سرور با مشکلاتی نظیر نامعتبر بودن اطلاعات ارسالی،
خطا در سرور،  مواجه شویم،  این متد فراخوانی می شود. از آنجایی که در سرور تنها یک استثنا
را برای این امر در نظر گرفته ایم پس این خطا بدان معنی است که این کاربر قبلا ثبت نام نکرده
است. بنابراین در اینجا درخواستی را برای ثبت نام کاربر به سرور ارسال می کنیم
آرگومان ها:
req: شی درخواست ارسالی
result: مقادیر بازگشتی درخواست
        """
        # او را در سرور ثبت نام کن
        post_request(SERVER.format('user/info'), {'email': self.email}, HEADERS,
                     self.register_user_success, self.error, self.failure)

# چهار متدی که در ادامه آمده اند برای دسترسی آسان به عملیات مورد نیاز تابع
# dynamic_popup است این متد ها توابع موجود در کلاس Board را فراخوانی می کنند

    def reset_board(self, btn):
        """
        متد reset کلاس Board  را فراخوانی می کند
آرگومان ها:
btn: دکمه ای که هنگام کلیک بر روی آن، این متد فراخوانی شده است
        """

        # شی popup ای که این دکمه روی آن قرار دارد را برمی گرداند
        popup = btn.parent.parent.parent.parent.parent
        self.root.ids.board.reset()
        popup.dismiss()

    def stop_win_sound(self, btn):
        """
        متد stop_win_sound کلاس Board  را فراخوانی می کند
آرگومان ها:
btn: دکمه ای که هنگام کلیک بر روی آن، این متد فراخوانی شده است
        """

        # شی popup ای که این دکمه روی آن قرار دارد را برمی گرداند
        popup = btn.parent.parent.parent.parent.parent
        self.root.ids.board.stop_win_sound()
        popup.dismiss()

    def stop_lose_sound(self, btn):
        """
        متد stop_lose_sound کلاس Board  را فراخوانی می کند
آرگومان ها:
btn: دکمه ای که هنگام کلیک بر روی آن، این متد فراخوانی شده است
        """

        # شی popup ای که این دکمه روی آن قرار دارد را برمی گرداند
        popup = btn.parent.parent.parent.parent.parent
        self.root.ids.board.stop_lose_sound()
        self.reset_board(btn)

    def save_score(self, btn):
        """
        متد save_score کلاس Board  را فراخوانی می کند
آرگومان ها:
btn: دکمه ای که هنگام کلیک بر روی آن، این متد فراخوانی شده است
        """

        # شی popup ای که این دکمه روی آن قرار دارد را برمی گرداند
        popup = btn.parent.parent.parent.parent.parent
        self.root.ids.board.save_score()
        popup.dismiss()

    @staticmethod
    def close(*args):
        """
        برنامه را می بندد
        آرگومان ها:
        args: اطلاعات ارسالی توسط متد on_press
        """

        exit(0)


if __name__ == '__main__':

    # رنگ پیش فرض پنجره را تغییر می دهد
    Window.clearcolor = get_color_from_hex('607d8b')

    # فونت دلخواه Roboto را اضافه می کند
    LabelBase.register('Roboto', fn_regular='data/font/Roboto-Thin.ttf',
                       fn_bold='data/font/Roboto-Medium.ttf')

    # فونت دلخواه Tabassom را اضافه می کند
    LabelBase.register('Tabassom', fn_regular='data/font/tabassom.ttf')

    # نقطه ی شروع برنامه
    GameApp().run()
