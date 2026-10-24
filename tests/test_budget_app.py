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


def current_page(app):
    return app.week_carousel.current_slide


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


def test_keyboard_keeps_the_text_box_being_typed_in_visible(app):
    from kivy.core.window import Window

    assert Window.softinput_mode == "below_target"


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

def test_empty_week_shows_message_without_a_row(app):
    app.saved_amounts = []
    app.update_display()

    assert current_page(app).rv.data == []
    assert current_page(app).empty_label.text == "No transactions yet."
    assert app.spent_label.text == "Spent: $0.00"
    assert app.trans_label.text == "Transactions: 0"
    assert app.left_label.text == "No weekly max set"


def test_update_display_sorts_newest_first_and_formats_rows(app):
    week_start = current_page(app).start
    food = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
    app.saved_amounts = [
        make_entry(5.0, week_start + timedelta(hours=1), category=food),
        make_entry(12.5, week_start + timedelta(hours=2), category=None, note="late lunch"),
        make_entry(99.0, week_start - timedelta(hours=1)),  # previous week, not shown #
    ]

    app.update_display()
    rows = current_page(app).rv.data

    assert len(rows) == 2
    assert rows[0]["index"] == 1  # the "now" entry sorts first
    assert rows[0]["category_text"] == "Uncategorized"
    assert rows[0]["amount_text"] == "$12.50"
    assert rows[0]["note_text"] == "late lunch"
    assert rows[1]["index"] == 0
    assert rows[1]["category_text"] == "Food"
    assert rows[1]["category_color"] == food["color"]
    assert current_page(app).empty_label.text == ""

    assert app.spent_label.text == "Spent: $17.50"
    assert app.trans_label.text == "Transactions: 2"


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


## SORTING ##

def _sorted_amounts(app):
    return [row["amount_text"] for row in current_page(app).rv.data]


def _sorting_entries(app):
    middle = current_page(app).start + timedelta(days=2)
    return [
        make_entry(20.0, middle),
        make_entry(5.0, middle + timedelta(days=1)),
        make_entry(50.0, middle - timedelta(days=1)),
    ]


def test_default_sort_is_newest_first(app):
    app.saved_amounts = _sorting_entries(app)
    app.update_display()

    assert _sorted_amounts(app) == ["$5.00", "$20.00", "$50.00"]


def test_toggle_date_sort_shows_oldest_first(app):
    app.saved_amounts = _sorting_entries(app)
    app.toggle_sort_order()

    assert _sorted_amounts(app) == ["$50.00", "$20.00", "$5.00"]


def test_sort_by_amount_biggest_first_then_smallest(app):
    app.saved_amounts = _sorting_entries(app)
    app.set_sort_method("amount")
    assert _sorted_amounts(app) == ["$50.00", "$20.00", "$5.00"]

    app.toggle_sort_order()
    assert _sorted_amounts(app) == ["$5.00", "$20.00", "$50.00"]


def test_switching_sort_method_resets_to_descending(app):
    app.toggle_sort_order()
    app.set_sort_method("amount")

    assert app.sort_by == "amount"
    assert app.sort_descending is True


def test_sort_controls_reflect_app_state(app, kivy_window):
    from ui.sort_controls import SortControls

    controls = SortControls(app)
    controls.select_method("amount")
    assert controls.method_label.text == "Amount"
    assert controls.order_triangle.descending is True

    controls.toggle_order()
    assert controls.order_triangle.descending is False
    assert app.sort_descending is False


def test_tapping_sort_text_or_triangle_toggles_order(app, kivy_window):
    from kivy.tests.common import UnitTestTouch
    from ui.sort_controls import SortControls

    controls = SortControls(app, size_hint=(None, None), size=(130, 50), pos=(0, 0))
    kivy_window.add_widget(controls)
    try:
        controls.do_layout()
        controls.order_toggle.do_layout()

        for widget in (controls.method_label, controls.order_triangle):
            before = app.sort_descending
            touch = UnitTestTouch(widget.x + widget.width / 2, widget.y + widget.height / 2)
            touch.touch_down()
            touch.touch_up()
            assert app.sort_descending is not before
    finally:
        kivy_window.remove_widget(controls)


## TOP BAR ##

def _root_widget(app):
    return app.screen_manager


def test_title_is_centered_on_any_width(app):
    title = next(w for w in _root_widget(app).walk() if getattr(w, "text", None) == "Transactions")
    top_bar = title.parent

    for width in (300, 360, 480, 720):
        top_bar.width = width
        top_bar.do_layout()
        assert title.center_x == top_bar.x + width / 2


def test_top_bar_has_menu_button(app):
    from ui.menu_button import MenuButton

    assert any(isinstance(w, MenuButton) for w in _root_widget(app).walk())


## BUDGET SETTINGS ##

def test_budget_defaults_to_calendar_months_without_max(app):
    assert app.budget_settings == {"start_day": 1, "weekly_max_history": []}


def test_update_budget_persists_and_reloads(app, tmp_path):
    from main import BudgetApp

    app.update_budget(15, 150.0, now=datetime(2026, 10, 22))

    reloaded = BudgetApp()
    reloaded._user_data_dir = str(tmp_path)
    reloaded.build()

    assert reloaded.budget_settings == {
        "start_day": 15,
        "weekly_max_history": [{"from": datetime(2026, 10, 15), "amount": 150.0}],
    }


def test_update_budget_keeps_previous_periods_max(app):
    from budget_periods import weekly_max_for

    app.update_budget(15, 150.0, now=datetime(2026, 9, 20))
    app.update_budget(15, 200.0, now=datetime(2026, 10, 22))

    history = app.budget_settings["weekly_max_history"]
    assert weekly_max_for(datetime(2026, 9, 15), history) == 150.0
    assert weekly_max_for(datetime(2026, 10, 15), history) == 200.0


def test_build_handles_corrupt_budget_json(tmp_path, kivy_window):
    from main import BudgetApp

    (tmp_path / "budget.json").write_text("{not valid json")

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()  # should not raise

    assert instance.budget_settings == {"start_day": 1, "weekly_max_history": []}


## SCREEN NAVIGATION ##

def test_view_history_button_opens_history_screen(app):
    btn_history = next(w for w in _root_widget(app).walk() if getattr(w, "text", None) == "View\nHistory")

    btn_history.dispatch("on_release")

    assert app.screen_manager.current == "history"
    assert len(app.history_screen.carousel.slides) >= 1


def test_back_key_leaves_history_but_not_main(app):
    app.open_history()

    assert app.on_back_key(None, 27) is True
    assert app.screen_manager.current == "main"
    assert app.on_back_key(None, 27) is False


def test_tapping_history_week_opens_its_transactions(app):
    week_start = current_page(app).start
    app.saved_amounts = [make_entry(7.0, week_start + timedelta(hours=1))]
    app.open_history()

    page = app.history_screen.carousel.current_slide
    tapped = app.week_carousel.index
    page.week_rows[tapped].dispatch("on_release")

    assert app.screen_manager.current == "week"
    shown = app.week_screen.carousel.current_slide
    assert shown.start == week_start
    assert [row["amount_text"] for row in shown.rv.data] == ["$7.00"]


def test_back_from_week_returns_to_its_history_period(app):
    app.saved_amounts = [make_entry(3.0, datetime(2026, 1, 20))]
    app.open_history()
    oldest = app.history_screen.carousel.slides[0].period
    app.open_week(oldest["start"], oldest["end"], 2)

    assert app.on_back_key(None, 27) is True
    assert app.screen_manager.current == "history"
    assert app.history_screen.carousel.current_slide.period["start"] == oldest["start"]

    assert app.on_back_key(None, 27) is True
    assert app.screen_manager.current == "main"


## WEEK PAGES ##

def test_main_page_shows_the_current_periods_four_weeks_on_this_week(app):
    now = datetime.now()
    pages = app.week_carousel.slides

    assert len(pages) == 4
    assert pages[0].start == app.week_carousel.period[0]
    assert pages[-1].end == app.week_carousel.period[1]
    assert current_page(app).start <= now < current_page(app).end
    assert current_page(app).title_label.text.startswith("This Week · ")


def test_each_week_page_lists_only_its_own_transactions(app):
    first, second = app.week_carousel.slides[:2]
    app.saved_amounts = [
        make_entry(1.0, first.start),
        make_entry(2.0, second.start),
        make_entry(3.0, second.end - timedelta(minutes=1)),
    ]
    app.update_display()

    assert [row["amount_text"] for row in first.rv.data] == ["$1.00"]
    assert [row["amount_text"] for row in second.rv.data] == ["$3.00", "$2.00"]


def test_upcoming_week_message(app):
    last = app.week_carousel.slides[-1]
    last.refresh(app, last.start - timedelta(days=1))

    assert last.rv.data == []
    assert last.empty_label.text == "Week hasn't started."
    assert last.title_label.text.startswith("Week 4 · ")


def test_info_panel_follows_the_week_being_viewed(app):
    first = app.week_carousel.slides[0]
    app.saved_amounts = [make_entry(40.0, first.start), make_entry(2.0, first.start)]
    app.update_budget(app.budget_settings["start_day"], 30.0)

    app.week_carousel.index = 0

    assert app.spent_label.text == "Spent: $42.00"
    assert app.trans_label.text == "Transactions: 2"
    assert app.left_label.text == "Over by: $12.00"

    app.week_carousel.index = 3

    assert app.spent_label.text == "Spent: $0.00"
    assert app.left_label.text == "Left: $30.00"


@pytest.fixture
def opened_add_popups(monkeypatch):
    import main

    opened = []
    stub = type("Stub", (), {"open": lambda self: None})
    monkeypatch.setattr(main, "AddTransactionPopup", lambda app, day=None: opened.append(day) or stub())
    return opened


def test_add_on_current_week_leaves_date_blank(app, opened_add_popups):
    current = app.week_carousel.index

    app.open_transaction_window(None)

    assert opened_add_popups == [None]
    assert app.week_carousel.index == current


def test_add_on_past_week_prefills_its_first_day_and_stays_there(app, opened_add_popups):
    app.week_carousel.show_period(datetime(2026, 1, 1), datetime(2026, 2, 1))
    app.week_carousel.index = 2

    app.open_transaction_window(None)

    assert opened_add_popups == [datetime(2026, 1, 15).date()]
    assert app.week_carousel.index == 2


def test_saving_a_transaction_shows_the_week_it_landed_in(app):
    from ui.add_transaction_popup import AddTransactionPopup

    first = app.week_carousel.slides[0]
    app.week_carousel.index = 3

    popup = AddTransactionPopup(app, day=first.start.date())
    popup.amount_input_box.text = "8"
    popup.save_text()

    assert app.week_carousel.index == 0
    assert [row["amount_text"] for row in first.rv.data] == ["$8.00"]


def test_changing_start_day_rebuilds_week_pages(app):
    app.update_budget(15, None)

    assert app.week_carousel.period[0].day == 15
    assert len(app.week_carousel.slides) == 4
