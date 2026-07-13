import json
from datetime import datetime

from ui.add_transaction_popup import AddTransactionPopup
from ui.edit_transaction_popup import EditTransactionPopup


class FakeApp:
    def __init__(self, tmp_path):
        self.saved_amounts = []
        self.transactions_file = str(tmp_path / "transactions.json")
        self.selected_category = None
        self.errors = []
        self.update_display_calls = 0

    def show_error(self, message):
        self.errors.append(message)

    def update_display(self):
        self.update_display_calls += 1


## ADD TRANSACTION ##

def test_save_text_appends_valid_entry(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "42.50"
    popup.note_input_box.text = "  groceries  "
    fake_app.selected_category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}

    popup.save_text()

    assert len(fake_app.saved_amounts) == 1
    entry = fake_app.saved_amounts[0]
    assert entry["amount"] == 42.50
    assert entry["note"] == "groceries"
    assert entry["category"] == fake_app.selected_category
    assert fake_app.update_display_calls == 1

    with open(fake_app.transactions_file) as f:
        saved = json.load(f)
    assert len(saved) == 1


def test_save_text_rejects_invalid_amount(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "not-a-number"

    popup.save_text()

    assert fake_app.saved_amounts == []
    assert fake_app.errors == ["Please enter a valid number."]
    assert fake_app.update_display_calls == 0


def test_save_text_blank_note_becomes_none(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "5"
    popup.note_input_box.text = "   "

    popup.save_text()

    assert fake_app.saved_amounts[0]["note"] is None


def test_constructing_popup_clears_previously_selected_category(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.selected_category = {"name": "Stale", "color": [0, 0, 0, 1]}

    AddTransactionPopup(fake_app)

    assert fake_app.selected_category is None


## EDIT TRANSACTION ##

def test_save_edit_updates_amount_note_and_category(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    fake_app.saved_amounts = [
        {"amount": 10.0, "timestamp": datetime.now(), "category": category, "note": "old note"}
    ]
    popup = EditTransactionPopup(fake_app, 0)

    popup.save_edit(0, "25.75", "  new note  ")

    entry = fake_app.saved_amounts[0]
    assert entry["amount"] == 25.75
    assert entry["note"] == "new note"
    assert fake_app.update_display_calls == 1

    with open(fake_app.transactions_file) as f:
        saved = json.load(f)
    assert saved[0]["amount"] == 25.75


def test_save_edit_ignores_invalid_amount(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    fake_app.saved_amounts = [
        {"amount": 10.0, "timestamp": datetime.now(), "category": category, "note": None}
    ]
    popup = EditTransactionPopup(fake_app, 0)

    popup.save_edit(0, "abc", "note")

    assert fake_app.saved_amounts[0]["amount"] == 10.0
    assert fake_app.update_display_calls == 0


def test_save_edit_blank_note_becomes_none(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    category = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    fake_app.saved_amounts = [
        {"amount": 10.0, "timestamp": datetime.now(), "category": category, "note": "old"}
    ]
    popup = EditTransactionPopup(fake_app, 0)

    popup.save_edit(0, "10", "   ")

    assert fake_app.saved_amounts[0]["note"] is None


def test_edit_popup_construction_with_uncategorized_entry(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime.now(), "category": None, "note": None}
    ]

    EditTransactionPopup(fake_app, 0)
