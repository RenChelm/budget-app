from datetime import datetime

import pytest

from budget_periods import summarize_week
from ui.budget_popup import BudgetPopup
from ui.entry_row import BORDER_WIDTH
from ui.history_screen import HistoryScreen, PeriodPage
from ui.week_row import (
    CURRENT_BORDER_WIDTH,
    OVER_BORDER_WIDTH,
    UNCATEGORIZED_COLOR,
    WeekRow,
)

FOOD = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
NOW = datetime(2026, 10, 22, 9, 0)
WEEK_START, WEEK_END = datetime(2026, 10, 15), datetime(2026, 10, 22)


class FakeApp:
    def __init__(self, saved_amounts=None, start_day=15, weekly_max_history=None):
        self.saved_amounts = saved_amounts or []
        self.budget_settings = {"start_day": start_day, "weekly_max_history": weekly_max_history or []}
        self.errors = []
        self.budget_updates = []
        self.show_main_calls = 0
        self.opened_weeks = []

    def show_error(self, message):
        self.errors.append(message)

    def update_budget(self, start_day, weekly_max):
        self.budget_updates.append((start_day, weekly_max))

    def show_main(self):
        self.show_main_calls += 1

    def open_week(self, start, end, week_index):
        self.opened_weeks.append((start, end, week_index))


def make_entry(amount, timestamp, category=None):
    return {"amount": amount, "timestamp": timestamp, "category": category, "note": None}


def make_week(transactions, weekly_max=100.0, now=datetime(2026, 11, 1)):
    return summarize_week(transactions, WEEK_START, WEEK_END, weekly_max, now)


## WEEK ROW ##

def test_week_row_is_filled_with_top_category_color(kivy_window):
    row = WeekRow(make_week([make_entry(40.0, WEEK_START, FOOD), make_entry(10.0, WEEK_START)]), 1)

    assert row.fill_color == FOOD["color"]
    assert row.dates_label.text == "Week 1 · Oct 15 – 21"
    assert row.spent_label.text == "$50.00"
    assert row.detail_label.text == "Food 80% · 2 purchases"
    assert row.status_label.text == "$50.00 left"
    assert row.bar_fraction == pytest.approx(0.5)


def test_week_row_uses_neutral_gray_when_uncategorized_spending_leads(kivy_window):
    row = WeekRow(make_week([make_entry(5.0, WEEK_START)]), 1)

    assert row.fill_color == UNCATEGORIZED_COLOR
    assert row.detail_label.text == "Uncategorized 100% · 1 purchase"


def test_week_row_over_budget_shows_overage_and_heavy_border(kivy_window):
    row = WeekRow(make_week([make_entry(130.0, WEEK_START, FOOD)]), 2)

    assert row.status_label.text == "$30.00 over"
    assert row.border_line.width == OVER_BORDER_WIDTH
    assert row.bar_fraction == 1


def test_week_row_current_week_has_white_border(kivy_window):
    row = WeekRow(make_week([], now=datetime(2026, 10, 18)), 1)

    assert row.border_line.width == CURRENT_BORDER_WIDTH
    assert row.detail_label.text == "No spending"
    assert row.spent_label.text == "$0.00"


def test_week_row_upcoming_week_is_dimmed_without_bar(kivy_window):
    row = WeekRow(make_week([], now=datetime(2026, 10, 1)), 3)

    assert row.fill_color == (0, 0, 0, 0)
    assert row.detail_label.text == "Upcoming"
    assert row.spent_label.text == ""
    assert row.show_bar is False
    assert row.border_line.width == BORDER_WIDTH


def test_week_row_without_weekly_max_hides_bar_and_status(kivy_window):
    row = WeekRow(make_week([make_entry(5.0, WEEK_START, FOOD)], weekly_max=None), 1)

    assert row.show_bar is False
    assert row.status_label.text == ""


## PERIOD PAGE ##

def _history_screen(app):
    screen = HistoryScreen(app, name="history")
    screen.refresh(now=NOW)
    return screen


def test_refresh_builds_one_page_per_period_and_opens_on_current(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(12.0, datetime(2026, 8, 20)), make_entry(30.0, datetime(2026, 10, 16), FOOD)],
        weekly_max_history=[{"from": datetime(2026, 9, 15), "amount": 150.0}]
    )
    screen = _history_screen(app)
    pages = screen.carousel.slides

    assert len(pages) == 3
    assert screen.carousel.index == 2
    assert all(len(page.week_rows) == 4 for page in pages)
    assert pages[-1].title_label.text == "Oct 15 – Nov 14, 2026"
    assert pages[-1].total_label.text == "$30.00 of $600.00 · $150.00/week"
    assert pages[-1].summary_label.text == "This week: $21.43/day · 7 days left"
    assert pages[0].older_label.text == ""
    assert pages[0].newer_label.text == "Sep 15 – Oct 14 ›"
    assert pages[-1].older_label.text == "‹ Sep 15 – Oct 14"


def test_refresh_replaces_pages_instead_of_adding(kivy_window):
    app = FakeApp(saved_amounts=[make_entry(12.0, datetime(2026, 8, 20))])
    screen = _history_screen(app)
    screen.refresh(now=NOW)

    assert len(screen.carousel.slides) == 3


def test_past_period_summary_counts_weeks_over_budget(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(200.0, datetime(2026, 9, 16)), make_entry(10.0, datetime(2026, 9, 23))],
        weekly_max_history=[{"from": datetime(2026, 9, 15), "amount": 150.0}]
    )
    past_page = _history_screen(app).carousel.slides[0]

    assert past_page.summary_label.text == "Over budget in 1 of 4 weeks"


def test_period_without_weekly_max_prompts_to_set_one(kivy_window):
    page = _history_screen(FakeApp()).carousel.slides[-1]

    assert page.total_label.text == "$0.00 spent"
    assert page.summary_label.text == "Set a weekly max with View Budget"


def test_current_week_over_budget_summary(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(160.0, datetime(2026, 10, 22, 8, 0))],
        weekly_max_history=[{"from": datetime(2026, 10, 15), "amount": 150.0}]
    )
    page = _history_screen(app).carousel.slides[-1]

    assert page.summary_label.text == "This week: $10.00 over"


def test_back_button_returns_to_main(kivy_window):
    app = FakeApp()
    screen = HistoryScreen(app, name="history")

    screen.back_btn.dispatch("on_release")

    assert app.show_main_calls == 1


## BUDGET POPUP ##

def test_budget_popup_prefills_current_settings(kivy_window):
    app = FakeApp(start_day=15, weekly_max_history=[{"from": datetime(2020, 1, 15), "amount": 150.0}])
    popup = BudgetPopup(app)

    assert popup.max_input_box.text == "150.00"
    assert popup.start_day_input_box.text == "15"
    assert popup.period_label.text.startswith("Current period:")


def test_budget_popup_saves_valid_settings(kivy_window):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.max_input_box.text = "175.5"
    popup.start_day_input_box.text = "20"

    popup.save_budget()

    assert app.budget_updates == [(20, 175.5)]
    assert app.errors == []


def test_budget_popup_blank_max_means_no_limit(kivy_window):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.max_input_box.text = "   "

    popup.save_budget()

    assert app.budget_updates == [(15, None)]


@pytest.mark.parametrize("start_day", ["0", "32", ""])
def test_budget_popup_rejects_invalid_start_day(kivy_window, start_day):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.start_day_input_box.text = start_day

    popup.save_budget()

    assert app.budget_updates == []
    assert len(app.errors) == 1
    assert popup.period_label.text == "Start day must be 1-31"


@pytest.mark.parametrize("weekly_max", ["0", "."])
def test_budget_popup_rejects_invalid_weekly_max(kivy_window, weekly_max):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.max_input_box.text = weekly_max

    popup.save_budget()

    assert app.budget_updates == []
    assert len(app.errors) == 1


def test_budget_popup_uses_number_keyboards(kivy_window):
    popup = BudgetPopup(FakeApp())

    assert popup.max_input_box.input_type == "number"
    assert popup.max_input_box.input_filter == "float"
    assert popup.start_day_input_box.input_type == "number"
    assert popup.start_day_input_box.input_filter == "int"


## OPENING A WEEK ##

def test_tapping_week_row_opens_that_week(kivy_window):
    app = FakeApp(saved_amounts=[make_entry(12.0, datetime(2026, 9, 20))])
    screen = _history_screen(app)
    september = screen.carousel.slides[0]

    september.week_rows[2].dispatch("on_release")

    assert app.opened_weeks == [(datetime(2026, 9, 15), datetime(2026, 10, 15), 2)]


def test_refresh_can_open_on_a_specific_period(kivy_window):
    app = FakeApp(saved_amounts=[make_entry(12.0, datetime(2026, 8, 20))])
    screen = HistoryScreen(app, name="history")

    screen.refresh(now=NOW, open_start=datetime(2026, 9, 15))
    assert screen.carousel.index == 1

    screen.refresh(now=NOW, open_start=datetime(2026, 9, 1))  # No longer a period start #
    assert screen.carousel.index == 2
