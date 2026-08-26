from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plant import Plant, Watering
from app.services.seasons import season_context


@dataclass(frozen=True)
class AccountCareStats:
    current_streak: int
    longest_streak: int
    xp: int
    growth_stage: int
    mood: str
    total_waterings: int


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _stage(xp: int) -> int:
    if xp >= 200:
        return 5
    if xp >= 120:
        return 4
    if xp >= 60:
        return 3
    if xp >= 20:
        return 2
    return 1


def calculate_account_stats(
    db: Session,
    user_id: int,
    plants: list[Plant] | None = None,
    now: datetime | None = None,
) -> AccountCareStats:
    current = _utc(now or datetime.now(timezone.utc))
    season = season_context(current)
    records = list(
        db.scalars(
            select(Watering)
            .join(Plant, Plant.id == Watering.plant_id)
            .where(Plant.user_id == user_id)
            .order_by(Watering.watered_at.asc())
        ).all()
    )
    garden = plants if plants is not None else list(db.scalars(select(Plant).where(Plant.user_id == user_id)).all())
    if not garden:
        return AccountCareStats(0, 0, 0, 1, "happy", 0)

    by_plant: dict[int, list[date]] = defaultdict(list)
    for record in records:
        by_plant[record.plant_id].append(_utc(record.watered_at).date())

    def qualifies(week: date) -> bool:
        end = min(week + timedelta(days=6), current.date())
        threshold = ceil(len(garden) * 0.7)
        touched = 0
        for plant in garden:
            dates = by_plant.get(plant.id, [])
            if any(week <= watered <= end for watered in dates):
                touched += 1
            before = [watered for watered in dates if watered <= end]
            frequency = season.frequency(plant.watering_frequency)
            if not before or (end - max(before)).days > frequency + 1:
                return False
        return touched >= threshold

    first = min((day for days in by_plant.values() for day in days), default=current.date())
    first_week = _week_start(first)
    last_week = _week_start(current.date())
    weeks: list[bool] = []
    cursor = first_week
    while cursor <= last_week:
        weeks.append(qualifies(cursor))
        cursor += timedelta(days=7)

    current_streak = 0
    for valid in reversed(weeks):
        if not valid:
            break
        current_streak += 1
    longest = run = 0
    for valid in weeks:
        run = run + 1 if valid else 0
        longest = max(longest, run)

    overdue_count = sum(
        (current.date() - _utc(plant.last_watered).date()).days > season.frequency(plant.watering_frequency) + 1
        for plant in garden
    )
    overdue = overdue_count > 0
    soon = any(
        (current.date() - _utc(plant.last_watered).date()).days > season.frequency(plant.watering_frequency) * 0.4
        for plant in garden
    )
    mood = "sad" if overdue_count >= ceil(len(garden) * 0.5) else "doubtful" if overdue or soon else "happy"
    xp = sum(plant.xp for plant in garden)
    return AccountCareStats(current_streak, longest, xp, _stage(xp), mood, len(records))
