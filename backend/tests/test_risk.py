from datetime import datetime, timezone

import pytest

from app.services.risk import HIGH_RISK, HEALTHY, NEEDS_WATER_SOON, calculate_care_metrics


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("last_watered", "frequency", "risk", "status", "days_until_due"),
    [
        (datetime(2026, 8, 25, tzinfo=timezone.utc), 7, 0, HEALTHY, 7),
        (datetime(2026, 8, 23, tzinfo=timezone.utc), 7, 29, HEALTHY, 5),
        (datetime(2026, 8, 21, tzinfo=timezone.utc), 7, 57, NEEDS_WATER_SOON, 3),
        (datetime(2026, 8, 16, tzinfo=timezone.utc), 7, 100, HIGH_RISK, -2),
    ],
)
def test_calculate_care_metrics(last_watered, frequency, risk, status, days_until_due):
    metrics = calculate_care_metrics(last_watered, frequency, now=NOW)

    assert metrics.risk_score == risk
    assert metrics.status == status
    assert metrics.days_until_due == days_until_due


def test_invalid_frequency_is_rejected():
    with pytest.raises(ValueError):
        calculate_care_metrics(NOW, 0, now=NOW)

