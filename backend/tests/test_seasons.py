from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.services.risk import calculate_care_metrics
from app.services.seasons import effective_frequency, get_season, season_context


def payload():
    return {
        "nickname": "Season test",
        "species": "Bird's Nest Fern",
        "room": "Office",
        "sunlight": "Indirect Light",
        "watering_frequency": 7,
        "last_watered": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        "notes": None,
    }


def test_factor_table_and_boundaries():
    assert [(month, get_season(month).name) for month in (2, 3, 6, 7, 9, 10, 11, 12)] == [
        (2, "Winter"),
        (3, "Summer"),
        (6, "Summer"),
        (7, "Monsoon"),
        (9, "Monsoon"),
        (10, "Post-monsoon"),
        (11, "Post-monsoon"),
        (12, "Winter"),
    ]
    assert get_season(4).factor == 0.75
    assert get_season(8).factor == 1.25
    assert get_season(10).factor == 1.0
    assert get_season(1).factor == 1.4


def test_frequency_minimum_and_risk_override():
    assert effective_frequency(1, 4) == 1
    now = datetime(2026, 12, 10, tzinfo=timezone.utc)
    watered = now - timedelta(days=5)
    summer = calculate_care_metrics(watered, 7, now=now, frequency_override=5)
    winter = calculate_care_metrics(watered, 7, now=now, frequency_override=10)
    assert summer.days_until_due == 0
    assert winter.days_until_due == 5


def test_response_fields_and_live_override(client: TestClient):
    plant_id = client.post("/api/plants?season=winter", json=payload()).json()["id"]
    winter = client.get(f"/api/plants/{plant_id}?season=winter").json()
    summer = client.get(f"/api/plants/{plant_id}?season=summer").json()
    assert winter["season"] == "Winter"
    assert winter["base_watering_frequency"] == 7
    assert winter["effective_watering_frequency"] == 10
    assert winter["season_factor"] == 1.4
    assert summer["effective_watering_frequency"] == 5
    assert winter["days_until_due"] > summer["days_until_due"]


def test_season_context_rejects_invalid_names():
    try:
        season_context(override="storm")
    except ValueError as error:
        assert str(error) == "invalid season"
    else:
        raise AssertionError("invalid season must fail")
