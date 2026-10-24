import pytest

from kivy.app import App
from kivy.tests.common import UnitTestTouch

from ui.entry_row import EntryRow


@pytest.fixture
def entry_row(kivy_window):
    row = EntryRow()
    row.size_hint_x = None  # Rows normally stretch to the list's width #
    row.pos = (0, 0)
    row.size = (300, 70)
    kivy_window.add_widget(row)
    yield row
    kivy_window.remove_widget(row)


class StubApp:
    def __init__(self):
        self.edited = []

    def open_edit_window(self, index):
        self.edited.append(index)


## TEXT / COLOR PROPERTY BINDINGS ##

def test_text_properties_bind_to_labels(entry_row):
    entry_row.timestamp_text = "Jul 13, 10:00 AM"
    entry_row.category_text = "Food"
    entry_row.note_text = "Lunch"
    entry_row.amount_text = "$12.34"

    assert entry_row.timestamp_label.text == "Jul 13, 10:00 AM"
    assert entry_row.category_label.text == "Food"
    assert entry_row.note_label.text == "Lunch"
    assert entry_row.amount_label.text == "$12.34"


def test_category_color_changes_label_contrast(entry_row):
    entry_row.category_color = [1, 1, 1, 1]  # white background
    assert list(entry_row.category_label.color) == [0, 0, 0, 1]

    entry_row.category_color = [0, 0, 0, 1]  # black background
    assert list(entry_row.category_label.color) == [1, 1, 1, 1]


def test_background_tracks_full_row(entry_row):
    entry_row.pos = (10, 20)
    entry_row.size = (500, 70)

    assert entry_row.bg_rect.pos == (10, 20)
    assert entry_row.bg_rect.size == (500, 70)


## TAP TO EDIT ##

def test_tap_opens_edit_window_for_its_entry(entry_row):
    App._running_app = stub = StubApp()
    entry_row.index = 7

    touch = UnitTestTouch(150, 35)
    touch.touch_down()
    touch.touch_up()

    assert stub.edited == [7]

