from calendar import monthrange
from datetime import datetime, timedelta

WEEKS_PER_PERIOD = 4

## PERIOD BOUNDARIES ##

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

def period_weeks(start, end):
    # Periods are 28-31 days, so the last week absorbs the leftover days (7-10 days long) #
    bounds = [start + timedelta(weeks=i) for i in range(WEEKS_PER_PERIOD)] + [end]
    return list(zip(bounds, bounds[1:]))

## WEEKLY MAX ##

def weekly_max_for(start, weekly_max_history):
    # A change applies from the period it was made in onward, so older periods keep their old max #
    # The earliest setting also covers periods from before the budget was first set #
    if not weekly_max_history:
        return None
    applicable = [change for change in weekly_max_history if change["from"] <= start]
    return (applicable[-1] if applicable else weekly_max_history[0])["amount"]

def set_weekly_max(weekly_max_history, start, amount):
    if weekly_max_for(start, weekly_max_history) == amount:
        return weekly_max_history
    kept = [change for change in weekly_max_history if change["from"] < start]
    return kept + [{"from": start, "amount": amount}]

## SUMMARIES ##

def summarize_week(transactions, start, end, weekly_max, now):
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

    if now < start:
        status = "upcoming"
    elif now >= end:
        status = "past"
    else:
        status = "current"

    today = datetime(now.year, now.month, now.day)

    return {
        "start": start,
        "end": end,
        "status": status,
        "spent": spent,
        "count": len(entries),
        "weekly_max": weekly_max,
        "left": weekly_max - spent if weekly_max is not None else None,
        "days_left": (end - today).days if status == "current" else 0,
        "top_category": top,
        "top_share": min(top["amount"] / spent, 1) if top else 0,
    }

def history_periods(transactions, start_day, weekly_max_history, now):
    # Every period from the one holding the oldest transaction through the current one #
    oldest = min((entry["timestamp"] for entry in transactions), default=now)
    current = period_start(now, start_day)
    start = period_start(min(oldest, now), start_day)

    periods = []
    while start <= current:
        end = next_period_start(start, start_day)
        weekly_max = weekly_max_for(start, weekly_max_history)
        periods.append({
            "start": start,
            "end": end,
            "weekly_max": weekly_max,
            "weeks": [summarize_week(transactions, ws, we, weekly_max, now) for ws, we in period_weeks(start, end)],
        })
        start = end
    return periods

## FORMATTING ##

def format_range(start, end, with_year=False):
    # `end` is exclusive (midnight after the last day), so show the day before it #
    last = end - timedelta(days=1)
    first_text = f"{start:%b} {start.day}"

    if with_year and start.year != last.year:
        return f"{first_text}, {start.year} – {last:%b} {last.day}, {last.year}"

    last_text = str(last.day) if (start.year, start.month) == (last.year, last.month) else f"{last:%b} {last.day}"
    return f"{first_text} – {last_text}" + (f", {last.year}" if with_year else "")
