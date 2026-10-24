import pytest

from kivy.tests.common import UnitTestTouch

import ui.text_box as text_box
from ui.text_box import TextBox


@pytest.fixture
def focused_box(kivy_window, monkeypatch):
    # Kivy's own touch handling isn't under test; it needs a fully laid-out box #
    monkeypatch.setattr(text_box.TextInput, "on_touch_down", lambda self, touch: True)

    box = TextBox(size_hint=(None, None), size=(200, 40), pos=(0, 0))
    kivy_window.add_widget(box)
    box.focus = True
    box.focus_changes = []
    box.bind(focus=lambda inst, focused: box.focus_changes.append(focused))
    yield box
    box.focus = False
    kivy_window.remove_widget(box)


def tap(box):
    box.on_touch_down(UnitTestTouch(box.center_x, box.center_y))


def test_tap_on_android_reopens_a_hidden_keyboard(focused_box, monkeypatch):
    monkeypatch.setattr(text_box, "platform", "android")
    monkeypatch.setattr(text_box, "keyboard_visible", lambda: False)

    tap(focused_box)

    assert focused_box.focus_changes == [False, True]
    assert focused_box.focus is True


def test_tap_while_keyboard_is_open_leaves_it_alone(focused_box, monkeypatch):
    monkeypatch.setattr(text_box, "platform", "android")
    monkeypatch.setattr(text_box, "keyboard_visible", lambda: True)

    tap(focused_box)

    assert focused_box.focus_changes == []


def test_tap_on_desktop_leaves_focus_alone(focused_box, monkeypatch):
    monkeypatch.setattr(text_box, "platform", "linux")
    monkeypatch.setattr(text_box, "keyboard_visible", lambda: False)

    tap(focused_box)

    assert focused_box.focus_changes == []


def test_text_boxes_that_open_the_keyboard_all_use_text_box(tmp_path, kivy_window):
    from datetime import datetime
    from types import SimpleNamespace

    from ui.add_transaction_popup import AddTransactionPopup
    from ui.edit_transaction_popup import EditTransactionPopup
    from ui.number_input import NumberInput

    app = SimpleNamespace(
        saved_amounts=[{"amount": 5.0, "timestamp": datetime.now(), "category": None, "note": None}]
    )

    assert issubclass(NumberInput, TextBox)
    assert isinstance(AddTransactionPopup(app).note_input_box, TextBox)
    edit_boxes = [w for w in EditTransactionPopup(app, 0).content.walk() if getattr(w, "hint_text", "") == "Enter Note (Optional)"]
    assert len(edit_boxes) == 1 and isinstance(edit_boxes[0], TextBox)
