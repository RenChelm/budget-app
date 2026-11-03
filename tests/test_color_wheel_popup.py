import math
from colorsys import hsv_to_rgb

import pytest

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.tests.common import UnitTestTouch
from kivy.uix.modalview import ModalView

from ui.color_wheel_popup import TEXTURE_SIZE, ColorWheelPopup, position_to_hue_saturation, wheel_pixels


@pytest.fixture(autouse=True)
def close_popups(kivy_window):
    yield
    for widget in list(kivy_window.children):
        if isinstance(widget, ModalView):
            widget.dismiss(animation=False)


def opened_popup(color=(0.3, 0.6, 0.9, 1), on_save=lambda color: None):
    popup = ColorWheelPopup(color, on_save=on_save)
    popup.open(animation=False)
    for _ in range(10):
        Clock.tick()
    return popup


def touch_at(x, y, move_to=None):
    touch = UnitTestTouch(x, y)
    touch.touch_down()
    if move_to is not None:
        touch.touch_move(*move_to)
    touch.touch_up()


def pixel(x, y):
    # RGB of the wheel picture at (x, y), counted from the bottom left #
    i = (y * TEXTURE_SIZE + x) * 3
    return tuple(wheel_pixels()[i:i + 3])


## WHEEL PICTURE ##

def test_angle_is_hue_and_distance_is_saturation():
    assert position_to_hue_saturation(1, 0) == (0, 1)                       # Right edge: red
    assert position_to_hue_saturation(0, 0.5) == pytest.approx((0.25, 0.5))  # Halfway up: lime, half strength
    assert position_to_hue_saturation(-0.5, 0)[0] == pytest.approx(0.5)     # Left: cyan
    assert position_to_hue_saturation(0, -3) == pytest.approx((0.75, 1))     # Past the edge counts as the edge


def test_wheel_picture_is_white_in_the_middle_and_full_color_at_the_edge():
    middle, last = TEXTURE_SIZE // 2, TEXTURE_SIZE - 1

    assert all(c > 245 for c in pixel(middle, middle))
    assert pixel(last, middle)[0] == 255 and max(pixel(last, middle)[1:]) < 20       # Red on the right
    assert pixel(middle, 0)[2] == 255 and max(pixel(middle, 0)[:2]) < 140           # Blue-violet at the bottom


## PICKING ##

def test_opens_on_the_color_it_was_given(kivy_window):
    popup = opened_popup((0.3, 0.6, 0.9, 1))

    assert popup.wheel.color == pytest.approx([0.3, 0.6, 0.9, 1])
    assert popup.brightness.value == pytest.approx(0.9)
    assert popup.preview.text == "#4C99E6"


def test_tapping_the_wheel_picks_hue_and_saturation(kivy_window):
    popup = opened_popup()
    wheel = popup.wheel

    touch_at(wheel.center_x + wheel.radius, wheel.center_y)

    assert wheel.hue == pytest.approx(0, abs=0.01)
    assert wheel.saturation == pytest.approx(1)
    assert popup.preview.text == "#E60000"      # Red, at the brightness it opened with


def test_dragging_follows_the_finger_and_can_run_past_the_edge(kivy_window):
    popup = opened_popup()
    wheel = popup.wheel

    touch_at(wheel.center_x, wheel.center_y, move_to=(wheel.center_x, wheel.center_y - wheel.radius - dp(40)))

    assert wheel.hue == pytest.approx(0.75)
    assert wheel.saturation == 1


def test_tapping_the_middle_picks_white(kivy_window):
    popup = opened_popup((1, 0, 0, 1))
    wheel = popup.wheel

    touch_at(wheel.center_x, wheel.center_y)

    assert wheel.saturation == pytest.approx(0, abs=0.01)
    assert popup.preview.text == "#FFFFFF"


def test_taps_well_outside_the_wheel_are_ignored(kivy_window):
    popup = opened_popup((0.3, 0.6, 0.9, 1))
    wheel = popup.wheel

    touch_at(wheel.center_x + wheel.radius + dp(30), wheel.y + dp(2))

    assert wheel.color == pytest.approx([0.3, 0.6, 0.9, 1])


def test_brightness_dims_the_color_and_the_wheel(kivy_window):
    popup = opened_popup((1, 0, 0, 1))

    popup.brightness.value = 0.5

    assert popup.wheel.color == pytest.approx([0.5, 0, 0, 1])
    assert popup.wheel.tint.rgb == pytest.approx([0.5, 0.5, 0.5])
    assert popup.preview.text == "#800000"


def test_preview_text_stays_readable_on_light_and_dark_colors(kivy_window):
    popup = opened_popup((1, 1, 0.8, 1))
    assert tuple(popup.preview.color) == (0, 0, 0, 1)

    popup.brightness.value = 0.2
    assert tuple(popup.preview.color) == (1, 1, 1, 1)


def test_marker_sits_on_the_picked_spot(kivy_window):
    popup = opened_popup()
    wheel = popup.wheel
    wheel.hue, wheel.saturation = 0.25, 0.5

    x, y = wheel.marker_pos

    assert x == pytest.approx(wheel.center_x)
    assert y == pytest.approx(wheel.center_y + wheel.radius / 2)


## SAVING ##

def test_save_hands_back_the_color_and_closes(kivy_window):
    saved, dismissed = [], []
    popup = opened_popup((1, 0, 0, 1), on_save=saved.append)
    popup.dismiss = lambda *args, **kwargs: dismissed.append(True)
    popup.wheel.hue, popup.wheel.saturation = 1 / 3, 1

    popup._save()

    assert saved == [pytest.approx(list(hsv_to_rgb(1 / 3, 1, 1)) + [1])]
    assert dismissed == [True]


def test_popup_fits_on_a_phone_screen(kivy_window):
    popup = opened_popup()

    assert popup.top <= kivy_window.height
    assert popup.y >= 0
    assert popup.wheel.radius >= dp(100)
