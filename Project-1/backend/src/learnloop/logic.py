"""Pure date / progress maths for the dashboard (no DB, easy to unit test)."""

import datetime as dt
from collections.abc import Iterable, Mapping
from zoneinfo import ZoneInfo

ONE_DAY = dt.timedelta(days=1)


def today_in(tz_name: str, now: dt.datetime | None = None) -> dt.date:
    """Today's calendar date in the given IANA timezone."""
    now = now or dt.datetime.now(dt.UTC)
    return now.astimezone(ZoneInfo(tz_name)).date()


def week_start_of(day: dt.date, week_start: str = "monday") -> dt.date:
    """First day of the week containing `day` (Monday- or Sunday-based)."""
    if week_start == "sunday":
        offset = (day.weekday() + 1) % 7  # Sunday -> 0
    else:
        offset = day.weekday()  # Monday -> 0
    return day - dt.timedelta(days=offset)


def percent(value: float, whole: float) -> int:
    """Whole-number percentage, half rounded up. 0 when `whole` is 0."""
    if whole <= 0:
        return 0
    return int(value * 100 / whole + 0.5)


def completion_percent(done: int, total: int) -> int:
    """Module completion % (AC2.2): 0 when the track has no modules."""
    return percent(done, total)


def hours(minutes: float) -> float:
    return round(minutes / 60, 2)


def streaks(study_days: Iterable[dt.date], today: dt.date) -> tuple[int, int]:
    """(current, longest) runs of consecutive calendar days with a session (AC4.2).

    The current streak may end today or yesterday (today isn't over yet).
    Uses real date arithmetic, so month/year boundaries just work.
    """
    days = sorted(set(study_days))
    if not days:
        return 0, 0

    longest = run = 1
    for prev, cur in zip(days, days[1:], strict=False):
        run = run + 1 if cur - prev == ONE_DAY else 1
        longest = max(longest, run)

    day_set = set(days)
    anchor = today if today in day_set else today - ONE_DAY
    current = 0
    while anchor in day_set:
        current += 1
        anchor -= ONE_DAY
    return current, longest


def weekly_trend(
    minutes_by_day: Mapping[dt.date, int], current_week_start: dt.date, weeks: int = 8
) -> list[tuple[dt.date, float]]:
    """Hours per week for the last `weeks` weeks, oldest first, zero weeks included (AC4.4)."""
    starts = [current_week_start - dt.timedelta(weeks=i) for i in range(weeks - 1, -1, -1)]
    totals = dict.fromkeys(starts, 0)
    first = starts[0]
    for day, mins in minutes_by_day.items():
        if day < first:
            continue
        idx = (day - first).days // 7
        if 0 <= idx < weeks:
            totals[starts[idx]] += mins
    return [(s, hours(totals[s])) for s in starts]
