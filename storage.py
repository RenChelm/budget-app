import json
import os
from datetime import datetime

## READING AND WRITING THE APP'S JSON FILES ##
# The only place files are read or written; everything else works on plain lists and dicts #

# Calendar months with no weekly max until the user sets one #
# Weekly mode instead keeps every week 7 days, starting on `start_weekday` (0 = Monday) #
# `carry_overs` records each answer to moving a week's/period's leftover or overspend onto the next one #
DEFAULT_BUDGET_SETTINGS = {
    "mode": "monthly",
    "start_day": 1,
    "start_weekday": 0,
    "weekly_max_history": [],
    "long_week_max_history": [],
    "carry_overs": []
}

def read_json(path):
    # The file's contents, or None when it's missing, empty or not valid JSON #
    try:
        with open(path, "r") as f:
            content = f.read().strip()
        return json.loads(content) if content else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def write_json(path, data):
    # Dates are written as text ("2026-08-30 18:45:00"), which the decoders below turn back into dates #
    with open(path, "w") as f:
        json.dump(data, f, default=str)

## DECODING (A FILE'S PLAIN JSON INTO WHAT THE APP WORKS WITH; NONE MEANS NOTHING WAS SAVED) ##

def _with_dates(record, keys):
    # A copy with any of `keys` that were saved as text turned back into dates #
    return {**record, **{key: datetime.fromisoformat(record[key]) for key in keys if isinstance(record.get(key), str)}}

def decode_transactions(raw):
    return [_with_dates(entry, ("timestamp",)) for entry in raw or []]

def decode_names(raw):
    # Retailer and brand lists used to be plain names, which load as names with no color #
    return [entry if isinstance(entry, dict) else {"name": entry, "color": None} for entry in raw or []]

def decode_budget_settings(raw):
    # Anything missing from the file keeps its default #
    settings = {**DEFAULT_BUDGET_SETTINGS, **(raw or {})}
    return {
        **settings,
        "weekly_max_history": [_with_dates(change, ("from",)) for change in settings["weekly_max_history"]],
        "long_week_max_history": [_with_dates(change, ("from",)) for change in settings["long_week_max_history"]],
        "carry_overs": [_with_dates(choice, ("start", "end")) for choice in settings["carry_overs"]]
    }

## THE APP'S SAVED DATA ##
# Popups work out a new list with pure functions, then hand it to one of these to keep and save #
# Nothing is changed in place, so anything still holding the old list (like a cached History page) sees it as it was #

class SavedData:
    def load_saved_data(self, data_dir, name_kinds):
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        self.categories_file = os.path.join(data_dir, "categories.json")
        self.budget_file = os.path.join(data_dir, "budget.json")
        self.colors_file = os.path.join(data_dir, "colors.json")

        # Retailers and brands the user has added for the Advanced section (retailers.json, brands.json) #
        self.names_files = {kind: os.path.join(data_dir, f"{kind}s.json") for kind in name_kinds}

        self.saved_amounts = decode_transactions(read_json(self.transactions_file))
        self.saved_categories = read_json(self.categories_file) or []
        self.saved_colors = read_json(self.colors_file) or []     # Picked from the color wheel, newest first #
        self.saved_names = {kind: decode_names(read_json(path)) for kind, path in self.names_files.items()}
        self.budget_settings = decode_budget_settings(read_json(self.budget_file))

    def save_transactions(self, transactions):
        self.saved_amounts = transactions
        write_json(self.transactions_file, transactions)

    def save_categories(self, categories):
        self.saved_categories = categories
        write_json(self.categories_file, categories)

    def save_colors(self, colors):
        self.saved_colors = colors
        write_json(self.colors_file, colors)

    def save_names(self, kind, entries):
        self.saved_names = {**self.saved_names, kind: entries}
        write_json(self.names_files[kind], entries)

    def save_budget_settings(self, settings):
        self.budget_settings = settings
        write_json(self.budget_file, settings)
