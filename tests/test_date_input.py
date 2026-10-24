from datetime import date, timedelta

import pytest

from kivy.clock import Clock
from kivy.tests.common import UnitTestTouch

import ui.date_input as date_input
from ui.date_input import DateInput


## PARSING ##

def test_blank_means_no_day(kivy_window):
    assert DateInput().parse_day() is None
    assert DateInput(text="   ").parse_day() is None


def test_day_shows_in_readable_format_and_parses_back(kivy_window):
    box = DateInput(day=date(2026, 10, 5))

    assert box.text == "Oct 05, 2026"
    assert box.parse_day() == date(2026, 10, 5)


def test_typed_iso_date_is_accepted(kivy_window):
    assert DateInput(text="2026-10-05").parse_day() == date(2026, 10, 5)


def test_text_that_isnt_a_date_is_rejected(kivy_window):
    with pytest.raises(ValueError, match="valid date"):
        DateInput(text="yesterday").parse_day()


def test_future_day_is_rejected(kivy_window):
    with pytest.raises(ValueError, match="future"):
        DateInput(day=date.today() + timedelta(days=1)).parse_day()


## CLEARING THE FIELD ##

def test_cleared_date_reverts_to_what_it_was(kivy_window):
    box = DateInput(day=date(2026, 10, 15))

    box.focus = True
    box.text = ""
    box.focus = False

    assert box.parse_day() == date(2026, 10, 15)


def test_new_date_replaces_the_old_one_and_is_kept_when_cleared_later(kivy_window):
    box = DateInput(day=date(2026, 10, 15))

    box.focus = True
    box.text = "2026-10-17"
    box.focus = False
    box.focus = True
    box.text = "  "
    box.focus = False

    assert box.parse_day() == date(2026, 10, 17)


def test_field_that_started_blank_stays_blank(kivy_window):
    box = DateInput()

    box.focus = True
    box.focus = False

    assert box.parse_day() is None


## ANDROID DATE PICKER ##

@pytest.fixture
def fake_android(monkeypatch):
    shown = []
    monkeypatch.setattr(date_input, "platform", "android")
    monkeypatch.setattr(date_input, "_DateSetListener", lambda callback: callback, raising=False)
    monkeypatch.setattr(date_input, "_show_date_picker", lambda initial, listener: shown.append((initial, listener)), raising=False)
    return shown


@pytest.fixture
def placed_box(kivy_window):
    box = DateInput(size_hint=(None, None), size=(200, 40), pos=(0, 0))
    kivy_window.add_widget(box)
    yield box
    kivy_window.remove_widget(box)


def test_tap_on_android_opens_picker_on_today_instead_of_keyboard(placed_box, fake_android):
    touch = UnitTestTouch(100, 20)
    touch.touch_down()
    touch.touch_up()

    assert [initial for initial, _ in fake_android] == [date.today()]
    assert placed_box.focus is False


def test_picker_opens_on_the_day_already_entered(placed_box, fake_android):
    placed_box.set_day(date(2026, 9, 3))

    placed_box.open_date_picker()

    assert fake_android[0][0] == date(2026, 9, 3)


def test_picking_a_day_fills_the_field(placed_box, fake_android):
    placed_box.open_date_picker()
    _, on_date_set = fake_android[0]

    on_date_set(2026, 9, 3)
    Clock.tick()  # The picker answers on Android's UI thread; the text is set on Kivy's #

    assert placed_box.parse_day() == date(2026, 9, 3)


def test_tap_on_desktop_is_handled_as_typing(placed_box, fake_android, monkeypatch):
    from kivy.uix.textinput import TextInput

    monkeypatch.setattr(date_input, "platform", "linux")
    monkeypatch.setattr(TextInput, "on_touch_down", lambda self, touch: "typing")

    assert placed_box.on_touch_down(UnitTestTouch(100, 20)) == "typing"
    assert fake_android == []
