import pytest

from kivy.app import App
from kivy.tests.common import UnitTestTouch

from ui.entry_row import EntryRow, SWIPE_LOCK_DISTANCE, SWIPE_OPEN_THRESHOLD


@pytest.fixture
def entry_row(kivy_window):
    row = EntryRow()
    row.pos = (0, 0)
    row.size = (300, 70)
    kivy_window.add_widget(row)
    yield row
    kivy_window.remove_widget(row)


def swipe(start_x, dx, start_y=35):
    """Simulate a single drag-and-release touch on the row."""
    touch = UnitTestTouch(start_x, start_y)
    touch.touch_down()
    touch.touch_move(start_x + dx, start_y)
    touch.touch_up()
    return touch


class ActionSpy:
    def __init__(self, entry_row):
        self.calls = []
        entry_row.on_edit_pressed = lambda inst: self.calls.append("edit")
        entry_row.on_delete_pressed = lambda inst: self.calls.append("delete")


## TEXT / COLOR PROPERTY BINDINGS ##

def test_text_properties_bind_to_labels(entry_row):
    entry_row.timestamp_text = "Jul 13, 10:00 AM"
    entry_row.category_text = "Food"
    entry_row.note_text = "Lunch"
    entry_row.amount_text = "$12.34"

    assert entry_row.content.timestamp_label.text == "Jul 13, 10:00 AM"
    assert entry_row.content.category_label.text == "Food"
    assert entry_row.content.note_label.text == "Lunch"
    assert entry_row.content.amount_label.text == "$12.34"


def test_category_color_changes_label_contrast(entry_row):
    entry_row.category_color = [1, 1, 1, 1]  # white background
    assert list(entry_row.content.category_label.color) == [0, 0, 0, 1]

    entry_row.category_color = [0, 0, 0, 1]  # black background
    assert list(entry_row.content.category_label.color) == [1, 1, 1, 1]


## SWIPE GESTURE ##

def test_drag_updates_swipe_x_live(entry_row):
    touch = UnitTestTouch(200, 35)
    touch.touch_down()
    touch.touch_move(150, 35)  # dx = -50
    assert entry_row.swipe_x == pytest.approx(-50)
    touch.touch_up()


def test_vertical_drag_does_not_swipe(entry_row):
    ActionSpy(entry_row)
    touch = UnitTestTouch(200, 35)
    touch.touch_down()
    touch.touch_move(205, 100)  # mostly vertical movement
    assert entry_row.swipe_x == 0
    touch.touch_up()


def test_small_swipe_snaps_closed_without_triggering_action(entry_row):
    spy = ActionSpy(entry_row)

    swipe(start_x=200, dx=-(SWIPE_LOCK_DISTANCE + 5))  # past lock, short of open threshold

    assert spy.calls == []


def test_swipe_left_past_threshold_triggers_edit(entry_row):
    spy = ActionSpy(entry_row)

    swipe(start_x=250, dx=-(SWIPE_OPEN_THRESHOLD + 20))

    assert spy.calls == ["edit"]


def test_swipe_right_past_threshold_triggers_delete(entry_row):
    spy = ActionSpy(entry_row)

    swipe(start_x=50, dx=(SWIPE_OPEN_THRESHOLD + 20))

    assert spy.calls == ["delete"]


## RESET / REPOSITION ##

def test_reset_swipe_snaps_immediately(entry_row):
    entry_row.swipe_x = 120
    entry_row.reset_swipe()
    assert entry_row.swipe_x == 0


def test_changing_index_resets_swipe(entry_row):
    entry_row.swipe_x = 80
    entry_row.index = 4
    assert entry_row.swipe_x == 0


def test_swipe_x_repositions_content(entry_row):
    entry_row.pos = (10, 20)
    entry_row.swipe_x = 40
    assert entry_row.content.x == 50
    assert entry_row.content.y == 20


## APP CALLBACKS ##

def test_on_edit_pressed_opens_edit_window(entry_row):
    calls = []

    class StubApp:
        def open_edit_window(self, index):
            calls.append(index)

    App._running_app = StubApp()
    entry_row.index = 7
    entry_row.on_edit_pressed(entry_row)

    assert calls == [7]


def test_on_delete_pressed_deletes_entry(entry_row):
    calls = []

    class StubApp:
        def delete_entry(self, index):
            calls.append(index)

    App._running_app = StubApp()
    entry_row.index = 3
    entry_row.on_delete_pressed(entry_row)

    assert calls == [3]
