from dataclasses import dataclass
from datetime import datetime, timezone


HEALTHY = "Healthy"
NEEDS_WATER_SOON = "Needs Water Soon"
HIGH_RISK = "Overdue / High Risk"


@dataclass(frozen=True)
class CareMetrics:
    days_since_watered: int
    days_until_due: int
    risk_score: int
    status: str


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def calculate_care_metrics(
    last_watered: datetime,
    watering_frequency: int,
    *,
    now: datetime | None = None,
) -> CareMetrics:
    if watering_frequency <= 0:
        raise ValueError("watering frequency must be greater than zero")

    current = _as_utc(now or datetime.now(timezone.utc))
    watered = _as_utc(last_watered)
    days_since = max(0, (current.date() - watered.date()).days)
    days_until_due = watering_frequency - days_since
    risk_score = min(100, round((days_since / watering_frequency) * 100))

    if risk_score < 40:
        status = HEALTHY
    elif risk_score < 70:
        status = NEEDS_WATER_SOON
    else:
        status = HIGH_RISK

    return CareMetrics(
        days_since_watered=days_since,
        days_until_due=days_until_due,
        risk_score=risk_score,
        status=status,
    )

