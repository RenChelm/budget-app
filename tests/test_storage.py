import json
from datetime import datetime

import pytest

from storage import (
    DEFAULT_BUDGET_SETTINGS,
    SavedData,
    decode_budget_settings,
    decode_names,
    decode_transactions,
    read_json,
    write_json,
)


## READING AND WRITING ##

@pytest.mark.parametrize("content", [None, "", "   \n", "{not valid json"])
def test_read_json_gives_none_for_a_missing_empty_or_broken_file(tmp_path, content):
    path = tmp_path / "data.json"
    if content is not None:
        path.write_text(content)

    assert read_json(str(path)) is None


def test_read_json_gives_the_files_contents(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps([{"name": "Food"}]))

    assert read_json(str(path)) == [{"name": "Food"}]


def test_written_dates_decode_back_to_the_same_dates(tmp_path):
    path = str(tmp_path / "transactions.json")
    transactions = [{"amount": 5.0, "timestamp": datetime(2026, 8, 30, 18, 45), "category": None, "note": None}]

    write_json(path, transactions)

    assert read_json(path)[0]["timestamp"] == "2026-08-30 18:45:00"
    assert decode_transactions(read_json(path)) == transactions


## DECODING ##

def test_decode_transactions_turns_saved_text_into_dates_without_changing_what_was_read():
    raw = [{"amount": 9.99, "timestamp": "2026-07-01T12:00:00"}, {"amount": 1.0}]

    decoded = decode_transactions(raw)

    assert decoded == [{"amount": 9.99, "timestamp": datetime(2026, 7, 1, 12, 0)}, {"amount": 1.0}]
    assert raw[0]["timestamp"] == "2026-07-01T12:00:00"


def test_decode_names_loads_older_plain_names_with_no_color():
    raw = ["Lay's", {"name": "Nike", "color": [0.9, 0.3, 0.3, 1]}]

    assert decode_names(raw) == [{"name": "Lay's", "color": None}, {"name": "Nike", "color": [0.9, 0.3, 0.3, 1]}]


@pytest.mark.parametrize("decode", [decode_transactions, decode_names])
def test_decoding_nothing_saved_gives_an_empty_list(decode):
    assert decode(None) == []


def test_decode_budget_settings_with_nothing_saved_gives_the_defaults():
    assert decode_budget_settings(None) == DEFAULT_BUDGET_SETTINGS


def test_decode_budget_settings_keeps_defaults_for_anything_missing_and_turns_text_into_dates():
    raw = {
        "start_day": 15,
        "weekly_max_history": [{"from": "2026-10-15 00:00:00", "amount": 150.0}],
        "carry_overs": [{"mode": "weekly", "start": "2026-10-05", "end": "2026-10-12", "over": False, "carried": True}],
    }

    settings = decode_budget_settings(raw)

    assert settings["mode"] == "monthly" and settings["start_weekday"] == 0
    assert settings["start_day"] == 15
    assert settings["weekly_max_history"] == [{"from": datetime(2026, 10, 15), "amount": 150.0}]
    assert settings["long_week_max_history"] == []
    assert (settings["carry_overs"][0]["start"], settings["carry_overs"][0]["end"]) == (datetime(2026, 10, 5), datetime(2026, 10, 12))


def test_decoded_budget_settings_never_share_the_defaults_lists():
    settings = decode_budget_settings(None)

    assert all(settings[key] is not DEFAULT_BUDGET_SETTINGS[key] for key in ("weekly_max_history", "long_week_max_history", "carry_overs"))


## THE APP'S SAVED DATA ##

class DataApp(SavedData):
    pass


@pytest.fixture
def app(tmp_path):
    instance = DataApp()
    instance.load_saved_data(str(tmp_path), ["retailer", "brand"])
    return instance


def test_load_saved_data_with_no_files_starts_empty(app, tmp_path):
    assert (app.saved_amounts, app.saved_categories, app.saved_colors) == ([], [], [])
    assert app.saved_names == {"retailer": [], "brand": []}
    assert app.budget_settings == DEFAULT_BUDGET_SETTINGS
    assert app.names_files == {"retailer": str(tmp_path / "retailers.json"), "brand": str(tmp_path / "brands.json")}


@pytest.mark.parametrize("save, attribute, file, value", [
    ("save_transactions", "saved_amounts", "transactions.json", [{"amount": 5.0, "timestamp": datetime(2026, 10, 1)}]),
    ("save_categories", "saved_categories", "categories.json", [{"name": "Food", "color": [1, 0.6, 0.2, 1]}]),
    ("save_colors", "saved_colors", "colors.json", [[0.8, 0.4, 0.4, 1]]),
    ("save_budget_settings", "budget_settings", "budget.json", {**DEFAULT_BUDGET_SETTINGS, "start_day": 15}),
])
def test_each_save_keeps_the_new_value_and_reloads_the_same(app, tmp_path, save, attribute, file, value):
    getattr(app, save)(value)

    assert getattr(app, attribute) is value
    assert (tmp_path / file).exists()

    reloaded = DataApp()
    reloaded.load_saved_data(str(tmp_path), ["retailer", "brand"])
    assert getattr(reloaded, attribute) == value


def test_save_names_replaces_one_kind_without_changing_the_old_dict(app, tmp_path):
    old = app.saved_names
    walmart = [{"name": "Walmart", "color": None}]

    app.save_names("retailer", walmart)

    assert app.saved_names == {"retailer": walmart, "brand": []}
    assert old == {"retailer": [], "brand": []}
    assert json.loads((tmp_path / "retailers.json").read_text()) == walmart
