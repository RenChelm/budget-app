import json
from datetime import datetime

import pytest

from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView

from ui.category_edit_popup import CategoryEditPopup, PALETTE
from ui.name_select_popup import (
    NameSelectPopup, add_entry, edit_entry, find_entry, matching_entries, name_color,
)
from ui.text_box import TextBox

RED, BLUE = list(PALETTE[0]), list(PALETTE[5])


def entry(name, color=None):
    return {"name": name, "color": color}


def entries(*names):
    # Names with no color, or (name, color) pairs #
    return [entry(*n) if isinstance(n, tuple) else entry(n) for n in names]


class FakeApp:
    def __init__(self, tmp_path, retailers=(), brands=()):
        self.saved_names = {"retailer": entries(*retailers), "brand": entries(*brands)}
        self.names_files = {"retailer": str(tmp_path / "retailers.json"), "brand": str(tmp_path / "brands.json")}
        self.saved_amounts = []
        self.transactions_file = str(tmp_path / "transactions.json")
        self.saved_colors = []
        self.colors_file = str(tmp_path / "colors.json")
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


def open_new_popup(popup, monkeypatch):
    # Taps New and hands back the Add popup it opened #
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    popup.new_btn.dispatch("on_release")
    return opened[0]


def open_edit_popup(popup, monkeypatch, name, button="Edit"):
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    row_button(popup, name, button).dispatch("on_release")
    return opened[0]


def names_of(app, kind="retailer"):
    return [e["name"] for e in app.saved_names[kind]]


def hint_texts(popup):
    return [w.text for w in popup.list_layout.children if isinstance(w, Label) and not isinstance(w, Button)]


def saved_file(path):
    with open(path) as f:
        return json.load(f)


def saved_names_in(path):
    return [e["name"] for e in saved_file(path)]


## NAME LISTS ##

def test_find_entry_ignores_case():
    assert find_entry(entries("Walmart", "Target"), "walmart") == entry("Walmart")
    assert find_entry(entries("Walmart"), "Wal") is None


def test_name_color_is_the_saved_color_or_none():
    saved = entries(("Walmart", BLUE), "Target")

    assert name_color(saved, "WALMART") == BLUE
    assert name_color(saved, "Target") is None
    assert name_color(saved, "Aldi") is None        # No longer in the list
    assert name_color(saved, None) is None


def test_matching_entries_finds_any_part_ignoring_case_a_to_z():
    saved = entries("Walmart", "target", "Costco", "Trader Joe's")
    names = lambda found: [e["name"] for e in found]

    assert names(matching_entries(saved, "")) == ["Costco", "target", "Trader Joe's", "Walmart"]
    assert names(matching_entries(saved, "  TAR ")) == ["target"]
    assert names(matching_entries(saved, "t")) == ["Costco", "target", "Trader Joe's", "Walmart"]
    assert matching_entries(saved, "zzz") == []


def test_add_entry_keeps_the_list_a_to_z_with_its_color():
    assert add_entry(entries("Costco", "Walmart"), "Target", RED) == ([entry("Costco"), entry("Target", RED), entry("Walmart")], "Target")


def test_add_entry_reuses_one_saved_in_a_different_case_as_it_is():
    assert add_entry(entries(("Walmart", BLUE)), "WALMART", RED) == ([entry("Walmart", BLUE)], "Walmart")


def test_edit_entry_renames_and_recolors_and_keeps_a_to_z():
    assert edit_entry(entries("Costco", "Walmrat"), "Walmrat", "Aldi", RED) == ([entry("Aldi", RED), entry("Costco")], "Aldi")


def test_edit_entry_can_change_just_the_color_or_just_the_case():
    assert edit_entry(entries(("walmart", BLUE)), "walmart", "walmart", RED) == ([entry("walmart", RED)], "walmart")
    assert edit_entry(entries(("walmart", BLUE)), "walmart", "Walmart", BLUE) == ([entry("Walmart", BLUE)], "Walmart")


def test_edit_entry_onto_another_saved_name_merges_them_with_the_color_just_picked():
    assert edit_entry(entries(("Walmart", BLUE), "Walmrat"), "Walmrat", "walmart", RED) == ([entry("Walmart", RED)], "Walmart")


## PICKER ##

def test_picker_starts_empty_with_no_default_names(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path))

    assert listed_names(popup) == []
    assert hint_texts(popup) == []


@pytest.mark.parametrize("kind, title, hint, clear, new", [
    ("retailer", "Select Retailer/Platform", "Search retailers/platforms", "No Retailer/Platform", "New Retailer/Platform"),
    ("brand", "Select Brand/Creator", "Search brands/creators", "No Brand/Creator", "New Brand/Creator"),
])
def test_both_pickers_have_a_search_bar_and_a_new_button(tmp_path, kivy_window, kind, title, hint, clear, new):
    popup, _, _ = make_picker(FakeApp(tmp_path), kind)

    assert popup.title == title
    assert isinstance(popup.search_input, TextBox)
    assert popup.search_input.hint_text == hint
    assert popup.clear_btn.text == clear
    assert popup.new_btn.text == new


def test_search_bar_is_at_the_top_and_new_is_at_the_bottom(tmp_path, kivy_window):
    # The keyboard covers the bottom of the screen, so what's typed and the closest results stay above it #
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Target"]))

    assert popup.content.children[-1] is popup.search_input
    assert popup.content.children[0] is popup.new_btn


def test_picker_lists_saved_names_a_to_z_with_x_and_edit(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart", "costco", "Target"]))

    assert listed_names(popup) == ["costco", "Target", "Walmart"]
    row = next(row for row in popup.list_layout.children if not isinstance(row, (Button, Label)))
    assert [btn.text for btn in reversed(row.children)][1:] == ["X", "Edit"]


def test_typing_filters_the_list(tmp_path, kivy_window):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart", "Target", "Trader Joe's"]))

    popup.search_input.text = "tra"

    assert listed_names(popup) == ["Trader Joe's"]


@pytest.mark.parametrize("retailers", [["Walmart"], []])
def test_a_search_with_no_matches_says_so(tmp_path, kivy_window, retailers):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=retailers))

    popup.search_input.text = "zzz"

    assert listed_names(popup) == []
    assert hint_texts(popup) == ["No matches"]


def test_the_search_only_searches_and_never_adds_or_picks(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, picked, _ = make_picker(app)

    for text in ("Aldi", "walmart"):
        popup.search_input.text = text
        popup.search_input.dispatch("on_text_validate")

    assert picked == []
    assert names_of(app) == ["Walmart"]


@pytest.mark.parametrize("kind, title", [("retailer", "Add Retailer/Platform"), ("brand", "Add Brand/Creator")])
def test_new_opens_an_add_popup(tmp_path, kivy_window, monkeypatch, kind, title):
    popup, _, _ = make_picker(FakeApp(tmp_path), kind)

    add_popup = open_new_popup(popup, monkeypatch)

    assert add_popup.title == title
    assert add_popup.name_input.text == ""


def test_new_starts_with_what_was_searched_for(tmp_path, kivy_window, monkeypatch):
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmart"]))
    popup.search_input.text = "  Aldi "

    assert open_new_popup(popup, monkeypatch).name_input.text == "Aldi"


def test_adding_saves_the_name_and_picks_it(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, picked, _ = make_picker(app)
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup.name_input.text = "  Aldi "
    add_popup._save()

    assert picked == ["Aldi"]
    assert names_of(app) == ["Aldi", "Walmart"]
    assert saved_names_in(app.names_files["retailer"]) == ["Aldi", "Walmart"]


def test_adding_a_saved_name_in_a_different_case_picks_the_saved_one(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, picked, _ = make_picker(app)
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup.name_input.text = "WALMART"
    add_popup._save()

    assert picked == ["Walmart"]
    assert names_of(app) == ["Walmart"]


def test_retailers_and_brands_are_separate_lists(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup, _, _ = make_picker(app, "brand")
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup.name_input.text = "Lay's"
    add_popup._save()

    assert (names_of(app, "retailer"), names_of(app, "brand")) == (["Walmart"], ["Lay's"])
    assert saved_names_in(app.names_files["brand"]) == ["Lay's"]


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
    assert saved_names_in(app.names_files["retailer"]) == ["Target"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"
    assert picked == []


def test_edit_opens_a_rename_popup_with_the_name_filled_in(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    popup, _, _ = make_picker(FakeApp(tmp_path, retailers=["Walmrat"]))

    row_button(popup, "Walmrat", "Edit").dispatch("on_release")

    assert opened[0].title == "Edit Retailer/Platform"
    assert opened[0].name_input.text == "Walmrat"


def test_renaming_updates_the_list_and_past_transactions(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
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
    assert saved_names_in(app.names_files["retailer"]) == ["Target", "Walmart"]
    assert [entry.get("retailer") for entry in app.saved_amounts] == ["Walmart", "Target", None]
    assert app.saved_amounts[0]["brand"] == "Walmrat"     # Only the retailer list was renamed #
    assert [entry.get("retailer") for entry in saved_file(app.transactions_file)] == ["Walmart", "Target", None]
    assert renamed == [("Walmrat", "Walmart")]
    assert app.update_display_calls == 1


def test_renaming_onto_a_saved_name_merges_them(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Walmart", "Walmrat"])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmrat"}]
    popup, _, renamed = make_picker(app)

    popup._on_edit_save("Walmrat", "WALMART", None)

    assert listed_names(popup) == ["Walmart"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"
    assert renamed == [("Walmrat", "Walmart")]


## COLORS ##

def test_add_and_edit_use_the_category_popup_with_its_colors(tmp_path, kivy_window, monkeypatch):
    popup, _, _ = make_picker(FakeApp(tmp_path, brands=["Lay's"]), "brand")

    add_popup = open_new_popup(popup, monkeypatch)
    edit_popup = open_edit_popup(popup, monkeypatch, "Lay's")

    assert (add_popup.title, edit_popup.title) == ("Add Brand/Creator", "Edit Brand/Creator")
    assert add_popup.name_input.hint_text == "Brand/Creator name"
    assert len(add_popup.swatch_buttons) == len(PALETTE)
    assert add_popup.custom_color_btn.text == "Custom Color"


def test_a_new_name_starts_with_no_color_picked(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path)
    popup = make_manager(app)
    add_popup = open_new_popup(popup, monkeypatch)

    assert add_popup.selected_color is None
    assert all(btn.text == "" for btn in add_popup.swatch_buttons.values())

    add_popup.name_input.text = "Aldi"
    add_popup._save()

    assert app.saved_names["retailer"] == [entry("Aldi")]
    assert saved_file(app.names_files["retailer"]) == [entry("Aldi")]


def test_adding_a_name_with_a_color_saves_the_color(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path)
    popup, picked, _ = make_picker(app)
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup.name_input.text = "Target"
    add_popup._select_color(PALETTE[0])
    add_popup._save()

    assert picked == ["Target"]
    assert saved_file(app.names_files["retailer"]) == [entry("Target", RED)]


def test_listed_names_show_their_color(tmp_path, kivy_window):
    popup = make_manager(FakeApp(tmp_path, retailers=[("Target", RED), "Walmart"]))

    target, walmart = row_button(popup, "Target", "Target"), row_button(popup, "Walmart", "Walmart")

    assert (target.background_normal, list(target.background_color)) == ("", RED)
    assert tuple(target.color) == (1, 1, 1, 1)
    assert walmart.background_normal != ""      # Plain button look


def test_edit_opens_on_the_names_color_and_changing_it_keeps_the_name(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path, retailers=[("Target", RED)])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Target"}]
    popup, _, renamed = make_picker(app)
    edit_popup = open_edit_popup(popup, monkeypatch, "Target")

    assert edit_popup.selected_color == PALETTE[0]

    edit_popup._select_color(PALETTE[5])
    edit_popup._save()

    assert app.saved_names["retailer"] == [entry("Target", BLUE)]
    assert app.saved_amounts[0]["retailer"] == "Target"
    assert list(row_button(popup, "Target", "Target").background_color) == BLUE
    assert renamed == [("Target", "Target")]


def test_a_wheel_color_saved_while_adding_a_name_is_kept_for_categories_too(tmp_path, kivy_window, monkeypatch):
    app = FakeApp(tmp_path)
    popup = make_manager(app, "brand")
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup._on_color_wheel_save([0.8, 0.4, 0.4, 1])

    assert app.saved_colors == [[0.8, 0.4, 0.4, 1]]
    assert add_popup.selected_color == (0.8, 0.4, 0.4, 1)


def test_the_name_box_stays_above_the_keyboard(tmp_path, kivy_window, monkeypatch):
    # Phone keyboards take up to about the bottom half of the screen #
    app = FakeApp(tmp_path)
    app.saved_colors = [[i / 10, 0.2, 0.3, 1] for i in range(8)]
    add_popup = open_new_popup(make_manager(app), monkeypatch)
    monkeypatch.undo()
    add_popup.open(animation=False)
    for _ in range(10):
        Clock.tick()

    assert add_popup._is_open
    assert isinstance(add_popup.name_input, TextBox)
    assert add_popup.top <= kivy_window.height
    assert add_popup.name_input.y > kivy_window.height / 2
    add_popup.dismiss(animation=False)


## MANAGING A LIST (OPENED FROM CUSTOM ON THE MAIN PAGE) ##

def make_manager(app, kind="retailer"):
    return NameSelectPopup(app, kind)


@pytest.mark.parametrize("kind, title, hint, new", [
    ("retailer", "Manage Retailers/Platforms", "Search retailers/platforms", "New Retailer/Platform"),
    ("brand", "Manage Brands/Creators", "Search brands/creators", "New Brand/Creator"),
])
def test_managing_has_its_own_title_and_no_clear_button(tmp_path, kivy_window, kind, title, hint, new):
    popup = make_manager(FakeApp(tmp_path), kind)

    assert popup.title == title
    assert popup.search_input.hint_text == hint
    assert popup.new_btn.text == new
    assert popup.clear_btn is None
    assert not any(getattr(w, "text", "").startswith("No ") for w in popup.content.walk() if isinstance(w, Button))


def test_managing_lists_saved_names_with_x_and_edit(tmp_path, kivy_window):
    popup = make_manager(FakeApp(tmp_path, retailers=["Walmart", "Aldi"]))

    assert listed_names(popup) == ["Aldi", "Walmart"]
    assert row_button(popup, "Walmart", "X") and row_button(popup, "Walmart", "Edit")


@pytest.mark.parametrize("search", ["", "Ald"])
def test_managing_adds_a_name_and_stays_open_for_more(tmp_path, kivy_window, monkeypatch, search):
    app = FakeApp(tmp_path, retailers=["Walmart"])
    popup = make_manager(app)
    popup.open(animation=False)
    popup.search_input.text = search
    add_popup = open_new_popup(popup, monkeypatch)

    add_popup.name_input.text = "  Aldi "
    add_popup._save()

    assert saved_names_in(app.names_files["retailer"]) == ["Aldi", "Walmart"]
    assert popup.search_input.text == ""
    assert listed_names(popup) == ["Aldi", "Walmart"]
    assert popup._is_open


def test_managing_tapping_a_name_renames_it(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    app = FakeApp(tmp_path, retailers=["Walmrat"])
    app.saved_amounts = [{"amount": 5.0, "timestamp": datetime(2026, 10, 1), "retailer": "Walmrat"}]
    popup = make_manager(app)

    row_button(popup, "Walmrat", "Walmrat").dispatch("on_release")
    opened[0].name_input.text = "Walmart"
    opened[0]._save()

    assert opened[0].title == "Edit Retailer/Platform"
    assert listed_names(popup) == ["Walmart"]
    assert app.saved_amounts[0]["retailer"] == "Walmart"


def test_managing_x_removes_the_name(tmp_path, kivy_window):
    app = FakeApp(tmp_path, retailers=["Target", "Walmart"])
    popup = make_manager(app)

    row_button(popup, "Walmart", "X").dispatch("on_release")

    assert listed_names(popup) == ["Target"]
    assert saved_names_in(app.names_files["retailer"]) == ["Target"]
