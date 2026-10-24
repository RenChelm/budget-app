import sys
import types

import pytest

import ui.number_input as number_input
from ui.number_input import NumberInput, TYPE_CLASS_NUMBER, TYPE_NUMBER_FLAG_DECIMAL


def test_decimal_input_requests_number_keyboard_and_filters_floats(kivy_window):
    box = NumberInput()

    assert box.input_type == "number"
    assert box.input_filter == "float"
    assert box.multiline is False


def test_whole_number_input_filters_ints(kivy_window):
    box = NumberInput(decimal=False)

    assert box.input_type == "number"
    assert box.input_filter == "int"


@pytest.fixture
def fake_android(monkeypatch):
    calls = []
    android = types.ModuleType("android")
    android.mActivity = types.SimpleNamespace(changeKeyboard=calls.append)
    monkeypatch.setitem(sys.modules, "android", android)
    monkeypatch.setattr(number_input, "platform", "android")
    monkeypatch.setattr(number_input.Clock, "schedule_once", lambda callback, *args: callback(0))
    return calls


def test_focus_on_android_asks_for_the_decimal_number_pad(kivy_window, fake_android):
    box = NumberInput()

    box.on_number_focus(box, True)

    assert fake_android == [TYPE_CLASS_NUMBER | TYPE_NUMBER_FLAG_DECIMAL]


def test_whole_number_input_keeps_plain_number_pad(kivy_window, fake_android):
    box = NumberInput(decimal=False)

    box.on_number_focus(box, True)

    assert fake_android == []


def test_losing_focus_does_not_change_keyboard(kivy_window, fake_android):
    box = NumberInput()

    box.on_number_focus(box, False)

    assert fake_android == []
