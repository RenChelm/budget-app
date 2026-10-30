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
    assert app.budget_settings == {
        "mode": "monthly",
        "start_day": 1,
        "start_weekday": 0,
        "weekly_max_history": [],
        "long_week_max_history": [],
        "carry_overs": [],
    }


def test_update_budget_persists_and_reloads(app, tmp_path):
    from main import BudgetApp

    app.update_budget({"start_day": 15}, 150.0, now=datetime(2026, 10, 22))

    reloaded = BudgetApp()
    reloaded._user_data_dir = str(tmp_path)
    reloaded.build()

    assert reloaded.budget_settings == {
        "mode": "monthly",
        "start_day": 15,
        "start_weekday": 0,
        "weekly_max_history": [{"from": datetime(2026, 10, 15), "amount": 150.0}],
        "long_week_max_history": [],
        "carry_overs": [],
    }


def test_update_budget_persists_weekly_mode(app, tmp_path):
    from main import BudgetApp

    app.update_budget({"mode": "weekly", "start_weekday": 6}, 150.0, now=datetime(2026, 10, 29))

    reloaded = BudgetApp()
    reloaded._user_data_dir = str(tmp_path)
    reloaded.build()

    assert reloaded.budget_settings["mode"] == "weekly"
    assert reloaded.budget_settings["start_weekday"] == 6
    assert reloaded.budget_settings["weekly_max_history"] == [{"from": datetime(2026, 10, 4), "amount": 150.0}]


def test_switching_modes_keeps_the_current_max_for_the_new_period(app):
    from budget_periods import weekly_max_for

    app.update_budget({"start_day": 15}, 100.0, now=datetime(2026, 9, 20))
    app.update_budget({"start_day": 15}, 150.0, now=datetime(2026, 10, 22))
    app.update_budget({"mode": "weekly"}, 150.0, now=datetime(2026, 10, 29))

    # October's weeks start Oct 5, before the Oct 15 change, so the max is set again from Oct 5 #
    history = app.budget_settings["weekly_max_history"]
    assert weekly_max_for(datetime(2026, 10, 5), history) == 150.0
    assert weekly_max_for(datetime(2026, 9, 7), history) == 100.0


def test_update_budget_keeps_previous_periods_max(app):
    from budget_periods import weekly_max_for

    app.update_budget({"start_day": 15}, 150.0, now=datetime(2026, 9, 20))
    app.update_budget({"start_day": 15}, 200.0, now=datetime(2026, 10, 22))

    history = app.budget_settings["weekly_max_history"]
    assert weekly_max_for(datetime(2026, 9, 15), history) == 150.0
    assert weekly_max_for(datetime(2026, 10, 15), history) == 200.0


def test_build_handles_corrupt_budget_json(tmp_path, kivy_window):
    from main import BudgetApp

    (tmp_path / "budget.json").write_text("{not valid json")

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()  # should not raise

    assert instance.budget_settings == {
        "mode": "monthly",
        "start_day": 1,
        "start_weekday": 0,
        "weekly_max_history": [],
        "long_week_max_history": [],
        "carry_overs": [],
    }


def test_budget_saved_before_weekly_mode_loads_as_monthly(tmp_path, kivy_window):
    from main import BudgetApp

    (tmp_path / "budget.json").write_text(json.dumps({
        "start_day": 15, "weekly_max_history": [{"from": "2026-10-15 00:00:00", "amount": 150.0}]
    }))

    instance = BudgetApp()
    instance._user_data_dir = str(tmp_path)
    instance.build()

    assert instance.budget_settings["mode"] == "monthly"
    assert instance.budget_settings["start_day"] == 15
    assert instance.budget_settings["weekly_max_history"] == [{"from": datetime(2026, 10, 15), "amount": 150.0}]


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

def test_every_swipeable_screen_shares_the_same_swipe_settings(app):
    from kivy.metrics import dp
    from ui.page_carousel import SWIPE_MIN_MOVE, SWIPE_TIMEOUT

    carousels = [app.week_carousel, app.week_screen.carousel, app.history_screen.carousel]

    for carousel in carousels:
        assert carousel.min_move == SWIPE_MIN_MOVE
        assert carousel.scroll_timeout == SWIPE_TIMEOUT
        assert carousel.scroll_distance == dp(20)
        assert carousel.ignore_perpendicular_swipes is True
        assert carousel.direction == "right"


def test_a_shorter_swipe_now_turns_the_week(app, monkeypatch):
    import kivy.uix.carousel as carousel_module

    # Records where each swipe would settle instead of animating there #
    targets = []

    class RecordingAnimation:
        def __init__(self, **kwargs):
            targets.append(kwargs["_offset"])

        def bind(self, **kwargs):
            pass

        def cancel_all(self, *args):
            pass

        def start(self, widget):
            pass

    monkeypatch.setattr(carousel_module, "Animation", RecordingAnimation)
    carousel = app.week_carousel
    carousel.width = 360
    carousel.index = 1

    carousel._start_animation(offset=-0.15 * 360)   # 15% of the width; Kivy's default needed 20% #
    carousel._start_animation(offset=-0.10 * 360)   # Still too short, so it snaps back #

    assert targets == [-360, 0]


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
    app.update_budget({}, 30.0)

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
    app.update_budget({"start_day": 15}, None)

    assert app.week_carousel.period[0].day == 15
    assert len(app.week_carousel.slides) == 4


def test_switching_to_weekly_rebuilds_week_pages_as_seven_day_weeks(app):
    now = datetime.now()
    app.update_budget({"mode": "weekly", "start_weekday": 2}, None)
    pages = app.week_carousel.slides

    assert len(pages) in (4, 5)
    assert all((page.end - page.start).days == 7 for page in pages)
    assert all(page.start.weekday() == 2 for page in pages)
    assert pages[0].start.day <= 7          # Starts on the month's first Wednesday #
    assert current_page(app).start <= now < current_page(app).end


def test_week_arrows_hide_only_at_the_ends_of_a_five_week_period(app):
    app.week_carousel.show_period(datetime(2026, 11, 2), datetime(2026, 12, 7))
    pages = app.week_carousel.slides

    assert len(pages) == 5
    assert [page.prev_btn.disabled for page in pages] == [True, False, False, False, False]
    assert [page.next_btn.disabled for page in pages] == [False, False, False, False, True]


def test_update_budget_persists_long_week_max(app, tmp_path):
    from main import BudgetApp

    app.update_budget({"start_day": 1}, 150.0, 200.0, now=datetime(2026, 10, 22))

    reloaded = BudgetApp()
    reloaded._user_data_dir = str(tmp_path)
    reloaded.build()

    assert reloaded.budget_settings["long_week_max_history"] == [{"from": datetime(2026, 10, 1), "amount": 200.0}]


## CARRY-OVER ##

@pytest.fixture
def opened_carry_over_popups(monkeypatch):
    import main

    opened = []

    class StubPopup:
        def __init__(self, app, span, current, mode):
            opened.append((span, current, mode))
            self.on_dismiss = None

        def bind(self, on_dismiss):
            self.on_dismiss = on_dismiss

        def open(self):
            pass

        def dismiss(self):
            self.on_dismiss(self)

    monkeypatch.setattr(main, "CarryOverPopup", StubPopup)
    return opened


def _spend_last_week(app, amount):
    # Weekly mode with a $100 max, and `amount` spent in the week before the current one #
    app.update_budget({"mode": "weekly"}, 100.0)
    last_start = current_page(app).start - timedelta(weeks=1)
    app.saved_amounts = [make_entry(amount, last_start + timedelta(days=1))]
    app.update_display()
    return last_start


def _week(app, start):
    from budget_periods import week_summary

    return week_summary(app.saved_amounts, app.budget_settings, start, datetime.now())


def test_check_carry_over_asks_about_last_week_once(app, opened_carry_over_popups):
    last_start = _spend_last_week(app, 60.0)

    app.check_carry_over()
    app.check_carry_over()  # Already showing #

    assert len(opened_carry_over_popups) == 1
    span, current, mode = opened_carry_over_popups[0]
    assert span["start"] == last_start
    assert span["carry_over"]["amount"] == 40.0
    assert current["start"] == current_page(app).start
    assert mode == "weekly"

    app.set_carry_over(span, False)
    app.carry_over_popup.dismiss()
    app.check_carry_over()

    assert len(opened_carry_over_popups) == 1


def test_check_carry_over_offers_to_subtract_last_weeks_overspend(app, opened_carry_over_popups):
    _spend_last_week(app, 130.0)

    app.check_carry_over()

    span, current, mode = opened_carry_over_popups[0]
    assert span["carry_over"] == {"amount": -30.0, "over": True, "carried": False, "answered": False}


def test_check_carry_over_does_nothing_when_last_week_was_on_budget(app, opened_carry_over_popups):
    _spend_last_week(app, 100.0)

    app.check_carry_over()

    assert opened_carry_over_popups == []
    assert app.carry_over_popup is None


def test_adding_carry_over_raises_this_weeks_budget_and_persists(app, tmp_path):
    from main import BudgetApp

    last_start = _spend_last_week(app, 60.0)
    app.set_carry_over(_week(app, last_start), True)

    assert app.left_label.text == "Left: $140.00\n($40.00 added)"

    reloaded = BudgetApp()
    reloaded._user_data_dir = str(tmp_path)
    reloaded.build()

    assert reloaded.budget_settings["carry_overs"] == [
        {"mode": "weekly", "start": last_start, "end": last_start + timedelta(weeks=1), "over": False, "carried": True}
    ]


def test_subtracting_an_overspend_lowers_this_weeks_budget(app):
    last_start = _spend_last_week(app, 130.0)
    app.set_carry_over(_week(app, last_start), True)

    assert app.left_label.text == "Left: $70.00\n($30.00 subtracted)"


def test_switching_modes_hides_carry_overs_until_switching_back(app):
    last_start = _spend_last_week(app, 60.0)
    app.set_carry_over(_week(app, last_start), True)

    app.update_budget({"mode": "monthly"}, 100.0)

    assert "added" not in app.left_label.text

    app.update_budget({"mode": "weekly"}, 100.0)

    assert app.left_label.text == "Left: $140.00\n($40.00 added)"
    assert len(app.budget_settings["carry_overs"]) == 1


def test_set_carry_over_redraws_history_on_the_same_page(app):
    last_start = _spend_last_week(app, 60.0)
    app.open_history()
    shown = app.history_screen.carousel.current_slide.period["start"]

    app.set_carry_over(_week(app, last_start), True)

    assert app.screen_manager.current == "history"
    assert app.history_screen.carousel.current_slide.period["start"] == shown
    rows = [row for page in app.history_screen.carousel.slides for row in page.week_rows]
    last_week = next(row for row in rows if row.week["start"] == last_start)
    assert last_week.carry_btn.text == "Added to next week"


def test_week_screen_is_titled_by_month_in_weekly_mode(app):
    app.update_budget({"mode": "weekly"}, None)
    app.open_week(datetime(2026, 11, 2), datetime(2026, 12, 7), 4)

    assert app.week_screen.title_label.text == "November 2026"
    assert len(app.week_screen.carousel.slides) == 5
    assert app.week_screen.carousel.index == 4
