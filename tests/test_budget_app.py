import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from kivy.app import App
from kivy.uix.button import Button


@pytest.fixture
def app(tmp_path, kivy_window):
    from main import BudgetApp

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()
    App._running_app = instance
    return instance


def make_entry(amount, timestamp, category=None, note=None):
    return {"amount": amount, "timestamp": timestamp, "category": category, "note": note}


## PERSISTENCE ON STARTUP ##

def test_build_loads_persisted_transactions(tmp_path, kivy_window):
    from main import BudgetApp

    (tmp_path / "transactions.json").write_text(json.dumps([
        {"amount": 9.99, "timestamp": "2026-07-01T12:00:00", "category": None, "note": None}
    ]))

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()

    assert len(instance.saved_amounts) == 1
    assert isinstance(instance.saved_amounts[0]["timestamp"], datetime)
    assert instance.saved_amounts[0]["amount"] == 9.99


def test_build_handles_corrupt_transactions_json(tmp_path, kivy_window):
    from main import BudgetApp

    (tmp_path / "transactions.json").write_text("{not valid json")

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()  # should not raise

    assert instance.saved_amounts == []


def test_build_handles_missing_files(tmp_path, kivy_window):
    from main import BudgetApp

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()  # should not raise

    assert instance.saved_amounts == []
    assert instance.saved_categories == []


## DELETE ENTRY ##

def test_delete_entry_removes_and_persists(app):
    app.saved_amounts = [
        make_entry(10.0, datetime.now()),
        make_entry(20.0, datetime.now()),
    ]

    app.delete_entry(0)

    assert len(app.saved_amounts) == 1
    assert app.saved_amounts[0]["amount"] == 20.0

    with open(app.transactions_file) as f:
        saved = json.load(f)
    assert len(saved) == 1


@pytest.mark.parametrize("bad_index", [-1, 5])
def test_delete_entry_ignores_out_of_range_index(app, bad_index):
    app.saved_amounts = [make_entry(5.0, datetime.now())]

    app.delete_entry(bad_index)

    assert len(app.saved_amounts) == 1


## UPDATE DISPLAY ##

def test_update_display_shows_placeholder_when_empty(app):
    app.saved_amounts = []
    app.update_display()

    assert app.rv.data == [{
        "timestamp_text": "No entries yet.",
        "category_text": "",
        "amount_text": "",
        "note_text": "",
        "index": -1,
        "category_color": [0.30, 0.45, 0.32, 1],
    }]
    assert app.spent_label.text == "Total Spent: $0.00"
    assert app.trans_label.text == "Total Transactions: 0"


def test_update_display_sorts_newest_first_and_formats_rows(app):
    now = datetime(2026, 7, 13, 10, 0)
    food = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    app.saved_amounts = [
        make_entry(5.0, now - timedelta(days=1), category=food),
        make_entry(12.5, now, category=None, note="late lunch"),
    ]

    app.update_display()
    rows = app.rv.data

    assert len(rows) == 2
    assert rows[0]["index"] == 1  # the "now" entry sorts first
    assert rows[0]["category_text"] == "Uncategorized"
    assert rows[0]["amount_text"] == "$12.50"
    assert rows[0]["note_text"] == "late lunch"
    assert rows[1]["index"] == 0
    assert rows[1]["category_text"] == "Food"
    assert rows[1]["category_color"] == food["color"]

    assert app.spent_label.text == "Total Spent: $17.50"
    assert app.trans_label.text == "Total Transactions: 2"


## SELECT CATEGORY ##

def test_select_category_updates_button_and_state(app):
    btn = Button()
    popup = MagicMock()
    category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}

    app.select_category(category, btn, popup)

    assert app.selected_category == category
    assert btn.text == "Food"
    assert list(btn.background_color) == category["color"]
    popup.dismiss.assert_called_once()


def test_select_category_without_button_still_dismisses(app):
    popup = MagicMock()
    category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}

    app.select_category(category, None, popup)

    assert app.selected_category == category
    popup.dismiss.assert_called_once()
