from datetime import datetime, timedelta

import pytest

from budget_periods import (
    format_range,
    history_periods,
    next_period_start,
    period_start,
    period_weeks,
    set_weekly_max,
    summarize_week,
    weekly_max_for,
)

FOOD = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
GAS = {"name": "Gas", "color": [0.3, 0.6, 0.9, 1]}


def make_entry(amount, timestamp, category=None):
    return {"amount": amount, "timestamp": timestamp, "category": category, "note": None}


## PERIOD BOUNDARIES ##

@pytest.mark.parametrize("moment, expected", [
    (datetime(2026, 10, 22, 9, 30), datetime(2026, 10, 15)),
    (datetime(2026, 10, 15, 0, 0), datetime(2026, 10, 15)),        # Starts at midnight on the start day #
    (datetime(2026, 10, 14, 23, 59), datetime(2026, 9, 15)),       # Last minute of the previous period #
    (datetime(2027, 1, 3), datetime(2026, 12, 15)),                # Crosses the year boundary #
])
def test_period_start_on_the_15th(moment, expected):
    assert period_start(moment, 15) == expected


@pytest.mark.parametrize("moment, expected", [
    (datetime(2026, 2, 10), datetime(2026, 1, 31)),
    (datetime(2026, 2, 28, 8, 0), datetime(2026, 2, 28)),          # 31st falls back to Feb 28 #
    (datetime(2026, 3, 15), datetime(2026, 2, 28)),
    (datetime(2028, 2, 29, 8, 0), datetime(2028, 2, 29)),          # Leap year #
    (datetime(2026, 4, 30), datetime(2026, 4, 30)),
])
def test_period_start_clamps_start_day_to_short_months(moment, expected):
    assert period_start(moment, 31) == expected


def test_next_period_start_returns_to_full_start_day_after_short_month():
    assert next_period_start(datetime(2026, 2, 28), 31) == datetime(2026, 3, 31)
    assert next_period_start(datetime(2026, 12, 15), 15) == datetime(2027, 1, 15)


def test_period_weeks_gives_leftover_days_to_week_four():
    start = datetime(2026, 10, 15)
    weeks = period_weeks(start, next_period_start(start, 15))

    assert [(we - ws).days for ws, we in weeks] == [7, 7, 7, 10]
    assert weeks[0][0] == start
    assert weeks[-1][1] == datetime(2026, 11, 15)


def test_period_weeks_in_february_are_all_seven_days():
    start = datetime(2026, 2, 1)
    weeks = period_weeks(start, next_period_start(start, 1))

    assert [(we - ws).days for ws, we in weeks] == [7, 7, 7, 7]


## WEEKLY MAX ##

def test_weekly_max_for_without_history_is_none():
    assert weekly_max_for(datetime(2026, 10, 15), []) is None


def test_weekly_max_for_uses_the_change_in_effect():
    history = [
        {"from": datetime(2026, 9, 15), "amount": 150.0},
        {"from": datetime(2026, 11, 15), "amount": 200.0},
    ]

    assert weekly_max_for(datetime(2026, 7, 15), history) == 150.0    # Earliest also covers older periods #
    assert weekly_max_for(datetime(2026, 10, 15), history) == 150.0
    assert weekly_max_for(datetime(2026, 11, 15), history) == 200.0


def test_set_weekly_max_keeps_past_periods_and_replaces_same_period_edits():
    history = set_weekly_max([], datetime(2026, 9, 15), 150.0)
    history = set_weekly_max(history, datetime(2026, 10, 15), 175.0)
    history = set_weekly_max(history, datetime(2026, 10, 15), 200.0)

    assert history == [
        {"from": datetime(2026, 9, 15), "amount": 150.0},
        {"from": datetime(2026, 10, 15), "amount": 200.0},
    ]


def test_set_weekly_max_skips_unchanged_amount():
    history = [{"from": datetime(2026, 9, 15), "amount": 150.0}]

    assert set_weekly_max(history, datetime(2026, 10, 15), 150.0) is history


def test_set_weekly_max_can_clear_the_limit():
    history = set_weekly_max([{"from": datetime(2026, 9, 15), "amount": 150.0}], datetime(2026, 10, 15), None)

    assert weekly_max_for(datetime(2026, 10, 15), history) is None
    assert weekly_max_for(datetime(2026, 9, 15), history) == 150.0


## WEEK SUMMARY ##

WEEK_START, WEEK_END = datetime(2026, 10, 15), datetime(2026, 10, 22)


def test_summarize_week_totals_only_entries_inside_the_week():
    transactions = [
        make_entry(10.0, WEEK_START - timedelta(minutes=1)),
        make_entry(20.0, WEEK_START, FOOD),
        make_entry(30.0, WEEK_END - timedelta(minutes=1), FOOD),
        make_entry(40.0, WEEK_END),
    ]

    week = summarize_week(transactions, WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1))

    assert week["spent"] == 50.0
    assert week["count"] == 2
    assert week["left"] == 50.0
    assert week["status"] == "past"


def test_summarize_week_picks_top_category_by_amount():
    transactions = [
        make_entry(5.0, WEEK_START, FOOD),
        make_entry(5.0, WEEK_START, FOOD),
        make_entry(30.0, WEEK_START, GAS),
    ]

    week = summarize_week(transactions, WEEK_START, WEEK_END, None, datetime(2026, 11, 1))

    assert week["top_category"]["name"] == "Gas"
    assert week["top_category"]["color"] == GAS["color"]
    assert week["top_share"] == pytest.approx(0.75)
    assert week["left"] is None


def test_summarize_week_groups_uncategorized_entries():
    transactions = [make_entry(8.0, WEEK_START), make_entry(4.0, WEEK_START), make_entry(10.0, WEEK_START, FOOD)]

    week = summarize_week(transactions, WEEK_START, WEEK_END, None, datetime(2026, 11, 1))

    assert week["top_category"] == {"name": None, "color": None, "amount": 12.0}


def test_summarize_week_with_no_spending_has_no_top_category():
    week = summarize_week([], WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1))

    assert week["top_category"] is None
    assert week["spent"] == 0
    assert week["left"] == 100.0


def test_summarize_week_reports_overspending_as_negative_left():
    week = summarize_week([make_entry(130.0, WEEK_START)], WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1))

    assert week["left"] == -30.0


@pytest.mark.parametrize("now, status, days_left", [
    (datetime(2026, 10, 14, 23, 0), "upcoming", 0),
    (datetime(2026, 10, 15, 8, 0), "current", 7),
    (datetime(2026, 10, 21, 23, 0), "current", 1),     # Last day still counts today #
    (datetime(2026, 10, 22, 0, 0), "past", 0),
])
def test_summarize_week_status_and_days_left(now, status, days_left):
    week = summarize_week([], WEEK_START, WEEK_END, 100.0, now)

    assert week["status"] == status
    assert week["days_left"] == days_left


## HISTORY ##

def test_history_periods_runs_from_oldest_transaction_to_current_period():
    transactions = [make_entry(12.0, datetime(2026, 8, 20)), make_entry(3.0, datetime(2026, 10, 16), FOOD)]
    history = [{"from": datetime(2026, 9, 15), "amount": 150.0}]

    periods = history_periods(transactions, 15, history, datetime(2026, 10, 22, 9, 0))

    assert [p["start"] for p in periods] == [datetime(2026, 8, 15), datetime(2026, 9, 15), datetime(2026, 10, 15)]
    assert periods[-1]["end"] == datetime(2026, 11, 15)
    assert all(len(p["weeks"]) == 4 for p in periods)
    assert all(p["weekly_max"] == 150.0 for p in periods)
    assert periods[0]["weeks"][0]["spent"] == 12.0
    assert [w["status"] for w in periods[-1]["weeks"]] == ["past", "current", "upcoming", "upcoming"]


def test_history_periods_without_transactions_is_just_the_current_period():
    periods = history_periods([], 1, [], datetime(2026, 10, 22))

    assert len(periods) == 1
    assert periods[0]["start"] == datetime(2026, 10, 1)
    assert periods[0]["weekly_max"] is None


## FORMATTING ##

@pytest.mark.parametrize("start, end, with_year, expected", [
    (datetime(2026, 10, 15), datetime(2026, 10, 22), False, "Oct 15 – 21"),
    (datetime(2026, 10, 29), datetime(2026, 11, 5), False, "Oct 29 – Nov 4"),
    (datetime(2026, 10, 15), datetime(2026, 11, 15), True, "Oct 15 – Nov 14, 2026"),
    (datetime(2026, 10, 1), datetime(2026, 11, 1), True, "Oct 1 – 31, 2026"),
    (datetime(2026, 12, 15), datetime(2027, 1, 15), True, "Dec 15, 2026 – Jan 14, 2027"),
    (datetime(2026, 12, 29), datetime(2027, 1, 5), False, "Dec 29 – Jan 4"),
])
def test_format_range(start, end, with_year, expected):
    assert format_range(start, end, with_year) == expected
