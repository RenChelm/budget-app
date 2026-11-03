import json
from datetime import datetime

import pytest

from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from ui.category_select_popup import CategorySelectPopup, DEFAULT_CATEGORIES
from ui.category_edit_popup import CategoryEditPopup, PALETTE, _normalize
from ui.color_wheel_popup import ColorWheelPopup
from ui.text_box import TextBox


class FakeApp:
    def __init__(self, tmp_path):
        self.saved_categories = []
        self.saved_amounts = []
        self.categories_file = str(tmp_path / "categories.json")
        self.transactions_file = str(tmp_path / "transactions.json")
        self.selected_category = None
        self.update_display_calls = 0

    def select_category(self, category, category_btn, popup):
        self.selected_category = category
        if category_btn is not None:
            category_btn.text = category["name"]
        popup.dismiss()

    def update_display(self):
        self.update_display_calls += 1


## CATEGORY SELECT POPUP ##

def test_populate_list_shows_saved_and_default_categories(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_categories = [{"name": "Custom", "color": [0.1, 0.2, 0.3, 1]}]

    popup = CategorySelectPopup(fake_app)

    # one row per saved category + one button per default category
    assert len(popup.list_layout.children) == 1 + len(DEFAULT_CATEGORIES)


def listed_categories(popup):
    # Category names in the list top to bottom; saved ones are rows with X and Edit, defaults are lone buttons #
    names = []
    for widget in reversed(popup.list_layout.children):
        if isinstance(widget, Button):
            names.append(widget.text)
        elif not isinstance(widget, Label):
            names.append(widget.children[-1].text)
    return names


def test_search_bar_is_at_the_top_and_new_category_is_at_the_bottom(tmp_path, kivy_window):
    popup = CategorySelectPopup(FakeApp(tmp_path))

    assert isinstance(popup.search_input, TextBox)
    assert popup.search_input.hint_text == "Search categories"
    assert popup.content.children[-1] is popup.search_input
    assert popup.content.children[0].text == "New Category"


def test_search_filters_saved_and_default_categories_ignoring_case(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_categories = [{"name": "Gas", "color": [0.1, 0.2, 0.3, 1]}, {"name": "Takeout", "color": [0.4, 0.5, 0.6, 1]}]
    popup = CategorySelectPopup(fake_app)

    popup.search_input.text = "  OO "
    assert listed_categories(popup) == ["Food", "Home Goods"]

    popup.search_input.text = "t"
    assert listed_categories(popup) == ["Takeout", "Entertainment", "Other"]

    popup.search_input.text = ""
    assert listed_categories(popup) == ["Gas", "Takeout"] + [cat["name"] for cat in DEFAULT_CATEGORIES]


def test_search_with_no_matches_says_so(tmp_path, kivy_window):
    popup = CategorySelectPopup(FakeApp(tmp_path))

    popup.search_input.text = "zzz"

    assert listed_categories(popup) == []
    assert [w.text for w in popup.list_layout.children if isinstance(w, Label)] == ["No matches"]


def test_search_keeps_filtering_after_a_delete(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_categories = [{"name": "Gas", "color": [0.1, 0.2, 0.3, 1]}, {"name": "Gifts", "color": [0.4, 0.5, 0.6, 1]}]
    popup = CategorySelectPopup(fake_app)
    popup.search_input.text = "gas"

    popup._delete_category(fake_app.saved_categories[0])

    assert listed_categories(popup) == []


@pytest.mark.parametrize("search, name", [("", ""), ("  Health ", "Health")])
def test_new_category_starts_with_what_was_searched_for(tmp_path, kivy_window, monkeypatch, search, name):
    opened = []
    monkeypatch.setattr(CategoryEditPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    popup = CategorySelectPopup(FakeApp(tmp_path))
    popup.search_input.text = search

    popup.content.children[0].dispatch("on_release")

    assert opened[0].title == "Add Category"
    assert opened[0].name_input.text == name


def test_delete_category_removes_by_name_and_persists(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_categories = [
        {"name": "Custom", "color": [0.1, 0.2, 0.3, 1]},
        {"name": "Other Custom", "color": [0.4, 0.5, 0.6, 1]},
    ]
    popup = CategorySelectPopup(fake_app)

    popup._delete_category(fake_app.saved_categories[0])

    assert [c["name"] for c in fake_app.saved_categories] == ["Other Custom"]
    with open(fake_app.categories_file) as f:
        saved = json.load(f)
    assert [c["name"] for c in saved] == ["Other Custom"]


def test_on_add_save_inserts_and_selects_category(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = CategorySelectPopup(fake_app)
    new_category = {"name": "Health", "color": [0.2, 0.7, 0.9, 1]}

    popup._on_add_save(new_category, None)

    assert fake_app.saved_categories[0] == new_category
    assert fake_app.selected_category == new_category
    with open(fake_app.categories_file) as f:
        saved = json.load(f)
    assert saved[0]["name"] == "Health"


def test_on_edit_save_updates_category_and_existing_transactions(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    old_category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    fake_app.saved_categories = [old_category]
    fake_app.saved_amounts = [
        {"amount": 10.0, "timestamp": datetime.now(), "category": old_category, "note": None},
    ]
    popup = CategorySelectPopup(fake_app)
    new_category = {"name": "Groceries", "color": [1, 0.6, 0.2, 1]}

    popup._on_edit_save(new_category, old_category)

    assert fake_app.saved_categories == [new_category]
    assert fake_app.saved_amounts[0]["category"] == new_category
    assert fake_app.update_display_calls == 1

    with open(fake_app.categories_file) as f:
        saved_categories = json.load(f)
    assert saved_categories[0]["name"] == "Groceries"


## CATEGORY EDIT POPUP ##

def test_normalize_rounds_color_components():
    assert _normalize((0.30000001, 0.6, 0.9, 1)) == (0.3, 0.6, 0.9, 1)


def test_defaults_to_palette_when_no_existing_category(kivy_window):
    popup = CategoryEditPopup(app=None, on_save=lambda *a: None)
    assert popup.selected_color == PALETTE[5]


def test_matches_existing_category_color_in_palette(kivy_window):
    existing = {"name": "Food", "color": list(PALETTE[2])}
    popup = CategoryEditPopup(app=None, on_save=lambda *a: None, existing_category=existing)
    assert popup.selected_color == PALETTE[2]


def test_select_color_updates_swatch_indicator(kivy_window):
    popup = CategoryEditPopup(app=None, on_save=lambda *a: None)

    popup._select_color(PALETTE[0])

    assert popup.swatch_buttons[PALETTE[0]].text == "X"
    others = [btn.text for color, btn in popup.swatch_buttons.items() if color != PALETTE[0]]
    assert all(t == "" for t in others)


def test_save_calls_callback_with_name_and_color_and_dismisses(kivy_window):
    saved = []
    popup = CategoryEditPopup(app=None, on_save=lambda cat, old: saved.append((cat, old)))
    popup.name_input.text = "  Health  "
    popup._select_color(PALETTE[3])

    popup._save()

    assert saved == [({"name": "Health", "color": list(PALETTE[3])}, None)]


def test_save_ignores_blank_name(kivy_window):
    saved = []
    popup = CategoryEditPopup(app=None, on_save=lambda cat, old: saved.append((cat, old)))
    popup.name_input.text = "   "

    popup._save()

    assert saved == []


## SAVED CUSTOM COLORS ##

class ColorsApp:
    def __init__(self, tmp_path, saved_colors=()):
        self.saved_colors = [list(c) for c in saved_colors]
        self.colors_file = str(tmp_path / "colors.json")


def saved_swatch_colors(popup):
    # Colors of the saved swatches beneath the defaults, in order #
    return [tuple(btn.background_color) for btn in reversed(popup.saved_grid.children) if isinstance(btn, Button)]


def open_color_wheel(popup, monkeypatch):
    opened = []
    monkeypatch.setattr(ColorWheelPopup, "open", lambda self, *args, **kwargs: opened.append(self))
    popup.custom_color_btn.dispatch("on_release")
    return opened[0]


def test_custom_color_button_sits_above_save(kivy_window, tmp_path):
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda *a: None)

    assert popup.custom_color_btn.text == "Custom Color"
    assert popup.content.children[1] is popup.custom_color_btn
    assert popup.content.children[0].text == "Save"


def test_no_saved_colors_shows_just_the_defaults(kivy_window, tmp_path):
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda *a: None)

    assert popup.saved_scroll.parent is None
    assert len(popup.swatch_buttons) == len(PALETTE)


def test_saved_colors_show_beneath_the_defaults(kivy_window, tmp_path):
    saved = [(0.1, 0.3, 0.35, 1), (0.95, 0.85, 0.7, 1)]
    popup = CategoryEditPopup(ColorsApp(tmp_path, saved), on_save=lambda *a: None)
    children = list(reversed(popup.content.children))

    assert saved_swatch_colors(popup) == saved
    assert children.index(popup.saved_scroll) == children.index(popup.custom_color_btn) - 1
    assert isinstance(children[children.index(popup.saved_scroll) - 1], GridLayout)


@pytest.mark.parametrize("count", [1, 3, 5])
def test_saved_swatches_are_the_same_size_as_the_defaults(kivy_window, tmp_path, count):
    popup = CategoryEditPopup(ColorsApp(tmp_path, [(i / 10, 0.2, 0.3, 1) for i in range(count)]), on_save=lambda *a: None)
    popup.open(animation=False)
    for _ in range(10):
        Clock.tick()

    default_width = popup.swatch_buttons[PALETTE[0]].width
    saved = [btn for btn in popup.saved_grid.children if isinstance(btn, Button)]
    assert len(saved) == count
    assert all(btn.width == pytest.approx(default_width) for btn in saved)
    popup.dismiss(animation=False)


def test_custom_color_opens_the_wheel_on_the_selected_color(kivy_window, tmp_path, monkeypatch):
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda *a: None)
    popup._select_color(PALETTE[0])

    wheel_popup = open_color_wheel(popup, monkeypatch)

    assert wheel_popup.wheel.color == pytest.approx(list(PALETTE[0]))


def test_saving_a_wheel_color_saves_it_newest_first_and_selects_it(kivy_window, tmp_path, monkeypatch):
    app = ColorsApp(tmp_path, [(0.1, 0.3, 0.35, 1)])
    popup = CategoryEditPopup(app, on_save=lambda *a: None)
    wheel_popup = open_color_wheel(popup, monkeypatch)
    wheel_popup.wheel.hue, wheel_popup.wheel.saturation, wheel_popup.brightness.value = 0, 0.5, 0.8

    wheel_popup._save()

    assert app.saved_colors == [[0.8, 0.4, 0.4, 1], [0.1, 0.3, 0.35, 1]]
    with open(app.colors_file) as f:
        assert json.load(f) == app.saved_colors
    assert saved_swatch_colors(popup) == [(0.8, 0.4, 0.4, 1), (0.1, 0.3, 0.35, 1)]
    assert popup.selected_color == (0.8, 0.4, 0.4, 1)
    assert popup.swatch_buttons[(0.8, 0.4, 0.4, 1)].text == "X"
    assert [btn.text for btn in popup.swatch_buttons.values()].count("X") == 1


def test_first_saved_color_adds_the_row_and_grows_the_popup(kivy_window, tmp_path):
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda *a: None)
    popup.open(animation=False)
    height = popup.height

    popup._on_color_wheel_save([0.8, 0.4, 0.4, 1])
    for _ in range(5):
        Clock.tick()

    assert popup.saved_scroll.parent is popup.content
    assert popup.height > height
    popup.dismiss(animation=False)


def test_saving_a_color_that_is_already_a_swatch_just_selects_it(kivy_window, tmp_path):
    app = ColorsApp(tmp_path, [(0.1, 0.3, 0.35, 1)])
    popup = CategoryEditPopup(app, on_save=lambda *a: None)

    popup._on_color_wheel_save([0.1001, 0.3, 0.35, 1])
    assert popup.selected_color == (0.1, 0.3, 0.35, 1)

    popup._on_color_wheel_save(list(PALETTE[3]))
    assert popup.selected_color == PALETTE[3]

    assert app.saved_colors == [[0.1, 0.3, 0.35, 1]]


def test_saved_color_is_used_when_saving_the_category(kivy_window, tmp_path):
    saved = []
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda cat, old: saved.append(cat))
    popup.name_input.text = "Gas"

    popup._on_color_wheel_save([0.8, 0.4, 0.4, 1])
    popup._save()

    assert saved == [{"name": "Gas", "color": [0.8, 0.4, 0.4, 1]}]


def test_editing_a_category_with_a_saved_color_keeps_it_selected(kivy_window, tmp_path):
    existing = {"name": "Gas", "color": [0.95, 0.85, 0.7, 1]}
    popup = CategoryEditPopup(ColorsApp(tmp_path, [(0.95, 0.85, 0.7, 1)]), on_save=lambda *a: None, existing_category=existing)

    assert popup.selected_color == (0.95, 0.85, 0.7, 1)
    assert popup.swatch_buttons[(0.95, 0.85, 0.7, 1)].text == "X"


def test_editing_keeps_a_color_that_is_no_longer_a_swatch(kivy_window, tmp_path):
    saved = []
    existing = {"name": "Gas", "color": [0.95, 0.85, 0.7, 1]}
    popup = CategoryEditPopup(ColorsApp(tmp_path), on_save=lambda cat, old: saved.append(cat), existing_category=existing)

    popup._save()

    assert saved[0]["color"] == [0.95, 0.85, 0.7, 1]


def test_many_saved_colors_scroll_so_the_popup_stays_on_screen(kivy_window, tmp_path):
    many = [(i / 40, 0.2, 0.3, 1) for i in range(40)]
    popup = CategoryEditPopup(ColorsApp(tmp_path, many), on_save=lambda *a: None)
    popup.open(animation=False)
    for _ in range(10):
        Clock.tick()

    assert len(saved_swatch_colors(popup)) == 40
    assert popup.saved_scroll.height < popup.saved_grid.height
    assert popup.top <= kivy_window.height
    assert popup.y >= 0
    popup.dismiss(animation=False)
