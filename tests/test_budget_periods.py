from datetime import datetime, timedelta

import pytest

from budget_periods import (
    carry_over_choice,
    format_money,
    format_period,
    format_range,
    history_periods,
    next_period_start,
    next_weekly_period_start,
    pending_carry_over,
    period_bounds,
    period_start,
    period_weeks,
    set_carry_over,
    set_weekly_max,
    summarize_week,
    week_start,
    week_summary,
    weekly_max_for,
    weekly_period_start,
)

FOOD = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
GAS = {"name": "Gas", "color": [0.3, 0.6, 0.9, 1]}


def make_entry(amount, timestamp, category=None):
    return {"amount": amount, "timestamp": timestamp, "category": category, "note": None}


def make_settings(mode="monthly", start_day=1, start_weekday=0, weekly_max_history=None,
                  long_week_max_history=None, carry_overs=None):
    return {
        "mode": mode,
        "start_day": start_day,
        "start_weekday": start_weekday,
        "weekly_max_history": weekly_max_history or [],
        "long_week_max_history": long_week_max_history or [],
        "carry_overs": carry_overs or [],
    }


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


## WEEKLY MODE BOUNDARIES ##

@pytest.mark.parametrize("moment, start_weekday, expected", [
    (datetime(2026, 10, 29, 15, 0), 0, datetime(2026, 10, 26)),    # Thursday, weeks start Monday #
    (datetime(2026, 10, 26, 0, 0), 0, datetime(2026, 10, 26)),     # Starts at midnight on the start weekday #
    (datetime(2026, 10, 25, 23, 59), 0, datetime(2026, 10, 19)),   # Sunday is the last day of a Monday week #
    (datetime(2026, 10, 29), 6, datetime(2026, 10, 25)),           # Weeks start Sunday #
    (datetime(2027, 1, 2), 0, datetime(2026, 12, 28)),             # Crosses the year boundary #
])
def test_week_start(moment, start_weekday, expected):
    assert week_start(moment, start_weekday) == expected


@pytest.mark.parametrize("moment, expected", [
    (datetime(2026, 10, 29), datetime(2026, 10, 5)),
    (datetime(2026, 11, 1, 20, 0), datetime(2026, 10, 5)),         # Its week started Oct 26, so it's October's #
    (datetime(2026, 10, 3), datetime(2026, 9, 7)),                 # Its week started Sep 28, so it's September's #
    (datetime(2026, 11, 2), datetime(2026, 11, 2)),
    (datetime(2027, 1, 2), datetime(2026, 12, 7)),
])
def test_weekly_period_start_is_the_month_the_week_starts_in(moment, expected):
    assert weekly_period_start(moment, 0) == expected


def test_next_weekly_period_start_is_next_months_first_start_weekday():
    assert next_weekly_period_start(datetime(2026, 10, 5), 0) == datetime(2026, 11, 2)
    assert next_weekly_period_start(datetime(2026, 12, 7), 0) == datetime(2027, 1, 4)
    assert next_weekly_period_start(datetime(2026, 10, 4), 6) == datetime(2026, 11, 1)  # Nov 1 is a Sunday #


def test_weekly_period_weeks_are_all_seven_days_four_or_five_of_them():
    october = period_weeks(*period_bounds(datetime(2026, 10, 29), make_settings("weekly")))
    november = period_weeks(*period_bounds(datetime(2026, 11, 20), make_settings("weekly")))

    assert [(we - ws).days for ws, we in october] == [7, 7, 7, 7]
    assert [(we - ws).days for ws, we in november] == [7, 7, 7, 7, 7]
    assert november[0][0] == datetime(2026, 11, 2)
    assert november[-1][1] == datetime(2026, 12, 7)
    assert all(ws.weekday() == 0 for ws, we in october + november)


def test_period_bounds_follows_the_mode():
    moment = datetime(2026, 10, 29)

    assert period_bounds(moment, make_settings("monthly", start_day=15)) == (datetime(2026, 10, 15), datetime(2026, 11, 15))
    assert period_bounds(moment, make_settings("weekly", start_day=15)) == (datetime(2026, 10, 5), datetime(2026, 11, 2))
    assert period_bounds(moment, make_settings("weekly", start_weekday=6)) == (datetime(2026, 10, 4), datetime(2026, 11, 1))


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


def test_summarize_week_adds_carried_in_budget():
    week = summarize_week([make_entry(30.0, WEEK_START)], WEEK_START, WEEK_END, 100.0, datetime(2026, 11, 1), carried_in=25.0)

    assert week["weekly_max"] == 100.0
    assert week["carried_in"] == 25.0
    assert week["budget"] == 125.0
    assert week["left"] == 95.0


def test_summarize_week_ignores_carried_in_without_a_max():
    week = summarize_week([], WEEK_START, WEEK_END, None, datetime(2026, 11, 1), carried_in=25.0)

    assert week["carried_in"] == 0
    assert week["budget"] is None
    assert week["left"] is None


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

    periods = history_periods(transactions, make_settings(start_day=15, weekly_max_history=history), datetime(2026, 10, 22, 9, 0))

    assert [p["start"] for p in periods] == [datetime(2026, 8, 15), datetime(2026, 9, 15), datetime(2026, 10, 15)]
    assert periods[-1]["end"] == datetime(2026, 11, 15)
    assert all(len(p["weeks"]) == 4 for p in periods)
    assert all(p["weekly_max"] == 150.0 for p in periods)
    assert periods[0]["weeks"][0]["spent"] == 12.0
    assert [w["status"] for w in periods[-1]["weeks"]] == ["past", "current", "upcoming", "upcoming"]


def test_history_periods_without_transactions_is_just_the_current_period():
    periods = history_periods([], make_settings(), datetime(2026, 10, 22))

    assert len(periods) == 1
    assert periods[0]["start"] == datetime(2026, 10, 1)
    assert periods[0]["weekly_max"] is None


def test_history_periods_in_weekly_mode_groups_weeks_by_month():
    transactions = [make_entry(12.0, datetime(2026, 10, 1)), make_entry(3.0, datetime(2026, 11, 1), FOOD)]
    history = [{"from": datetime(2026, 9, 7), "amount": 150.0}]

    periods = history_periods(transactions, make_settings("weekly", weekly_max_history=history), datetime(2026, 11, 20))

    assert [p["start"] for p in periods] == [datetime(2026, 9, 7), datetime(2026, 10, 5), datetime(2026, 11, 2)]
    assert [len(p["weeks"]) for p in periods] == [4, 4, 5]
    assert periods[0]["weeks"][-1]["spent"] == 12.0      # Oct 1 is in the week starting Sep 28 #
    assert periods[1]["weeks"][-1]["spent"] == 3.0       # Nov 1 is in the week starting Oct 26 #
    assert [w["status"] for w in periods[-1]["weeks"]] == ["past", "past", "current", "upcoming", "upcoming"]


## LONG WEEK MAX ##

def test_long_week_max_applies_to_monthly_modes_long_last_week():
    settings = make_settings(
        start_day=15,
        weekly_max_history=[{"from": datetime(2026, 10, 15), "amount": 150.0}],
        long_week_max_history=[{"from": datetime(2026, 10, 15), "amount": 200.0}],
    )

    period = history_periods([], settings, datetime(2026, 10, 22))[-1]

    assert [w["budget"] for w in period["weeks"]] == [150.0, 150.0, 150.0, 200.0]
    assert period["budget"] == 650.0


def test_long_week_max_skips_a_last_week_that_is_only_seven_days():
    settings = make_settings(
        weekly_max_history=[{"from": datetime(2026, 2, 1), "amount": 150.0}],
        long_week_max_history=[{"from": datetime(2026, 2, 1), "amount": 200.0}],
    )

    period = history_periods([], settings, datetime(2026, 2, 10))[-1]

    assert [w["budget"] for w in period["weeks"]] == [150.0] * 4


def test_long_week_max_is_ignored_without_a_weekly_max_or_in_weekly_mode():
    long_max = [{"from": datetime(2026, 10, 1), "amount": 200.0}]

    monthly = history_periods([], make_settings(long_week_max_history=long_max), datetime(2026, 10, 22))[-1]
    weekly = history_periods([], make_settings("weekly", weekly_max_history=[{"from": datetime(2026, 10, 5), "amount": 150.0}],
                                               long_week_max_history=long_max), datetime(2026, 10, 22))[-1]

    assert [w["budget"] for w in monthly["weeks"]] == [None] * 4
    assert [w["budget"] for w in weekly["weeks"]] == [150.0] * 4


## CARRY-OVERS ##

WEEKLY_MAX_100 = [{"from": datetime(2026, 9, 7), "amount": 100.0}]
OCT_5, OCT_12, OCT_19, OCT_26 = (datetime(2026, 10, d) for d in (5, 12, 19, 26))


def answer(start, end, carried=True, over=False, mode="weekly"):
    return {"mode": mode, "start": start, "end": end, "over": over, "carried": carried}


def weekly_weeks(transactions, carry_overs, now=datetime(2026, 10, 22), mode="weekly"):
    settings = make_settings(mode, weekly_max_history=WEEKLY_MAX_100, carry_overs=carry_overs)
    return {w["start"]: w for p in history_periods(transactions, settings, now) for w in p["weeks"]}


def test_set_carry_over_replaces_an_earlier_answer_for_the_same_mode_only():
    carry_overs = set_carry_over([], "monthly", datetime(2026, 9, 1), datetime(2026, 10, 1), False, True)
    carry_overs = set_carry_over(carry_overs, "weekly", OCT_5, OCT_12, False, False)
    carry_overs = set_carry_over(carry_overs, "weekly", OCT_5, OCT_12, True, True)

    assert carry_overs == [
        answer(datetime(2026, 9, 1), datetime(2026, 10, 1), mode="monthly"),
        answer(OCT_5, OCT_12, over=True),
    ]
    assert carry_over_choice(carry_overs, "weekly", OCT_5, OCT_12, True) is True
    assert carry_over_choice(carry_overs, "weekly", OCT_5, OCT_12, False) is None     # That answer was about overspending #
    assert carry_over_choice(carry_overs, "monthly", OCT_5, OCT_12, True) is None


def test_weekly_carry_over_adds_what_was_left_onto_the_next_week_and_chains():
    transactions = [make_entry(70.0, datetime(2026, 10, 6)), make_entry(50.0, datetime(2026, 10, 13))]

    weeks = weekly_weeks(transactions, [answer(OCT_5, OCT_12), answer(OCT_12, OCT_19)])

    assert weeks[OCT_5]["carry_over"] == {"amount": 30.0, "over": False, "carried": True, "answered": True}
    assert weeks[OCT_12]["carried_in"] == 30.0
    assert weeks[OCT_12]["left"] == 80.0
    assert weeks[OCT_19]["carried_in"] == 80.0      # 30 from the first week rides along #
    assert weeks[OCT_19]["budget"] == 180.0
    assert weeks[OCT_19]["carry_over"] is None      # Current week; it hasn't finished yet #
    assert weeks[OCT_26]["carried_in"] == 0


def test_declined_carry_over_adds_nothing_but_counts_as_answered():
    weeks = weekly_weeks([make_entry(70.0, datetime(2026, 10, 6))], [answer(OCT_5, OCT_12, carried=False)])

    assert weeks[OCT_5]["carry_over"] == {"amount": 30.0, "over": False, "carried": False, "answered": True}
    assert weeks[OCT_12]["carried_in"] == 0


def test_weekly_overspend_can_be_subtracted_from_the_next_week():
    weeks = weekly_weeks([make_entry(130.0, datetime(2026, 10, 6))], [answer(OCT_5, OCT_12, over=True)])

    assert weeks[OCT_5]["carry_over"] == {"amount": -30.0, "over": True, "carried": True, "answered": True}
    assert weeks[OCT_12]["carried_in"] == -30.0
    assert weeks[OCT_12]["budget"] == 70.0
    assert weeks[OCT_12]["left"] == 70.0


def test_a_big_overspend_can_leave_the_next_week_below_zero_and_carry_on():
    weeks = weekly_weeks([make_entry(230.0, datetime(2026, 10, 6))], [answer(OCT_5, OCT_12, over=True)])

    assert weeks[OCT_12]["budget"] == -30.0
    assert weeks[OCT_12]["carry_over"] == {"amount": -30.0, "over": True, "carried": False, "answered": False}


def test_moving_money_between_weeks_of_the_same_month_leaves_its_total_alone():
    transactions = [make_entry(130.0, datetime(2026, 10, 6)), make_entry(70.0, datetime(2026, 10, 13))]
    settings = make_settings("weekly", weekly_max_history=WEEKLY_MAX_100, carry_overs=[
        answer(OCT_5, OCT_12, over=True),       # Week 1's $30 overspend comes off week 2 #
        answer(OCT_12, OCT_19),                 # Week 2's leftover goes onto week 3 #
    ])

    october = history_periods(transactions, settings, datetime(2026, 10, 29))[-1]

    assert [w["budget"] for w in october["weeks"]] == [100.0, 70.0, 100.0, 100.0]
    assert october["budget"] == 400.0
    assert october["left"] == 200.0             # $400 given, $200 spent, however it's moved around #


@pytest.mark.parametrize("amount, over", [(60.0, False), (130.0, True)])
def test_weekly_month_total_ignores_money_from_last_months_final_week(amount, over):
    # The week of Sep 28 starts in September, so its amount moves across the month line into Oct 5's week #
    transactions = [make_entry(amount, datetime(2026, 9, 29))]
    settings = make_settings("weekly", weekly_max_history=WEEKLY_MAX_100,
                             carry_overs=[answer(datetime(2026, 9, 28), OCT_5, over=over)])

    september, october = history_periods(transactions, settings, datetime(2026, 10, 29))

    assert october["weeks"][0]["carried_in"] == 100.0 - amount
    assert october["carried_in"] == 0
    assert october["budget"] == 400.0
    assert september["budget"] == 400.0


def test_carry_over_answer_lapses_if_later_edits_flip_the_week_over_budget():
    carry_overs = [answer(OCT_5, OCT_12)]

    under = weekly_weeks([make_entry(70.0, datetime(2026, 10, 6))], carry_overs)
    over = weekly_weeks([make_entry(70.0, datetime(2026, 10, 6)), make_entry(45.0, datetime(2026, 10, 9))], carry_overs)

    assert under[OCT_12]["carried_in"] == 30.0
    assert over[OCT_5]["carry_over"] == {"amount": -15.0, "over": True, "carried": False, "answered": False}
    assert over[OCT_12]["carried_in"] == 0


def test_no_carry_over_for_weeks_before_tracking_began():
    weeks = weekly_weeks([make_entry(70.0, datetime(2026, 10, 13))], [])

    assert weeks[OCT_5]["carry_over"] is None       # Nothing was logged until the week after #
    assert weeks[OCT_12]["carry_over"] == {"amount": 30.0, "over": False, "carried": False, "answered": False}


def test_monthly_carry_over_is_split_evenly_over_next_months_weeks():
    settings = make_settings(
        weekly_max_history=[{"from": datetime(2026, 9, 1), "amount": 100.0}],
        carry_overs=[answer(datetime(2026, 9, 1), datetime(2026, 10, 1), mode="monthly")],
    )

    september, october = history_periods([make_entry(300.0, datetime(2026, 9, 3))], settings, datetime(2026, 10, 22))

    assert september["carry_over"] == {"amount": 100.0, "over": False, "carried": True, "answered": True}
    assert all(w["carry_over"] is None for w in september["weeks"])     # Monthly mode carries whole months #
    assert [w["carried_in"] for w in october["weeks"]] == [25.0] * 4
    assert october["carried_in"] == 100.0
    assert october["budget"] == 500.0
    assert october["carry_over"] is None


def test_monthly_overspend_is_subtracted_evenly_from_next_months_weeks():
    settings = make_settings(
        weekly_max_history=[{"from": datetime(2026, 9, 1), "amount": 100.0}],
        carry_overs=[answer(datetime(2026, 9, 1), datetime(2026, 10, 1), over=True, mode="monthly")],
    )

    september, october = history_periods([make_entry(500.0, datetime(2026, 9, 3))], settings, datetime(2026, 10, 22))

    assert september["carry_over"]["amount"] == -100.0
    assert [w["carried_in"] for w in october["weeks"]] == [-25.0] * 4
    assert october["budget"] == 300.0


def test_each_mode_keeps_its_own_carry_overs():
    transactions = [make_entry(70.0, datetime(2026, 9, 8)), make_entry(60.0, datetime(2026, 10, 6))]
    weekly_answer = answer(OCT_5, OCT_12)
    september = (datetime(2026, 9, 1), datetime(2026, 10, 1))

    weekly = weekly_weeks(transactions, [weekly_answer])
    monthly = weekly_weeks(transactions, [weekly_answer], mode="monthly")
    back_to_weekly = weekly_weeks(transactions, [weekly_answer, answer(*september, mode="monthly")])

    assert weekly[OCT_12]["carried_in"] == 40.0
    assert all(w["carried_in"] == 0 for w in monthly.values())             # Switching resets... #
    assert back_to_weekly[OCT_12]["carried_in"] == 40.0                     # ...until switching back #
    assert weekly_weeks(transactions, [answer(OCT_5, OCT_12, mode="monthly")])[OCT_12]["carried_in"] == 0


def test_pending_carry_over_is_last_week_until_answered():
    settings = make_settings("weekly", weekly_max_history=WEEKLY_MAX_100)
    transactions = [make_entry(60.0, datetime(2026, 10, 13))]

    last, current = pending_carry_over(transactions, settings, datetime(2026, 10, 22))
    assert (last["start"], last["carry_over"]["amount"]) == (OCT_12, 40.0)
    assert current["start"] == OCT_19

    settings["carry_overs"] = [answer(OCT_12, OCT_19, carried=False)]
    assert pending_carry_over(transactions, settings, datetime(2026, 10, 22)) is None


def test_pending_carry_over_offers_to_subtract_an_overspend():
    settings = make_settings("weekly", weekly_max_history=WEEKLY_MAX_100)

    last, current = pending_carry_over([make_entry(160.0, datetime(2026, 10, 13))], settings, datetime(2026, 10, 22))

    assert last["carry_over"] == {"amount": -60.0, "over": True, "carried": False, "answered": False}


def test_pending_carry_over_skips_weeks_on_budget_or_without_a_max():
    on_budget = [make_entry(100.0, datetime(2026, 10, 13))]
    under = [make_entry(60.0, datetime(2026, 10, 13))]

    assert pending_carry_over(on_budget, make_settings("weekly", weekly_max_history=WEEKLY_MAX_100), datetime(2026, 10, 22)) is None
    assert pending_carry_over(under, make_settings("weekly"), datetime(2026, 10, 22)) is None


def test_pending_carry_over_in_monthly_mode_is_last_month():
    settings = make_settings(weekly_max_history=[{"from": datetime(2026, 9, 1), "amount": 100.0}])

    last, current = pending_carry_over([make_entry(300.0, datetime(2026, 9, 3))], settings, datetime(2026, 10, 22))

    assert (last["start"], last["carry_over"]["amount"]) == (datetime(2026, 9, 1), 100.0)
    assert len(current["weeks"]) == 4


def test_week_summary_includes_carried_in_budget():
    settings = make_settings("weekly", weekly_max_history=WEEKLY_MAX_100, carry_overs=[answer(OCT_12, OCT_19)])

    week = week_summary([make_entry(60.0, datetime(2026, 10, 13))], settings, OCT_19, datetime(2026, 10, 22))

    assert week["carried_in"] == 40.0
    assert week["left"] == 140.0
    assert week_summary([], settings, datetime(2026, 1, 5), datetime(2026, 10, 22))["start"] == datetime(2026, 1, 5)


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


def test_format_money_puts_the_minus_before_the_dollar_sign():
    assert format_money(12.5) == "$12.50"
    assert format_money(-30) == "-$30.00"


def test_format_period_names_weekly_periods_by_month():
    assert format_period(datetime(2026, 10, 5), datetime(2026, 11, 2), "weekly", with_year=True) == "October 2026"
    assert format_period(datetime(2026, 10, 5), datetime(2026, 11, 2), "weekly") == "October"
    assert format_period(datetime(2026, 10, 15), datetime(2026, 11, 15), "monthly", with_year=True) == "Oct 15 – Nov 14, 2026"
