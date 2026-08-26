from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class StreakStats:
    current: int
    longest: int


@dataclass(frozen=True)
class HistoryDay:
    date: date
    status: str


def _date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def _dates(values: list[date | datetime]) -> list[date]:
    return sorted({_date(value) for value in values})


def compute_streaks(
    dates: list[date | datetime],
    frequency: int,
    today: date | datetime,
) -> StreakStats:
    if frequency <= 0:
        raise ValueError("watering frequency must be greater than zero")
    watered = _dates(dates)
    if not watered:
        return StreakStats(current=0, longest=0)

    grace_window = frequency + 1
    run = 1
    longest = 1
    for previous, current in zip(watered, watered[1:], strict=False):
        run = run + 1 if (current - previous).days <= grace_window else 1
        longest = max(longest, run)

    current = run
    if (_date(today) - watered[-1]).days > grace_window:
        current = 0
    return StreakStats(current=current, longest=longest)


def compute_consistency(
    dates: list[date | datetime],
    frequency: int,
    today: date | datetime,
) -> int:
    if frequency <= 0:
        raise ValueError("watering frequency must be greater than zero")
    current = _date(today)
    window_start = current - timedelta(days=29)
    actual = sum(window_start <= watered <= current for watered in _dates(dates))
    expected = max(1, 30 // frequency)
    return min(100, round((actual / expected) * 100))


def build_history(
    dates: list[date | datetime],
    frequency: int,
    today: date | datetime,
    *,
    days: int = 28,
) -> list[HistoryDay]:
    if frequency <= 0:
        raise ValueError("watering frequency must be greater than zero")
    if days <= 0:
        return []
    current = _date(today)
    watered = _dates(dates)
    watered_set = set(watered)
    result: list[HistoryDay] = []
    grace_window = frequency + 1

    for offset in range(days - 1, -1, -1):
        day = current - timedelta(days=offset)
        if day in watered_set:
            status = "watered"
        else:
            prior = [value for value in watered if value < day]
            status = (
                "overdue"
                if prior and (day - prior[-1]).days > grace_window
                else "ontrack"
            )
        result.append(HistoryDay(date=day, status=status))
    return result


def growth_stage(xp: int) -> int:
    if xp >= 200:
        return 5
    if xp >= 120:
        return 4
    if xp >= 60:
        return 3
    if xp >= 20:
        return 2
    return 1
