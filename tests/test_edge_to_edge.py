import sys
import types

import pytest

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager

import main
import ui.edge_to_edge as edge_to_edge
from ui.edge_to_edge import SafeAreaStrip, draw_edge_to_edge, safe_area
from ui.expanding_popup import SCREEN_MARGIN, ExpandingPopup

SHORT_EDGES = 1
FLAG_TRANSLUCENT_STATUS = 0x04000000
FLAG_TRANSLUCENT_NAVIGATION = 0x08000000
FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS = 0x80000000
SYSTEM_BARS = 0b0111
DISPLAY_CUTOUT = 0b10000000


@pytest.fixture(autouse=True)
def reset_safe_area():
    yield
    Window.unbind(on_resize=edge_to_edge._on_window_resize)
    edge_to_edge._following = False
    safe_area.top = 0
    safe_area.bottom = 0


class FakeWindow:
    # Records the calls made on the app's Android window, and which thread they were made on #
    def __init__(self, phone):
        self.phone = phone
        self.calls = []
        self.attrs = types.SimpleNamespace(layoutInDisplayCutoutMode=0)
        self.decor = types.SimpleNamespace(getRootWindowInsets=lambda: phone.insets)

    def getAttributes(self):
        return self.attrs

    def getDecorView(self):
        return self.decor

    def __getattr__(self, name):
        def call(*args):
            if name in self.phone.failing:
                raise RuntimeError(name + " failed")
            self.calls.append((name, *args, "ui thread" if self.phone.on_ui_thread else "kivy thread"))
        return call


class FakeInsets:
    def __init__(self, top, bottom):
        self.top, self.bottom = top, bottom
        self.masks = []

    def getInsets(self, mask):
        self.masks.append(mask)
        return types.SimpleNamespace(top=self.top, bottom=self.bottom)


class FakePhone:
    def __init__(self, sdk):
        self.sdk = sdk
        self.failing = set()
        self.on_ui_thread = False
        self.insets = FakeInsets(top=136, bottom=63)
        self.window = FakeWindow(self)

    def run_on_ui_thread(self, f):
        def run(*args):
            self.on_ui_thread = True
            try:
                return f(*args)
            finally:
                self.on_ui_thread = False
        return run

    def autoclass(self, name):
        return {
            "android.os.Build$VERSION": types.SimpleNamespace(SDK_INT=self.sdk),
            "android.graphics.Color": types.SimpleNamespace(TRANSPARENT=0),
            "android.view.WindowManager$LayoutParams": types.SimpleNamespace(
                LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES=SHORT_EDGES,
                FLAG_TRANSLUCENT_STATUS=FLAG_TRANSLUCENT_STATUS,
                FLAG_TRANSLUCENT_NAVIGATION=FLAG_TRANSLUCENT_NAVIGATION,
                FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS=FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS,
            ),
            "android.view.WindowInsets$Type": types.SimpleNamespace(
                systemBars=lambda: SYSTEM_BARS,
                displayCutout=lambda: DISPLAY_CUTOUT,
            ),
        }[name]


def fake_phone(monkeypatch, sdk=35):
    phone = FakePhone(sdk)
    activity = types.SimpleNamespace(getWindow=lambda: phone.window)
    monkeypatch.setitem(sys.modules, "jnius", types.SimpleNamespace(autoclass=phone.autoclass))
    monkeypatch.setitem(sys.modules, "android", types.SimpleNamespace(mActivity=activity))
    monkeypatch.setitem(sys.modules, "android.runnable", types.SimpleNamespace(run_on_ui_thread=phone.run_on_ui_thread))
    monkeypatch.setattr(edge_to_edge, "platform", "android")
    return phone


## TURNING IT ON ##

def test_does_nothing_off_android(monkeypatch, kivy_window):
    monkeypatch.setattr(edge_to_edge, "platform", "linux")
    monkeypatch.setitem(sys.modules, "jnius", None)  # Importing it would raise #

    draw_edge_to_edge()
    Clock.tick()

    assert (safe_area.top, safe_area.bottom) == (0, 0)


def test_leaves_android_10_and_older_alone(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch, sdk=29)

    draw_edge_to_edge()
    Clock.tick()

    assert phone.window.calls == []
    assert (safe_area.top, safe_area.bottom) == (0, 0)


def test_draws_behind_the_bars_and_camera_on_the_ui_thread(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch)

    draw_edge_to_edge()

    assert phone.window.attrs.layoutInDisplayCutoutMode == SHORT_EDGES
    assert phone.window.calls == [
        ("setAttributes", phone.window.attrs, "ui thread"),
        ("clearFlags", FLAG_TRANSLUCENT_STATUS | FLAG_TRANSLUCENT_NAVIGATION, "ui thread"),
        ("addFlags", FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS, "ui thread"),
        ("setStatusBarColor", 0, "ui thread"),
        ("setNavigationBarColor", 0, "ui thread"),
        ("setNavigationBarContrastEnforced", False, "ui thread"),
        ("setDecorFitsSystemWindows", False, "ui thread"),
    ]


def test_safe_area_is_read_on_kivys_thread_once_it_is_on(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch)

    draw_edge_to_edge()
    assert (safe_area.top, safe_area.bottom) == (0, 0)  # Not from Android's UI thread #

    Clock.tick()

    assert (safe_area.top, safe_area.bottom) == (136, 63)
    assert set(phone.insets.masks) == {SYSTEM_BARS | DISPLAY_CUTOUT}


def test_a_failed_step_keeps_the_normal_status_bar(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch)
    phone.failing.add("setStatusBarColor")

    draw_edge_to_edge()  # Logged, not raised #
    Clock.tick()

    assert "setDecorFitsSystemWindows" not in [call[0] for call in phone.window.calls]
    assert (safe_area.top, safe_area.bottom) == (0, 0)


def test_safe_area_waits_for_the_window_to_be_laid_out(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch)
    phone.insets = None

    draw_edge_to_edge()
    Clock.tick()
    assert (safe_area.top, safe_area.bottom) == (0, 0)

    phone.insets = FakeInsets(top=136, bottom=63)
    Window.dispatch("on_resize", *Window.size)  # Laying it out behind the bars resizes it #

    assert (safe_area.top, safe_area.bottom) == (136, 63)


def test_turning_it_on_twice_follows_resizes_once(monkeypatch, kivy_window):
    phone = fake_phone(monkeypatch)
    draw_edge_to_edge()
    draw_edge_to_edge()
    Clock.tick()
    phone.insets.masks.clear()

    Window.dispatch("on_resize", *Window.size)

    assert len(phone.insets.masks) == 1


## STRIPS ##

def test_strips_follow_their_side_of_the_safe_area(kivy_window):
    top = SafeAreaStrip("top", (1, 0, 0, 1))
    bottom = SafeAreaStrip("bottom", (0, 1, 0, 1))
    assert (top.height, bottom.height) == (0, 0)

    safe_area.top = 136
    safe_area.bottom = 63

    assert (top.height, bottom.height) == (136, 63)
    assert top.size_hint_y is None and bottom.size_hint_y is None


def test_strip_made_after_the_safe_area_is_known_starts_at_its_size(kivy_window):
    safe_area.top = 136

    assert SafeAreaStrip("top", (1, 0, 0, 1)).height == 136


def test_app_keeps_its_screens_between_the_strips(tmp_path, kivy_window, monkeypatch):
    calls = []
    monkeypatch.setattr(main, "draw_edge_to_edge", lambda: calls.append(True))
    app = main.BudgetApp()
    app._user_data_dir = str(tmp_path)

    root = app.build()
    app.on_start()
    Window.unbind(on_keyboard=app.on_back_key)

    top, screens, bottom = reversed(root.children)
    assert isinstance(top, SafeAreaStrip) and isinstance(bottom, SafeAreaStrip)
    assert screens is app.screen_manager and isinstance(screens, ScreenManager)
    assert calls == [True]

    safe_area.top = 136
    safe_area.bottom = 63
    root.size = (1080, 2424)
    root.do_layout()

    assert screens.top == top.y == 2424 - 136
    assert screens.y == bottom.top == 63


def test_strip_bar_runs_across_its_middle(kivy_window):
    strip = SafeAreaStrip("bottom", (0, 1, 0, 1), bar_color=(1, 1, 1, 1), bar_height=9)
    strip.width = 1080

    safe_area.bottom = 63

    assert tuple(strip.bar.size) == (1080, 9)
    assert strip.bar.pos[0] == strip.x
    assert strip.bar.pos[1] + 9 / 2 == pytest.approx(strip.center_y)


def test_strip_bar_is_hidden_until_edge_to_edge_is_on(kivy_window):
    strip = SafeAreaStrip("bottom", (0, 1, 0, 1), bar_color=(1, 1, 1, 1), bar_height=9)

    assert strip.bar.size[1] == 0


def test_strip_bar_never_sticks_out_of_a_short_strip(kivy_window):
    strip = SafeAreaStrip("bottom", (0, 1, 0, 1), bar_color=(1, 1, 1, 1), bar_height=9)

    safe_area.bottom = 5

    assert strip.bar.size[1] == 5
    assert strip.bar.pos[1] == strip.y


@pytest.mark.skip(reason="Gesture handle bar is temporarily commented out in main.py")
def test_gesture_handle_sits_on_a_divider_thin_light_gray_bar(tmp_path, kivy_window):
    from kivy.graphics import Color
    from kivy.metrics import dp

    app = main.BudgetApp()
    app._user_data_dir = str(tmp_path)
    bottom = app.build().children[0]

    strip_color, bar_color = [i.rgba for i in bottom.canvas.before.children if isinstance(i, Color)]
    assert isinstance(bottom, SafeAreaStrip)
    assert tuple(strip_color) == pytest.approx((0.125, 0.259, 0.188, 1))   # Forest Green #
    assert tuple(bar_color) == pytest.approx((0.8, 0.8, 0.8, 1))           # Light Gray, like the dividers #
    assert bottom.bar_height == dp(9)


## POPUPS ##

@pytest.fixture
def close_popups(kivy_window):
    yield
    for widget in list(kivy_window.children):
        if isinstance(widget, ModalView):
            widget.dismiss(animation=False)


def open_popup(height):
    popup = ExpandingPopup(title="Test", content=Label())
    popup.open(animation=False)
    popup.height = height   # Resizing is what lines it up, as it does when its content is laid out #
    for _ in range(5):
        Clock.tick()
    return popup


def test_tall_popup_stays_below_the_status_bar(kivy_window, close_popups):
    safe_area.top = 40

    popup = open_popup(kivy_window.height * 0.95)

    assert popup.top <= kivy_window.height - 40


def test_popup_stays_above_the_gesture_bar(kivy_window, close_popups):
    safe_area.bottom = 30

    popup = open_popup(kivy_window.height * 0.95)

    assert popup.y >= 30 + SCREEN_MARGIN - 0.01
