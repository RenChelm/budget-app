from calendar import monthrange
from datetime import datetime, timedelta

## PERIOD BOUNDARIES (MONTHLY: PERIODS START ON A DAY OF THE MONTH) ##

def _month_day(year, month, day):
    # Start days past the end of a short month fall back to its last day (31st -> Feb 28) #
    return datetime(year, month, min(day, monthrange(year, month)[1]))

def _shift_month(year, month, delta):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1

def period_start(moment, start_day):
    start = _month_day(moment.year, moment.month, start_day)
    if moment < start:
        start = _month_day(*_shift_month(moment.year, moment.month, -1), start_day)
    return start

def next_period_start(start, start_day):
    return _month_day(*_shift_month(start.year, start.month, 1), start_day)

## PERIOD BOUNDARIES (WEEKLY: EVERY WEEK IS 7 DAYS, STARTING ON A WEEKDAY) ##

def week_start(moment, start_weekday):
    # Midnight on the most recent start weekday (0 = Monday) #
    day = datetime(moment.year, moment.month, moment.day)
    return day - timedelta(days=(day.weekday() - start_weekday) % 7)

def _first_week_start(year, month, start_weekday):
    # Weeks belong to the month they start in, so a month's weeks begin on its first start weekday #
    first = datetime(year, month, 1)
    return first + timedelta(days=(start_weekday - first.weekday()) % 7)

def weekly_period_start(moment, start_weekday):
    week = week_start(moment, start_weekday)
    return _first_week_start(week.year, week.month, start_weekday)

def next_weekly_period_start(start, start_weekday):
    return _first_week_start(*_shift_month(start.year, start.month, 1), start_weekday)

## PERIOD BOUNDARIES (EITHER MODE) ##

def period_bounds(moment, settings):
    # The (start, end) of the budget period holding `moment` #
    if settings["mode"] == "weekly":
        start = weekly_period_start(moment, settings["start_weekday"])
        return start, next_weekly_period_start(start, settings["start_weekday"])
    start = period_start(moment, settings["start_day"])
    return start, next_period_start(start, settings["start_day"])

def period_weeks(start, end):
    # Monthly periods are 28-31 days, so week 4 absorbs the leftover days (7-10 days long) #
    # Weekly-mode periods are already whole weeks, 4 or 5 of them #
    bounds = [start + timedelta(weeks=i) for i in range((end - start).days // 7)] + [end]
    return list(zip(bounds, bounds[1:]))

## WEEKLY MAX ##

def weekly_max_for(start, weekly_max_history):
    # A change applies from the period it was made in onward, so older periods keep their old max #
    # The earliest setting also covers periods from before the budget was first set #
    # The long week max (monthly mode) keeps its own history the same way #
    if not weekly_max_history:
        return None
    applicable = [change for change in weekly_max_history if change["from"] <= start]
    return (applicable[-1] if applicable else weekly_max_history[0])["amount"]

def set_weekly_max(weekly_max_history, start, amount):
    if weekly_max_for(start, weekly_max_history) == amount:
        return weekly_max_history
    kept = [change for change in weekly_max_history if change["from"] < start]
    return kept + [{"from": start, "amount": amount}]

## CARRY-OVERS ##
# A finished week (weekly mode) or period (monthly mode) can move what was left onto the next one, #
# or subtract what was overspent from it #

def carry_over_choice(carry_overs, mode, start, end, over):
    # True if carried onto the next week/period, False if declined, None if never asked #
    # Each mode keeps its own answers, so switching back to a mode brings them back #
    for choice in carry_overs:
        if (choice["mode"], choice["start"], choice["end"], choice["over"]) == (mode, start, end, over):
            return choice["carried"]
    return None

def set_carry_over(carry_overs, mode, start, end, over, carried):
    # One answer per week/period; it's about a leftover or an overspend, so it's asked again if that flips #
    kept = [choice for choice in carry_overs if (choice["mode"], choice["start"], choice["end"]) != (mode, start, end)]
    return kept + [{"mode": mode, "start": start, "end": end, "over": over, "carried": carried}]

def _carry_over(span, oldest, settings):
    # Offered once a week/period has finished above or below budget, as long as tracking had begun #
    # The amount is worked out live, so adding a missed transaction later changes what carries over #
    if span["status"] != "past" or span["left"] is None or round(span["left"], 2) == 0 or oldest >= span["end"]:
        return None
    amount = round(span["left"], 2)  # Negative when overspent #
    choice = carry_over_choice(settings["carry_overs"], settings["mode"], span["start"], span["end"], amount < 0)
    return {"amount": amount, "over": amount < 0, "carried": choice is True, "answered": choice is not None}

def _carried(span):
    carry_over = span["carry_over"]
    return carry_over["amount"] if carry_over and carry_over["carried"] else 0

## SUMMARIES ##

def _status(start, end, now):
    if now < start:
        return "upcoming"
    if now >= end:
        return "past"
    return "current"

def summarize_week(transactions, start, end, weekly_max, now, carried_in=0):
    entries = [entry for entry in transactions if start <= entry["timestamp"] < end]
    spent = sum(entry["amount"] for entry in entries)

    # Uncategorized entries group under None #
    totals = {}
    for entry in entries:
        category = entry.get("category")
        name = category["name"] if category else None
        if name not in totals:
            totals[name] = {"name": name, "color": category["color"] if category else None, "amount": 0}
        totals[name]["amount"] += entry["amount"]

    top = max(totals.values(), key=lambda total: total["amount"], default=None)
    if top is None or top["amount"] <= 0 or spent <= 0:
        top = None

    status = _status(start, end, now)
    today = datetime(now.year, now.month, now.day)

    # `carried_in` is budget moved over from an earlier week/period (negative if it went over); it needs a max set #
    carried_in = carried_in if weekly_max is not None else 0
    budget = weekly_max + carried_in if weekly_max is not None else None

    return {
        "start": start,
        "end": end,
        "status": status,
        "spent": spent,
        "count": len(entries),
        "weekly_max": weekly_max,
        "carried_in": carried_in,
        "budget": budget,
        "left": budget - spent if budget is not None else None,
        "days_left": (end - today).days if status == "current" else 0,
        "top_category": top,
        "top_share": min(top["amount"] / spent, 1) if top else 0,
    }

def history_periods(transactions, settings, now, since=None):
    # Every period from the one holding the oldest transaction (or `since`, if earlier) through the current one #
    # Carry-overs make each budget depend on the one before, so they're worked out oldest first #
    oldest = min((entry["timestamp"] for entry in transactions), default=now)
    current = period_bounds(now, settings)[0]
    start = period_bounds(min(oldest, now, since or now), settings)[0]
    weekly = settings["mode"] == "weekly"

    periods = []
    carry = 0  # What was left of the last week (weekly mode) or period (monthly mode), if it's being added on #
    while start <= current:
        end = period_bounds(start, settings)[1]
        weekly_max = weekly_max_for(start, settings["weekly_max_history"])
        long_week_max = weekly_max_for(start, settings["long_week_max_history"])
        bounds = period_weeks(start, end)
        share = carry / len(bounds)  # Monthly mode splits it evenly over the period's weeks #

        weeks = []
        for ws, we in bounds:
            if weekly:
                week = summarize_week(transactions, ws, we, weekly_max, now, carry)
                week["carry_over"] = _carry_over(week, oldest, settings)
                carry = _carried(week)
            else:
                # The last week can be 8-10 days long and may have its own max #
                use_long = (we - ws).days > 7 and weekly_max is not None and long_week_max is not None
                week = summarize_week(transactions, ws, we, long_week_max if use_long else weekly_max, now, share)
                week["carry_over"] = None
            weeks.append(week)

        # Weekly mode's months only group weeks, so moving money between weeks never changes the total, even into #
        # a month's first week; the overspend or leftover already counts where it happened. Monthly mode's month #
        # is the budget itself, so last month's amount added or subtracted does change it #
        spent = sum(week["spent"] for week in weeks)
        incoming = 0 if weekly else sum(week["carried_in"] for week in weeks)
        budget = sum(week["weekly_max"] for week in weeks) + incoming if weekly_max is not None else None
        period = {
            "start": start,
            "end": end,
            "status": _status(start, end, now),
            "weekly_max": weekly_max,
            "spent": spent,
            "budget": budget,
            "carried_in": incoming,
            "left": budget - spent if budget is not None else None,
            "weeks": weeks,
        }
        period["carry_over"] = None if weekly else _carry_over(period, oldest, settings)
        if not weekly:
            carry = _carried(period)

        periods.append(period)
        start = end
    return periods

def week_summary(transactions, settings, start, now):
    # One week's summary taken from the full history, so it includes any carried-over budget #
    for period in history_periods(transactions, settings, now, since=start):
        for week in period["weeks"]:
            if week["start"] == start:
                return week
    return None

def pending_carry_over(transactions, settings, now):
    # The week (weekly mode) or period (monthly mode) that just ended over or under budget and hasn't been asked about, #
    # paired with the current one it would be added to #
    periods = history_periods(transactions, settings, now)
    if settings["mode"] == "weekly":
        spans = [week for period in periods for week in period["weeks"] if week["status"] != "upcoming"]
    else:
        spans = periods

    if len(spans) < 2 or spans[-2]["carry_over"] is None or spans[-2]["carry_over"]["answered"]:
        return None
    return spans[-2], spans[-1]

## FORMATTING ##

def format_money(amount):
    return f"-${-amount:.2f}" if amount < 0 else f"${amount:.2f}"

def format_range(start, end, with_year=False):
    # `end` is exclusive (midnight after the last day), so show the day before it #
    last = end - timedelta(days=1)
    first_text = f"{start:%b} {start.day}"

    if with_year and start.year != last.year:
        return f"{first_text}, {start.year} – {last:%b} {last.day}, {last.year}"

    last_text = str(last.day) if (start.year, start.month) == (last.year, last.month) else f"{last:%b} {last.day}"
    return f"{first_text} – {last_text}" + (f", {last.year}" if with_year else "")

def format_period(start, end, mode, with_year=False):
    # Weekly-mode periods are named after the month their weeks start in #
    if mode == "weekly":
        return f"{start:%B %Y}" if with_year else f"{start:%B}"
    return format_range(start, end, with_year)
