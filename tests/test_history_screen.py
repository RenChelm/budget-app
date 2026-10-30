from datetime import datetime, timedelta

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
    def __init__(self, saved_amounts=None, start_day=15, weekly_max_history=None, mode="monthly", start_weekday=0,
                 long_week_max_history=None, carry_overs=None):
        self.saved_amounts = saved_amounts or []
        self.budget_settings = {
            "mode": mode,
            "start_day": start_day,
            "start_weekday": start_weekday,
            "weekly_max_history": weekly_max_history or [],
            "long_week_max_history": long_week_max_history or [],
            "carry_overs": carry_overs or []
        }
        self.errors = []
        self.budget_updates = []
        self.show_main_calls = 0
        self.opened_weeks = []
        self.carry_over_choices = []

    def show_error(self, message):
        self.errors.append(message)

    def update_budget(self, changes, weekly_max, long_week_max=None):
        self.budget_updates.append((changes, weekly_max, long_week_max))

    def set_carry_over(self, span, carried):
        self.carry_over_choices.append((span["start"], span["end"], span["carry_over"]["over"], carried))

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


def test_week_row_bar_includes_carried_in_budget(kivy_window):
    week = summarize_week([make_entry(50.0, WEEK_START)], WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1), carried_in=100.0)
    row = WeekRow(week, 1)

    assert row.bar_fraction == pytest.approx(0.25)
    assert row.status_label.text == "$150.00 left"


def _finished_week(carried, over=False):
    # A finished week with $30 left (or $30 over) that can move onto next week #
    week = make_week([make_entry(130.0 if over else 70.0, WEEK_START)])
    week["carry_over"] = {"amount": -30.0 if over else 30.0, "over": over, "carried": carried, "answered": True}
    return week


@pytest.mark.parametrize("over, carried, text", [
    (False, False, "Add to next week"),
    (False, True, "Added to next week"),
    (True, False, "Subtract from next week"),
    (True, True, "Subtracted from next week"),
])
def test_week_row_offers_to_move_its_amount_onto_next_week(kivy_window, over, carried, text):
    choices = []
    week = _finished_week(carried, over)
    row = WeekRow(week, 1, on_carry_over=lambda *args: choices.append(args))

    assert row.carry_btn.text == text
    assert row.status_label.text == ("$30.00 over" if over else "$30.00 left")     # The amount it would move #

    row.carry_btn.dispatch("on_release")

    assert choices == [(week, not carried)]


def test_carry_over_button_names_the_amount_for_months(kivy_window):
    from ui.carry_over_button import carry_over_text

    assert carry_over_text({"amount": 95.0, "over": False, "carried": False}, "month") == "Add $95.00 to next month"
    assert carry_over_text({"amount": -120.0, "over": True, "carried": True}, "month") == "Subtracted $120.00 from next month"


def test_carry_over_button_is_filled_only_once_its_on(kivy_window):
    from ui.carry_over_button import CarryOverButton

    off = CarryOverButton({"amount": 30.0, "over": False, "carried": False}, "week", outline_color=(1, 1, 1, 1))
    on = CarryOverButton({"amount": 30.0, "over": False, "carried": True}, "week", outline_color=(1, 1, 1, 1))

    assert off.color == [1, 1, 1, 1]
    assert on.color == [0, 0, 0, 1]
    assert on.carried and not off.carried


def test_week_row_shortens_the_bar_beside_the_button(kivy_window):
    from ui.week_row import PILL_WIDTH

    plain = WeekRow(make_week([make_entry(70.0, WEEK_START)]), 1, size_hint=(None, None), size=(336, 96))
    with_button = WeekRow(_finished_week(False), 1, on_carry_over=lambda *args: None,
                          size_hint=(None, None), size=(336, 96))
    plain.update_rect()
    with_button.update_rect()

    assert with_button.bar_track.size[0] < plain.bar_track.size[0]
    assert with_button.bar_track.pos[0] + with_button.bar_track.size[0] < with_button.width * (0.96 - PILL_WIDTH)


def test_week_row_with_no_budget_left_shows_a_full_bar(kivy_window):
    week = summarize_week([], WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1), carried_in=-130.0)
    row = WeekRow(week, 1)

    assert row.bar_fraction == 1
    assert row.status_label.text == "$30.00 over"


def test_tapping_the_carry_button_does_not_open_the_week(kivy_window):
    from kivy.tests.common import UnitTestTouch

    opened, choices = [], []
    row = WeekRow(_finished_week(False), 1, on_carry_over=lambda *args: choices.append(args),
                  size_hint=(None, None), size=(336, 96), pos=(0, 0))
    row.bind(on_release=lambda inst: opened.append(inst))
    kivy_window.add_widget(row)
    try:
        row.do_layout()
        touch = UnitTestTouch(row.carry_btn.center_x, row.carry_btn.center_y)
        touch.touch_down()
        touch.touch_up()
    finally:
        kivy_window.remove_widget(row)

    assert len(choices) == 1
    assert opened == []


def test_week_row_without_carry_callback_has_no_button(kivy_window):
    row = WeekRow(_finished_week(False), 1)

    assert row.carry_btn is None
    assert row.status_label.text == "$30.00 left"


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


def test_weekly_mode_pages_are_months_of_four_or_five_weeks(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(12.0, datetime(2026, 10, 7)), make_entry(30.0, datetime(2026, 11, 17), FOOD)],
        weekly_max_history=[{"from": datetime(2026, 10, 5), "amount": 150.0}],
        mode="weekly"
    )
    screen = HistoryScreen(app, name="history")
    screen.refresh(now=datetime(2026, 11, 20))
    october, november = screen.carousel.slides

    assert len(october.week_rows) == 4
    assert len(november.week_rows) == 5
    assert october.title_label.text == "October 2026"
    assert november.title_label.text == "November 2026"
    assert november.total_label.text == "$30.00 of $750.00 · $150.00/week"
    assert november.older_label.text == "‹ October"
    assert october.newer_label.text == "November ›"
    assert november.week_rows[0].dates_label.text == "Week 1 · Nov 2 – 8"
    assert november.week_rows[-1].dates_label.text == "Week 5 · Nov 30 – Dec 6"


def test_weekly_mode_history_rows_carry_over_through_the_app(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(60.0, datetime(2026, 10, 13))],
        weekly_max_history=[{"from": datetime(2026, 10, 5), "amount": 100.0}],
        mode="weekly"
    )
    page = _history_screen(app).carousel.slides[-1]
    week_2 = page.week_rows[1]

    assert week_2.carry_btn.text == "Add to next week"
    assert week_2.status_label.text == "$40.00 left"
    assert page.week_rows[0].carry_btn is None      # Nothing was logged yet #
    assert page.week_rows[2].carry_btn is None      # Current week; it hasn't finished #
    assert page.carry_btn is None                   # Weekly mode moves weeks, not months #

    assert page.total_label.text == "$60.00 of $400.00 · $100.00/week"

    week_2.carry_btn.dispatch("on_release")

    assert app.carry_over_choices == [(datetime(2026, 10, 12), datetime(2026, 10, 19), False, True)]


def test_monthly_history_offers_to_add_a_months_leftover_to_next_month(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(500.0, datetime(2026, 9, 16))],
        weekly_max_history=[{"from": datetime(2026, 9, 15), "amount": 150.0}]
    )
    september, october = _history_screen(app).carousel.slides

    assert september.carry_btn.text == "Add $100.00 to next month"
    assert october.carry_btn is None
    assert october.last_month_label is None     # Not added yet #
    assert all(row.carry_btn is None for row in september.week_rows)

    september.carry_btn.dispatch("on_release")

    assert app.carry_over_choices == [(datetime(2026, 9, 15), datetime(2026, 10, 15), False, True)]


def test_added_leftover_raises_next_months_total(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(500.0, datetime(2026, 9, 16))],
        weekly_max_history=[{"from": datetime(2026, 9, 15), "amount": 150.0}],
        carry_overs=[{"mode": "monthly", "start": datetime(2026, 9, 15), "end": datetime(2026, 10, 15), "over": False, "carried": True}]
    )
    september, october = _history_screen(app).carousel.slides

    assert september.carry_btn.text == "Added $100.00 to next month"
    assert october.total_label.text == "$0.00 of $700.00 · $150.00/week"
    assert october.last_month_label.text == "Last month's $100.00 leftover added"
    assert september.last_month_label is None


def test_monthly_history_offers_to_subtract_an_overspent_month(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(700.0, datetime(2026, 9, 16))],
        weekly_max_history=[{"from": datetime(2026, 9, 15), "amount": 150.0}],
        carry_overs=[{"mode": "monthly", "start": datetime(2026, 9, 15), "end": datetime(2026, 10, 15), "over": True, "carried": True}]
    )
    september, october = _history_screen(app).carousel.slides

    assert september.carry_btn.text == "Subtracted $100.00 from next month"
    assert october.total_label.text == "$0.00 of $500.00 · $150.00/week"
    assert october.last_month_label.text == "Last month's $100.00 overspend subtracted"

    september.carry_btn.dispatch("on_release")

    assert app.carry_over_choices == [(datetime(2026, 9, 15), datetime(2026, 10, 15), True, False)]


def test_long_week_max_counts_toward_the_period_total(kivy_window):
    app = FakeApp(
        weekly_max_history=[{"from": datetime(2026, 10, 15), "amount": 150.0}],
        long_week_max_history=[{"from": datetime(2026, 10, 15), "amount": 200.0}]
    )
    page = _history_screen(app).carousel.slides[-1]

    assert page.total_label.text == "$0.00 of $650.00 · $150.00/week"
    assert page.week_rows[-1].status_label.text == ""   # Upcoming #


def test_weekly_mode_month_total_ignores_money_moved_between_its_weeks(kivy_window):
    app = FakeApp(
        saved_amounts=[make_entry(130.0, datetime(2026, 10, 6)), make_entry(60.0, datetime(2026, 10, 13))],
        weekly_max_history=[{"from": datetime(2026, 10, 5), "amount": 100.0}],
        mode="weekly",
        carry_overs=[{"mode": "weekly", "start": datetime(2026, 10, 5), "end": datetime(2026, 10, 12), "over": True, "carried": True}]
    )
    page = _history_screen(app).carousel.slides[-1]

    assert page.week_rows[0].carry_btn.text == "Subtracted from next week"
    assert page.week_rows[1].status_label.text == "$10.00 left"     # Week 2 has $30 less room #
    assert page.total_label.text == "$190.00 of $400.00 · $100.00/week"


def test_weekly_mode_month_total_ignores_money_from_last_months_final_week(kivy_window):
    # The week of Sep 28 starts in September; subtracting its overspend lowers the week of Oct 5 #
    app = FakeApp(
        saved_amounts=[make_entry(130.0, datetime(2026, 9, 29)), make_entry(20.0, datetime(2026, 10, 6))],
        weekly_max_history=[{"from": datetime(2026, 9, 7), "amount": 100.0}],
        mode="weekly",
        carry_overs=[{"mode": "weekly", "start": datetime(2026, 9, 28), "end": datetime(2026, 10, 5), "over": True, "carried": True}]
    )
    september, october = _history_screen(app).carousel.slides

    assert september.week_rows[-1].carry_btn.text == "Subtracted from next week"
    assert october.week_rows[0].status_label.text == "$50.00 left"
    assert october.total_label.text == "$20.00 of $400.00 · $100.00/week"
    assert october.last_month_label is None     # Weekly mode's month total doesn't change #
    assert september.total_label.text == "$130.00 of $400.00 · $100.00/week"


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
    assert popup.mode_choice.value == "monthly"
    assert popup.start_label.text == "Budget Starts On Day"
    assert popup.start_day_input_box in popup.mode_section.children
    assert popup.long_week_input_box in popup.mode_section.children
    assert popup.weekday_choice not in popup.mode_section.children


def test_budget_popup_prefills_weekly_mode(kivy_window):
    app = FakeApp(mode="weekly", start_weekday=6, weekly_max_history=[{"from": datetime(2020, 1, 5), "amount": 150.0}])
    popup = BudgetPopup(app)

    assert popup.max_input_box.text == "150.00"
    assert popup.mode_choice.value == "weekly"
    assert popup.weekday_choice.value == 6
    assert popup.start_label.text == "Weeks Start On"
    assert popup.mode_section.children == [popup.weekday_choice, popup.start_label]
    assert popup.period_label.text.startswith("This week:")


def test_budget_popup_switches_to_weekly_and_saves_the_weekday(kivy_window):
    app = FakeApp()
    popup = BudgetPopup(app)

    popup.mode_choice.buttons["weekly"].dispatch("on_release")
    assert popup.mode_section.children == [popup.weekday_choice, popup.start_label]

    popup.weekday_choice.buttons[6].dispatch("on_release")
    popup.save_budget()

    assert app.budget_updates == [({"mode": "weekly", "start_day": 15, "start_weekday": 6}, None, None)]
    assert app.errors == []


def test_choice_row_highlights_only_the_selected_option(kivy_window):
    from ui.choice_row import SELECTED_COLOR, UNSELECTED_COLOR

    popup = BudgetPopup(FakeApp())
    popup.weekday_choice.buttons[3].dispatch("on_release")

    colors = [tuple(btn.background_color) for btn in popup.weekday_choice.buttons.values()]
    assert colors == [UNSELECTED_COLOR] * 3 + [SELECTED_COLOR] + [UNSELECTED_COLOR] * 3
    assert popup.weekday_choice.value == 3


def test_budget_popup_weekly_mode_ignores_the_hidden_start_day(kivy_window):
    app = FakeApp(mode="weekly")
    popup = BudgetPopup(app)
    popup.start_day_input_box.text = "40"

    popup.save_budget()

    assert app.budget_updates == [({"mode": "weekly", "start_day": 15, "start_weekday": 0}, None, None)]
    assert app.errors == []


@pytest.fixture
def popup_now(monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 22, 9, 0)

    monkeypatch.setattr("ui.budget_popup.datetime", FixedDatetime)


def test_budget_popup_previews_the_long_week(kivy_window, popup_now):
    popup = BudgetPopup(FakeApp(start_day=1))

    assert popup.period_label.text == "Current period: Oct 1 – 31\nLong week: Oct 22 – 31 (10 days)"

    popup.start_day_input_box.text = "15"

    assert popup.period_label.text == "Current period: Oct 15 – Nov 14\nLong week: Nov 5 – 14 (10 days)"


def test_budget_popup_long_week_field_only_shows_for_monthly(kivy_window):
    popup = BudgetPopup(FakeApp())
    monthly_height = popup.height

    popup.mode_choice.value = "weekly"

    assert popup.long_week_input_box not in popup.mode_section.children
    assert popup.height < monthly_height


def test_budget_popup_prefills_and_saves_long_week_max(kivy_window):
    app = FakeApp(
        weekly_max_history=[{"from": datetime(2020, 1, 15), "amount": 150.0}],
        long_week_max_history=[{"from": datetime(2020, 1, 15), "amount": 200.0}]
    )
    popup = BudgetPopup(app)

    assert popup.long_week_input_box.text == "200.00"

    popup.long_week_input_box.text = "225"
    popup.save_budget()

    assert app.budget_updates == [({"mode": "monthly", "start_day": 15, "start_weekday": 0}, 150.0, 225.0)]


@pytest.mark.parametrize("long_week_max", ["0", "."])
def test_budget_popup_rejects_invalid_long_week_max(kivy_window, long_week_max):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.long_week_input_box.text = long_week_max

    popup.save_budget()

    assert app.budget_updates == []
    assert app.errors == ["Please enter a long week\nmax above $0."]


def test_budget_popup_weekly_mode_keeps_the_hidden_long_week_max(kivy_window):
    app = FakeApp(mode="weekly", long_week_max_history=[{"from": datetime(2020, 1, 5), "amount": 200.0}])
    popup = BudgetPopup(app)
    popup.long_week_input_box.text = "0"

    popup.save_budget()

    assert app.budget_updates == [({"mode": "weekly", "start_day": 15, "start_weekday": 0}, None, 200.0)]


def test_budget_popup_saves_valid_settings(kivy_window):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.max_input_box.text = "175.5"
    popup.start_day_input_box.text = "20"

    popup.save_budget()

    assert app.budget_updates == [({"mode": "monthly", "start_day": 20, "start_weekday": 0}, 175.5, None)]
    assert app.errors == []


def test_budget_popup_blank_max_means_no_limit(kivy_window):
    app = FakeApp()
    popup = BudgetPopup(app)
    popup.max_input_box.text = "   "

    popup.save_budget()

    assert app.budget_updates == [({"mode": "monthly", "start_day": 15, "start_weekday": 0}, None, None)]


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
    assert popup.long_week_input_box.input_type == "number"
    assert popup.long_week_input_box.input_filter == "float"


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


## CARRY-OVER POPUP ##

def _carry_span(amount=23.5):
    return {
        "start": WEEK_START,
        "end": WEEK_END,
        "spent": 150.0 - amount,
        "budget": 150.0,
        "carry_over": {"amount": amount, "over": amount < 0, "carried": False, "answered": False},
    }


def test_carry_over_popup_notes_last_week(kivy_window):
    from ui.carry_over_popup import CarryOverPopup
    from ui.color_utils import CONFIRM_COLOR

    popup = CarryOverPopup(FakeApp(), _carry_span(), {"start": WEEK_END}, mode="weekly")

    assert popup.title == "Under Budget"
    assert popup.message_label.text == (
        "You spent $126.50 of $150.00 last week.\n\nAdd the $23.50 you didn't spend to this week?"
    )
    assert popup.add_btn.text == "Add $23.50"
    assert tuple(popup.add_btn.background_color) == CONFIRM_COLOR
    assert popup.auto_dismiss is False


def test_carry_over_popup_offers_to_subtract_an_overspend(kivy_window):
    from ui.carry_over_popup import CarryOverPopup

    popup = CarryOverPopup(FakeApp(), _carry_span(-30.0), {"start": WEEK_END}, mode="weekly")

    assert popup.title == "Over Budget"
    assert popup.message_label.text == (
        "You spent $180.00 of $150.00 last week.\n\nSubtract the $30.00 you went over from this week?"
    )
    assert popup.add_btn.text == "Subtract $30.00"


def test_carry_over_popup_shows_a_negative_budget_with_the_minus_first(kivy_window):
    from ui.carry_over_popup import CarryOverPopup

    span = dict(_carry_span(-30.0), spent=0.0, budget=-30.0)
    popup = CarryOverPopup(FakeApp(), span, {"start": WEEK_END}, mode="weekly")

    assert popup.message_label.text.startswith("You spent $0.00 of -$30.00 last week.")


@pytest.mark.parametrize("amount, ending", [
    (80.0, "Add the $80.00 you didn't spend to this month? Each of its 4 weeks gets $20.00 more."),
    (-80.0, "Subtract the $80.00 you went over from this month? Each of its 4 weeks gets $20.00 less."),
])
def test_carry_over_popup_explains_the_monthly_split(kivy_window, amount, ending):
    from ui.carry_over_popup import CarryOverPopup

    popup = CarryOverPopup(FakeApp(), _carry_span(amount), {"weeks": [{}] * 4}, mode="monthly")

    assert popup.message_label.text.endswith("last month.\n\n" + ending)


@pytest.mark.parametrize("button, carried", [("add_btn", True), ("no_btn", False)])
def test_carry_over_popup_records_the_answer(kivy_window, button, carried):
    from ui.carry_over_popup import CarryOverPopup

    app = FakeApp()
    popup = CarryOverPopup(app, _carry_span(), {"start": WEEK_END}, mode="weekly")

    getattr(popup, button).dispatch("on_release")

    assert app.carry_over_choices == [(WEEK_START, WEEK_END, False, carried)]
