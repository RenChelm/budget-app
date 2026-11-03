import json
import time
from datetime import datetime

import pytest

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.tests.common import UnitTestTouch
from kivy.uix.modalview import ModalView

import ui.advanced_section as advanced_section
from ui.add_transaction_popup import AddTransactionPopup
from ui.advanced_section import AdvancedSection
from ui.edit_transaction_popup import EditTransactionPopup


class FakeApp:
    def __init__(self, tmp_path):
        self.saved_amounts = []
        self.transactions_file = str(tmp_path / "transactions.json")
        self.selected_category = None
        self.errors = []
        self.update_display_calls = 0
        self.shown_weeks = []

    def show_error(self, message):
        self.errors.append(message)

    def update_display(self):
        self.update_display_calls += 1

    def show_week_of(self, moment):
        self.shown_weeks.append(moment)


@pytest.fixture(autouse=True)
def close_popups(kivy_window):
    yield
    for widget in list(kivy_window.children):
        if isinstance(widget, ModalView):
            widget.dismiss(animation=False)


@pytest.fixture
def opened_pickers(monkeypatch):
    # Records which picker would open instead of opening it #
    opened = []

    class FakePicker:
        def __init__(self, app, kind, on_select, on_rename=None):
            self.kind, self.on_select, self.on_rename = kind, on_select, on_rename
            self.on_dismiss = None
            opened.append(self)

        def bind(self, on_dismiss):
            self.on_dismiss = on_dismiss

        def open(self):
            pass

        def dismiss(self):
            self.on_dismiss(self)

    monkeypatch.setattr(advanced_section, "NameSelectPopup", FakePicker)
    return opened


def settle(seconds=0):
    # Runs Kivy's clock so layouts (and, given time, animations) finish #
    end = time.monotonic() + seconds
    while True:
        Clock.tick()
        if time.monotonic() >= end:
            break
        time.sleep(0.01)
    for _ in range(10):
        Clock.tick()


def tap(widget):
    touch = UnitTestTouch(widget.center_x, widget.center_y)
    touch.touch_down()
    touch.touch_up()


def save_button(popup):
    return next(w for w in popup.content.walk() if getattr(w, "text", None) == "Save")


def opened_add_popup(tmp_path):
    popup = AddTransactionPopup(FakeApp(tmp_path))
    popup.open(animation=False)
    settle()
    return popup


## CLOSED BY DEFAULT ##

def test_add_popup_starts_with_advanced_closed(tmp_path, kivy_window):
    popup = AddTransactionPopup(FakeApp(tmp_path))

    assert popup.advanced.expanded is False
    assert popup.advanced.reveal.height == 0
    assert popup.advanced.choices == {"retailer": None, "brand": None}


def test_retailer_and_brand_start_unpicked_with_no_default(tmp_path, kivy_window):
    popup = AddTransactionPopup(FakeApp(tmp_path))

    assert popup.advanced.choice_btns["retailer"].text == "Select Retailer/Platform"
    assert popup.advanced.choice_btns["brand"].text == "Select Brand/Creator"


def test_hidden_retailer_and_brand_cant_be_tapped(tmp_path, kivy_window, opened_pickers):
    popup = opened_add_popup(tmp_path)

    for btn in popup.advanced.choice_btns.values():
        tap(btn)

    assert opened_pickers == []


## OPENING ADVANCED ##

def test_tapping_advanced_slides_retailer_and_brand_open(tmp_path, kivy_window):
    popup = opened_add_popup(tmp_path)

    tap(popup.advanced.toggle_btn)
    settle(advanced_section.OPEN_DURATION + 0.1)

    assert popup.advanced.expanded is True
    assert popup.advanced.reveal.height == popup.advanced.open_height


def test_tapping_advanced_again_closes_it(tmp_path, kivy_window):
    popup = opened_add_popup(tmp_path)

    tap(popup.advanced.toggle_btn)
    settle(advanced_section.OPEN_DURATION + 0.1)
    tap(popup.advanced.toggle_btn)
    settle(advanced_section.OPEN_DURATION + 0.1)

    assert popup.advanced.expanded is False
    assert popup.advanced.reveal.height == 0


def test_opening_advanced_grows_the_popup_downward_only(tmp_path, kivy_window):
    popup = opened_add_popup(tmp_path)
    top, height = popup.top, popup.height

    popup.advanced.set_expanded(True, animate=False)
    settle()

    assert popup.top == pytest.approx(top)
    assert popup.height == pytest.approx(height + popup.advanced.open_height)


def test_retailer_and_brand_open_between_advanced_and_save(tmp_path, kivy_window):
    popup = opened_add_popup(tmp_path)
    popup.advanced.set_expanded(True, animate=False)
    settle()

    toggle, save = popup.advanced.toggle_btn, save_button(popup)
    retailer, brand = popup.advanced.choice_btns["retailer"], popup.advanced.choice_btns["brand"]

    assert toggle.y > retailer.top > retailer.y > brand.top > brand.y > save.top
    assert save.y >= popup.y


def test_open_retailer_and_brand_can_be_tapped(tmp_path, kivy_window, opened_pickers):
    popup = opened_add_popup(tmp_path)
    popup.advanced.set_expanded(True, animate=False)
    settle()

    tap(popup.advanced.choice_btns["retailer"])
    tap(popup.advanced.choice_btns["brand"])

    assert [picker.kind for picker in opened_pickers] == ["retailer", "brand"]


@pytest.mark.parametrize("expanded", [False, True])
def test_save_sits_under_advanced_with_room_to_tap_each(tmp_path, kivy_window, expanded):
    popup = opened_add_popup(tmp_path)
    popup.advanced.set_expanded(expanded, animate=False)
    settle()

    above_save = popup.advanced.choice_btns["brand"] if expanded else popup.advanced.toggle_btn
    save = save_button(popup)

    assert above_save.y - save.top >= dp(16)
    assert save.height >= dp(44) and popup.advanced.toggle_btn.height >= dp(44)


def test_tall_popup_moves_up_instead_of_running_off_the_screen(tmp_path, kivy_window):
    popup = opened_add_popup(tmp_path)
    popup.advanced.set_expanded(True, animate=False)
    popup.advanced.height += kivy_window.height     # Taller than the screen can fit below its usual top #
    settle()

    assert popup.y >= 0


## PICKING ##

def test_picking_shows_the_name_on_its_button(tmp_path, kivy_window):
    section = AdvancedSection(FakeApp(tmp_path))

    section.set_choice("retailer", "Walmart")
    section.set_choice("brand", "Lay's")

    assert section.choice_btns["retailer"].text == "Retailer/Platform: Walmart"
    assert section.choice_btns["brand"].text == "Brand/Creator: Lay's"


def test_picking_no_retailer_clears_it(tmp_path, kivy_window):
    section = AdvancedSection(FakeApp(tmp_path), retailer="Walmart")

    section.set_choice("retailer", None)

    assert section.choices["retailer"] is None
    assert section.choice_btns["retailer"].text == "Select Retailer/Platform"


def test_picker_choice_lands_on_the_right_field(tmp_path, kivy_window, opened_pickers):
    section = AdvancedSection(FakeApp(tmp_path))

    section.open_picker("brand")
    opened_pickers[-1].on_select("Lay's")

    assert section.choices == {"retailer": None, "brand": "Lay's"}


def test_renaming_the_picked_name_keeps_it_picked(tmp_path, kivy_window, opened_pickers):
    section = AdvancedSection(FakeApp(tmp_path), retailer="Walmrat")

    section.open_picker("retailer")
    opened_pickers[-1].on_rename("Walmrat", "Walmart")
    opened_pickers[-1].on_rename("Target", "Tarjay")

    assert section.choices["retailer"] == "Walmart"


def test_picked_names_show_their_color_like_a_category(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    app.saved_names = {"retailer": [{"name": "Target", "color": [0.9, 0.3, 0.3, 1]}], "brand": [{"name": "Lay's", "color": None}]}
    section = AdvancedSection(app, retailer="Target", brand="Lay's")
    retailer_btn, brand_btn = section.choice_btns["retailer"], section.choice_btns["brand"]

    assert (retailer_btn.background_normal, list(retailer_btn.background_color)) == ("", [0.9, 0.3, 0.3, 1])
    assert tuple(retailer_btn.color) == (1, 1, 1, 1)
    assert brand_btn.background_normal != ""        # No color picked: plain button look

    section.set_choice("retailer", None)
    assert retailer_btn.background_normal != ""


def test_a_color_changed_in_the_list_shows_once_it_closes(tmp_path, kivy_window, opened_pickers):
    app = FakeApp(tmp_path)
    app.saved_names = {"retailer": [{"name": "Target", "color": None}], "brand": []}
    section = AdvancedSection(app, retailer="Target")

    section.open_picker("retailer")
    app.saved_names["retailer"] = [{"name": "Target", "color": [0.3, 0.6, 0.9, 1]}]
    opened_pickers[-1].dismiss()

    assert list(section.choice_btns["retailer"].background_color) == [0.3, 0.6, 0.9, 1]


## SAVING ##

def test_add_saves_no_retailer_or_brand_when_none_are_picked(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    popup = AddTransactionPopup(app)
    popup.amount_input_box.text = "5"

    popup.save_text()

    assert app.saved_amounts[0]["retailer"] is None
    assert app.saved_amounts[0]["brand"] is None


def test_add_saves_the_picked_retailer_and_brand(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    popup = AddTransactionPopup(app)
    popup.amount_input_box.text = "4.29"
    popup.advanced.set_choice("retailer", "Walmart")
    popup.advanced.set_choice("brand", "Lay's")

    popup.save_text()

    assert app.saved_amounts[0]["retailer"] == "Walmart"
    assert app.saved_amounts[0]["brand"] == "Lay's"
    with open(app.transactions_file) as f:
        saved = json.load(f)[0]
    assert (saved["retailer"], saved["brand"]) == ("Walmart", "Lay's")


## EDITING ##

def make_entry(**details):
    return {"amount": 4.29, "timestamp": datetime(2026, 10, 20, 12, 0), "category": None, "note": None, **details}


@pytest.mark.parametrize("details, expanded", [
    ({}, False),
    ({"retailer": None, "brand": None}, False),
    ({"retailer": "Walmart", "brand": None}, True),
    ({"retailer": None, "brand": "Lay's"}, True),
])
def test_edit_opens_advanced_only_when_the_transaction_has_a_retailer_or_brand(tmp_path, kivy_window, details, expanded):
    app = FakeApp(tmp_path)
    app.saved_amounts = [make_entry(**details)]

    popup = EditTransactionPopup(app, 0)

    assert popup.advanced.expanded is expanded
    assert popup.advanced.reveal.height == (popup.advanced.open_height if expanded else 0)


def test_edit_shows_the_transactions_retailer_and_brand(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    app.saved_amounts = [make_entry(retailer="Walmart", brand="Lay's")]

    popup = EditTransactionPopup(app, 0)

    assert popup.advanced.choices == {"retailer": "Walmart", "brand": "Lay's"}
    assert popup.advanced.choice_btns["retailer"].text == "Retailer/Platform: Walmart"


def test_edit_opened_with_advanced_sits_where_add_would_after_opening_it(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    app.saved_amounts = [make_entry(retailer="Walmart")]
    add = opened_add_popup(tmp_path)
    add.advanced.set_expanded(True, animate=False)
    settle()

    edit = EditTransactionPopup(app, 0)
    edit.open(animation=False)
    settle()

    assert edit.top == pytest.approx(add.top)
    assert edit.height == pytest.approx(add.height)


def test_edit_saves_changed_and_cleared_details(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    app.saved_amounts = [make_entry(retailer="Walmart", brand="Lay's")]
    popup = EditTransactionPopup(app, 0)
    popup.advanced.set_choice("retailer", "Target")
    popup.advanced.set_choice("brand", None)

    popup.save_edit(0, "4.29", "")

    assert app.saved_amounts[0]["retailer"] == "Target"
    assert app.saved_amounts[0]["brand"] is None


def test_edit_of_an_older_transaction_without_details_saves_none(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    app.saved_amounts = [make_entry()]
    popup = EditTransactionPopup(app, 0)

    popup.save_edit(0, "6", "")

    assert app.saved_amounts[0]["retailer"] is None
    assert app.saved_amounts[0]["brand"] is None
