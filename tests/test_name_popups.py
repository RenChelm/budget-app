import json
from datetime import datetime

import pytest

from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView

from ui.name_edit_popup import NameEditPopup
from ui.name_select_popup import NameSelectPopup, add_name, find_name, matching_names, rename_name
from ui.text_box import TextBox


class FakeApp:
    def __init__(self, tmp_path, retailers=(), brands=()):
        self.saved_names = {"retailer": list(retailers), "brand": list(brands)}
        self.names_files = {"retailer": str(tmp_path / "retailers.json"), "brand": str(tmp_path / "brands.json")}
        self.saved_amounts = []
        self.transactions_file = str(tmp_path / "transactions.json")
        self.update_display_calls = 0

    def update_display(self):
        self.update_display_calls += 1


@pytest.fixture(autouse=True)
def close_popups(kivy_window):
    yield
    for widget in list(kivy_window.children):
        if isinstance(widget, ModalView):
            widget.dismiss(animation=False)


def make_picker(app, kind="retailer"):
    picked, renamed = [], []
    popup = NameSelectPopup(app, kind, on_select=picked.append, on_rename=lambda old, new: renamed.append((old, new)))
    return popup, picked, renamed


def listed_names(popup):
    # The name buttons in the list, top to bottom #
    rows = [row for row in reversed(popup.list_layout.children) if not isinstance(row, (Button, Label))]
    return [row.children[-1].text for row in rows]


def row_button(popup, name, text):
    row = next(row for row in popup.list_layout.children if not isinstance(row, (Button, Label)) and row.children[-1].text == name)
    return next(btn for btn in row.children if btn.text == text)


def saved_file(path):
    with open(path) as f:
        return json.load(f)


## NAME LISTS ##

def test_find_name_ignores_case():
    assert find_name(["Walmart", "Target"], "walmart") == "Walmart"
    assert find_name(["Walmart"], "Wal") is None


def test_matching_names_finds_any_part_ignoring_case_a_to_z():
    names = ["Walmart", "target", "Costco", "Trader Joe's"]

    assert matching_names(names, "") == ["Costco", "target", "Trader Joe's", "Walmart"]
    assert matching_names(names, "  TAR ") == ["target"]
    assert matching_names(names, "t") == ["Costco", "target", "Trader Joe's", "Walmart"]
    assert matching_names(names, "zzz") == []


def test_add_name_keeps_the_list_a_to_z():
    assert add_name(["Costco", "Walmart"], "Target") == (["Costco", "Target", "Walmart"], "Target")


def test_add_name_reuses_one_saved_in_a_different_case():
    assert add_name(["Walmart"], "WALMART") == (["Walmart"], "Walmart")


def test_rename_name_replaces_it_and_keeps_a_to_z():
    assert rename_name(["Costco", "Walmrat"], "Walmrat", "Aldi") == (["Aldi", "Costco"], "Aldi")


def test_rename_name_can_fix_just_the_case():
    assert rename_name(["walmart"], "walmart", "Walmart") == (["Walmart"], "Walmart")


def test_rename_name_onto_another_saved_name_merges_them():
    assert rename_name(["Walmart", "Walmrat"], "Walmrat", "walmart") == (["Walmart"], "Walmart")


## PICKER ##

def test_picker_starts_empty_with_no_default_names(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path))

    assert listed_names(popup) == []
    assert popup.add_btn is None
    labels = [w for w in popup.list_layout.children if isinstance(w, Label) and not isinstance(w, Button)]
    assert [label.text for label in labels] == ["No retailers yet. Type one above to add it."]


@pytest.mark.parametrize("kind, title, hint, clear", [
    ("retailer", "Select Retailer", "Search or add retailer", "No Retailer"),
    ("brand", "Select Brand", "Search or add brand", "No Brand"),
])
def test_both_pickers_have_a_search_bar(tmp_path, kivy_window, kind, title, hint, clear):
    popup, _, _ = make_picker(FakeApp(tmp_path), kind)

    assert popup.title == title
    assert isinstance(popup.search_input, TextBox)
    assert popup.search_input.hint_text == hint
    assert popup.clear_btn.text == clear


def test_search_bar_is_at_the_top_with_the_add_button_right_under_it(tmp_path, kivy_window):
    # The keyboard covers the bottom of the screen, so what's typed and the closest results stay above it #
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Target"]))
    popup.search_input.text = "Tar"

    assert popup.content.children[-1] is popup.search_input
    assert popup.list_layout.children[-1] is popup.add_btn


def test_picker_lists_saved_names_a_to_z_with_x_and_edit(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart", "costco", "Target"]))

    assert listed_names(popup) == ["costco", "Target", "Walmart"]
    row = next(row for row in popup.list_layout.children if not isinstance(row, (Button, Label)))
    assert [btn.text for btn in reversed(row.children)][1:] == ["X", "Edit"]


def test_typing_filters_the_list(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart", "Target", "Trader Joe's"]))

    popup.search_input.text = "tra"

    assert listed_names(popup) == ["Trader Joe's"]


def test_add_button_only_shows_for_a_name_not_saved_yet(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart"]))

    popup.search_input.text = "walmart"
    assert popup.add_btn is None

    popup.search_input.text = "Wal"
    assert popup.add_btn.text == '+ Add "Wal"'

    popup.search_input.text = "   "
    assert popup.add_btn is None


def test_adding_saves_the_name_and_picks_it(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, picked, _ = make_picker(app)
    popup.search_input.text = "  Aldi "

    popup.add_btn.dispatch("on_release")

    assert picked == ["Aldi"]
    assert app.saved_names["retailer"] == ["Aldi", "Walmart"]
    assert saved_file(app.names_files["retailer"]) == ["Aldi", "Walmart"]


def test_retailers_and_brands_are_separate_lists(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, _, _ = make_picker(app, "brand")
    popup.search_input.text = "Lay's"

    popup.add_btn.dispatch("on_release")

    assert app.saved_names == {"retailer": ["Walmart"], "brand": ["Lay's"]}
    assert saved_file(app.names_files["brand"]) == ["Lay's"]


def test_enter_picks_a_saved_name_ignoring_case(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, picked, _ = make_picker(app)
    popup.search_input.text = "WALMART"

    popup.search_input.dispatch("on_text_validate")

    assert picked == ["Walmart"]
    assert app.saved_names["retailer"] == ["Walmart"]


def test_enter_adds_a_new_name(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    popup, picked, _ = make_picker(app)
    popup.search_input.text = "Costco"

    popup.search_input.dispatch("on_text_validate")

    assert picked == ["Costco"]
    assert app.saved_names["retailer"] == ["Costco"]


def test_enter_with_nothing_typed_does_nothing(tmp_path, kivy_window):
    popup, picked, _ = make_picker(FakeApp(tmp_path))

    popup.search_input.dispatch("on_text_validate")

    assert picked == []


def test_tapping_a_name_picks_it(tmp_path, kivy_window):
    popup, picked, _ = make_picker(FakeApp(tmp_path, retailers=["Target", "Walmart"]))

    row_button(popup, "Walmart", "Walmart").dispatch("on_release")

    assert picked == ["Walmart"]


def test_no_retailer_clears_the_pick(tmp_path, kivy_window):
    popup, picked, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart"]))

    popup.clear_btn.dispatch("on_release")

    assert picked == [None]


def test_x_removes_the_name_from_the_list_but_not_from_transactions(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Target", "Walmart"])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmart"}]
    popup, picked, _ = make_picker(app)

    row_button(popup, "Walmart", "X").dispatch("on_release")

    assert listed_names(popup) == ["Target"]
    assert saved_file(app.names_files["retailer"]) == ["Target"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"
    assert picked == []


def test_edit_opens_a_rename_popup_with_the_name_filled_in(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(NameEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmrat"]))

    row_button(popup, "Walmrat", "Edit").dispatch("on_release")

    assert opened[0].title == "Edit Retailer"
    assert opened[0].name_input.text == "Walmrat"


def test_renaming_updates_the_list_and_past_transactions(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(NameEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    app = FakeApp(tmp_path, retailers=["Target", "Walmrat"], brands=["Walmrat"])
    app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmrat", "brand": "Walmrat"},
        {"amount": 7.0, "timestamp": datetime(2026, 10, 2), "retailer": "Target", "brand": None},
        {"amount": 9.0, "timestamp": datetime(2026, 10, 3), "category": None, "note": None},
    ]
    popup, _, renamed = make_picker(app)
    row_button(popup, "Walmrat", "Edit").dispatch("on_release")

    opened[0].name_input.text = " Walmart "
    opened[0]._save()

    assert listed_names(popup) == ["Target", "Walmart"]
    assert saved_file(app.names_files["retailer"]) == ["Target", "Walmart"]
    assert [entry.get("retailer") for entry in app.saved_amounts] == ["Walmart", "Target", None]
    assert app.saved_amounts[0]["brand"] == "Walmrat"     # Only the retailer list was renamed #
    assert [entry.get("retailer") for entry in saved_file(app.transactions_file)] == ["Walmart", "Target", None]
    assert renamed == [("Walmrat", "Walmart")]
    assert app.update_display_calls == 1


def test_renaming_onto_a_saved_name_merges_them(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart", "Walmrat"])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmrat"}]
    popup, _, renamed = make_picker(app)

    popup._on_edit_save("Walmrat", "WALMART")

    assert listed_names(popup) == ["Walmart"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"
    assert renamed == [("Walmrat", "Walmart")]


## RENAME POPUP ##

def test_rename_ignores_a_blank_name(tmp_path, kivy_window):
    saved = []
    popup = NameEditPopup("Brand", "Lay's", on_save=saved.append)
    popup.name_input.text = "   "

    popup._save()

    assert saved == []


def test_rename_sits_high_so_the_keyboard_never_covers_the_name(kivy_window):
    # Phone keyboards take up to about the bottom half of the screen #
    popup = NameEditPopup("Brand", "Lay's", on_save=lambda name: None)
    popup.open(animation=False)
    for _ in range(10):
        Clock.tick()

    assert isinstance(popup.name_input, TextBox)
    assert popup.top <= kivy_window.height
    assert popup.y > kivy_window.height / 2


## MANAGING A LIST (OPENED FROM CUSTOM ON THE MAIN PAGE) ##

def make_manager(app, kind="retailer"):
    return NameSelectPopup(app, kind)


@pytest.mark.parametrize("kind, title, hint", [
    ("retailer", "Manage Retailers", "Search or add retailer"),
    ("brand", "Manage Brands", "Search or add brand"),
])
def test_managing_has_its_own_title_and_no_clear_button(tmp_path, kivy_window, kind, title, hint):
    popup = make_manager(FakeApp(tmp_path), kind)

    assert popup.title == title
    assert popup.search_input.hint_text == hint
    assert popup.clear_btn is None
    assert not any(getattr(w, "text", "").startswith("No ") for w in popup.content.walk() if isinstance(w, Button))


def test_managing_lists_saved_names_with_x_and_edit(tmp_path, kivy_window):
    popup = make_manager(FakeApp(tmp_path, retailers=["Walmart", "Aldi"]))

    assert listed_names(popup) == ["Aldi", "Walmart"]
    assert row_button(popup, "Walmart", "X") and row_button(popup, "Walmart", "Edit")


def test_managing_adds_a_name_and_stays_open_for_more(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup = make_manager(app)
    popup.open(animation=False)
    popup.search_input.text = "  Aldi "

    popup.add_btn.dispatch("on_release")

    assert saved_file(app.names_files["retailer"]) == ["Aldi", "Walmart"]
    assert popup.search_input.text == ""
    assert listed_names(popup) == ["Aldi", "Walmart"]
    assert popup._is_open


def test_managing_enter_adds_a_new_name(tmp_path, kivy_window):
    app = FakeApp(tmp_path)
    popup = make_manager(app, "brand")
    popup.open(animation=False)
    popup.search_input.text = "Lay's"

    popup.search_input.dispatch("on_text_validate")

    assert app.saved_names["brand"] == ["Lay's"]
    assert popup._is_open


def test_managing_enter_on_a_saved_name_does_nothing(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup = make_manager(app)
    popup.open(animation=False)
    popup.search_input.text = "walmart"

    popup.search_input.dispatch("on_text_validate")

    assert app.saved_names["retailer"] == ["Walmart"]
    assert popup.search_input.text == "walmart"
    assert popup._is_open


def test_managing_tapping_a_name_renames_it(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(NameEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    app = FakeApp(tmp_path, retailers=["Walmrat"])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmrat"}]
    popup = make_manager(app)

    row_button(popup, "Walmrat", "Walmrat").dispatch("on_release")
    opened[0].name_input.text = "Walmart"
    opened[0]._save()

    assert opened[0].title == "Edit Retailer"
    assert listed_names(popup) == ["Walmart"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"


def test_managing_x_removes_the_name(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Target", "Walmart"])
    popup = make_manager(app)

    row_button(popup, "Walmart", "X").dispatch("on_release")

    assert listed_names(popup) == ["Target"]
    assert saved_file(app.names_files["retailer"]) == ["Target"]
