import json
from datetime import date, datetime, timedelta

import pytest

from ui.add_transaction_popup import AddTransactionPopup
from ui.edit_transaction_popup import EditTransactionPopup


class FakeApp:
    def __init__(self, tmp_path):
        self.saved_amounts = []
        self.transactions_file = str(tmp_path / "transactions.json")
        self.selected_category = None
        self.errors = []
        self.update_display_calls = 0
        self.deleted = []
        self.shown_weeks = []

    def show_error(self, message):
        self.errors.append(message)

    def update_display(self):
        self.update_display_calls += 1

    def delete_entry(self, index):
        self.deleted.append(index)

    def show_week_of(self, moment):
        self.shown_weeks.append(moment)


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


def test_blank_date_saves_the_current_time(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "5"

    before = datetime.now()
    popup.save_text()

    timestamp = fake_app.saved_amounts[0]["timestamp"]
    assert before <= timestamp <= datetime.now()
    assert fake_app.shown_weeks == [timestamp]


def test_picked_date_keeps_the_current_time_of_day(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "5"
    picked = date.today() - timedelta(days=9)
    popup.date_input_box.set_day(picked)

    before = datetime.now()
    popup.save_text()

    timestamp = fake_app.saved_amounts[0]["timestamp"]
    assert timestamp.date() == picked
    assert before.time() <= timestamp.time()
    assert fake_app.shown_weeks == [timestamp]


def test_add_popup_prefills_the_given_day(tmp_path, kivy_window):
    popup = AddTransactionPopup(FakeApp(tmp_path), day=date(2026, 10, 1))

    assert popup.date_input_box.parse_day() == date(2026, 10, 1)


@pytest.mark.parametrize("text, error", [
    ("not-a-date", "Please enter a valid date."),
    ((date.today() + timedelta(days=1)).isoformat(), "Date can't be in the future."),
])
def test_save_text_rejects_bad_dates(tmp_path, kivy_window, text, error):
    fake_app = FakeApp(tmp_path)
    popup = AddTransactionPopup(fake_app)
    popup.amount_input_box.text = "5"
    popup.date_input_box.text = text

    popup.save_text()

    assert fake_app.saved_amounts == []
    assert fake_app.errors == [error]


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


def test_edit_popup_shows_the_entry_date(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime(2026, 9, 3, 18, 45), "category": None, "note": None}
    ]

    popup = EditTransactionPopup(fake_app, 0)

    assert popup.date_input_box.parse_day() == date(2026, 9, 3)


def test_save_edit_changes_date_and_keeps_time_of_day(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime(2026, 9, 3, 18, 45), "category": None, "note": None}
    ]
    popup = EditTransactionPopup(fake_app, 0)
    popup.date_input_box.set_day(date(2026, 8, 30))

    popup.save_edit(0, "5", "")

    assert fake_app.saved_amounts[0]["timestamp"] == datetime(2026, 8, 30, 18, 45)
    with open(fake_app.transactions_file) as f:
        assert json.load(f)[0]["timestamp"] == "2026-08-30 18:45:00"


def test_save_edit_blank_date_keeps_original_timestamp(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    original = datetime(2026, 9, 3, 18, 45)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": original, "category": None, "note": None}
    ]
    popup = EditTransactionPopup(fake_app, 0)
    popup.date_input_box.text = ""

    popup.save_edit(0, "5", "")

    assert fake_app.saved_amounts[0]["timestamp"] == original


def test_save_edit_rejects_invalid_date(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    original = datetime(2026, 9, 3, 18, 45)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": original, "category": None, "note": None}
    ]
    popup = EditTransactionPopup(fake_app, 0)
    popup.date_input_box.text = "someday"

    popup.save_edit(0, "7", "")

    assert fake_app.saved_amounts[0] == {"amount": 5.0, "timestamp": original, "category": None, "note": None}
    assert fake_app.errors == ["Please enter a valid date."]
    assert fake_app.update_display_calls == 0


def test_edit_popup_construction_with_uncategorized_entry(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime.now(), "category": None, "note": None}
    ]

    EditTransactionPopup(fake_app, 0)


def test_edit_popup_delete_button_deletes_entry(tmp_path, kivy_window):
    from kivy.uix.button import Button

    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime.now(), "category": None, "note": None}
    ]
    popup = EditTransactionPopup(fake_app, 0)

    delete_btn = next(w for w in popup.content.walk() if isinstance(w, Button) and w.text == "Delete")
    delete_btn.dispatch("on_release")

    assert fake_app.deleted == [0]


## NUMBER PAD ##

def test_amount_inputs_use_number_keyboard(tmp_path, kivy_window):
    fake_app = FakeApp(tmp_path)
    fake_app.saved_amounts = [
        {"amount": 5.0, "timestamp": datetime.now(), "category": None, "note": None}
    ]

    for box in (AddTransactionPopup(fake_app).amount_input_box, EditTransactionPopup(fake_app, 0).amount_input_box):
        assert box.input_type == "number"
        assert box.input_filter == "float"
