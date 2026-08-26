from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SeasonInfo:
    name: str
    factor: float


SEASONS = {
    "summer": SeasonInfo(name="Summer", factor=0.75),
    "monsoon": SeasonInfo(name="Monsoon", factor=1.25),
    "post-monsoon": SeasonInfo(name="Post-monsoon", factor=1.0),
    "winter": SeasonInfo(name="Winter", factor=1.4),
}


@dataclass(frozen=True)
class SeasonContext:
    season: str
    factor: float

    def frequency(self, base: int) -> int:
        if base <= 0:
            raise ValueError("watering frequency must be greater than zero")
        return max(1, round(base * self.factor))


def get_season(month: int) -> SeasonInfo:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    if 3 <= month <= 6:
        return SEASONS["summer"]
    if 7 <= month <= 9:
        return SEASONS["monsoon"]
    if 10 <= month <= 11:
        return SEASONS["post-monsoon"]
    return SEASONS["winter"]


def get_season_by_name(name: str) -> SeasonInfo:
    try:
        return SEASONS[name.strip().casefold()]
    except KeyError as error:
        raise ValueError("invalid season") from error


def effective_frequency(base: int, month: int) -> int:
    season = get_season(month)
    return SeasonContext(season.name, season.factor).frequency(base)


def season_context(
    now: datetime | None = None,
    *,
    override: str | None = None,
) -> SeasonContext:
    current = now or datetime.now(timezone.utc)
    season = get_season_by_name(override) if override else get_season(current.month)
    return SeasonContext(season=season.name, factor=season.factor)
