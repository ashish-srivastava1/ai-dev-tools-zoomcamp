import datetime as dt

import pytest

from learnloop import logic

D = dt.date


@pytest.mark.parametrize(
    "day,week_start,expected",
    [
        (D(2026, 10, 21), "monday", D(2026, 10, 19)),  # Wed -> Mon
        (D(2026, 10, 19), "monday", D(2026, 10, 19)),  # Mon itself
        (D(2026, 10, 25), "monday", D(2026, 10, 19)),  # Sun belongs to previous Mon
        (D(2026, 10, 25), "sunday", D(2026, 10, 25)),  # Sun itself
        (D(2026, 10, 21), "sunday", D(2026, 10, 18)),
        (D(2027, 1, 1), "monday", D(2026, 12, 28)),  # across a year boundary
    ],
)
def test_week_start_of(day, week_start, expected):
    assert logic.week_start_of(day, week_start) == expected


def test_today_in_uses_timezone():
    # 20:00 UTC on 31 Dec is already 1 Jan in India.
    now = dt.datetime(2026, 12, 31, 20, 0, tzinfo=dt.UTC)
    assert logic.today_in("Asia/Kolkata", now) == D(2027, 1, 1)
    assert logic.today_in("America/New_York", now) == D(2026, 12, 31)


@pytest.mark.parametrize(
    "value,whole,expected",
    [(0, 10, 0), (5, 10, 50), (1, 3, 33), (2, 3, 67), (1, 8, 13), (15, 10, 150), (3, 0, 0)],
)
def test_percent(value, whole, expected):
    assert logic.percent(value, whole) == expected


def test_completion_percent_zero_modules_is_zero():
    assert logic.completion_percent(0, 0) == 0
    assert logic.completion_percent(1, 3) == 33


def test_completion_percent_never_divides_by_zero():
    # Regression: a track without modules made GET /api/dashboard return 500 (ZeroDivisionError).
    assert logic.completion_percent(0, 0) == 0
    assert logic.completion_percent(2, 0) == 0


def test_streaks_empty():
    assert logic.streaks([], D(2026, 10, 21)) == (0, 0)


def test_streak_ending_today():
    days = [D(2026, 10, 19), D(2026, 10, 20), D(2026, 10, 21)]
    assert logic.streaks(days, D(2026, 10, 21)) == (3, 3)


def test_streak_ending_yesterday_still_counts():
    days = [D(2026, 10, 19), D(2026, 10, 20)]
    assert logic.streaks(days, D(2026, 10, 21)) == (2, 2)


def test_streak_broken_two_days_ago():
    days = [D(2026, 10, 18), D(2026, 10, 19)]
    assert logic.streaks(days, D(2026, 10, 21)) == (0, 2)


def test_longest_streak_in_the_past():
    days = [D(2026, 9, d) for d in range(1, 6)] + [D(2026, 10, 21)]
    assert logic.streaks(days, D(2026, 10, 21)) == (1, 5)


def test_streak_across_month_and_year_boundaries():
    days = [D(2026, 12, 30), D(2026, 12, 31), D(2027, 1, 1), D(2027, 1, 2)]
    assert logic.streaks(days, D(2027, 1, 2)) == (4, 4)
    month = [D(2026, 10, 30), D(2026, 10, 31), D(2026, 11, 1)]
    assert logic.streaks(month, D(2026, 11, 1)) == (3, 3)


def test_streak_across_leap_day():
    days = [D(2028, 2, 28), D(2028, 2, 29), D(2028, 3, 1)]
    assert logic.streaks(days, D(2028, 3, 1)) == (3, 3)


def test_duplicate_days_count_once():
    days = [D(2026, 10, 21), D(2026, 10, 21)]
    assert logic.streaks(days, D(2026, 10, 21)) == (1, 1)


def test_weekly_trend_has_8_weeks_with_zeros():
    current = D(2026, 10, 19)
    trend = logic.weekly_trend({D(2026, 10, 20): 90, D(2026, 9, 1): 60}, current)
    assert len(trend) == 8
    assert trend[0][0] == D(2026, 8, 31)
    assert trend[-1] == (D(2026, 10, 19), 1.5)
    assert trend[0] == (D(2026, 8, 31), 1.0)
    assert sum(h for _, h in trend) == 2.5


def test_weekly_trend_ignores_older_data():
    trend = logic.weekly_trend({D(2020, 1, 1): 600}, D(2026, 10, 19))
    assert all(h == 0 for _, h in trend)
