import json
from datetime import datetime

from ui.category_select_popup import CategorySelectPopup, DEFAULT_CATEGORIES
from ui.category_edit_popup import CategoryEditPopup, PALETTE, _normalize


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
