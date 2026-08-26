from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.plant import Plant, Watering
from app.services.streaks import build_history, compute_consistency, compute_streaks


TODAY = date(2026, 8, 27)


def payload(days_ago: int = 1):
    return {
        "nickname": "Streaky",
        "species": "Sweet Basil",
        "room": "Kitchen",
        "sunlight": "Direct Sun",
        "watering_frequency": 7,
        "last_watered": (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(),
        "notes": None,
    }


def test_streak_edge_cases_and_exact_grace():
    assert compute_streaks([], 7, TODAY).__dict__ == {"current": 0, "longest": 0}
    exact_grace = compute_streaks([TODAY - timedelta(days=8)], 7, TODAY)
    assert exact_grace.current == 1
    assert compute_streaks([TODAY - timedelta(days=9)], 7, TODAY).current == 0
    broken = compute_streaks(
        [TODAY - timedelta(days=30), TODAY - timedelta(days=22), TODAY - timedelta(days=10), TODAY - timedelta(days=2)],
        7,
        TODAY,
    )
    assert broken.current == 2
    assert broken.longest == 2


def test_consistency_is_bounded_and_history_marks_overdue_days():
    frequent = [TODAY - timedelta(days=value) for value in range(30)]
    assert compute_consistency(frequent, 7, TODAY) == 100
    assert compute_consistency([], 7, TODAY) == 0
    history = build_history([TODAY - timedelta(days=10)], 3, TODAY, days=4)
    assert [day.status for day in history] == ["overdue"] * 4


def test_xp_on_time_late_and_streak_bonus(client: TestClient, db_session: Session):
    on_time = client.post("/api/plants", json=payload(1)).json()
    watered = client.post(f"/api/plants/{on_time['id']}/water?season=post-monsoon").json()
    assert watered["xp"] == 10

    late = client.post("/api/plants", json=payload(20)).json()
    caught_up = client.post(f"/api/plants/{late['id']}/water?season=post-monsoon").json()
    assert caught_up["xp"] == 3

    bonus = client.post("/api/plants", json=payload(1)).json()
    plant = db_session.get(Plant, bonus["id"])
    assert plant is not None
    db_session.query(Watering).filter(Watering.plant_id == plant.id).delete()
    now = datetime.now(timezone.utc)
    for days in (22, 15, 8, 1):
        db_session.add(Watering(plant_id=plant.id, watered_at=now - timedelta(days=days)))
    plant.last_watered = now - timedelta(days=1)
    db_session.commit()
    streak_watered = client.post(f"/api/plants/{plant.id}/water?season=post-monsoon").json()
    assert streak_watered["xp"] == 15
    assert streak_watered["current_streak"] == 5


def test_milestone_crossing_and_cascade_delete(client: TestClient, db_session: Session):
    created = client.post("/api/plants", json=payload(1)).json()
    plant = db_session.get(Plant, created["id"])
    assert plant is not None
    db_session.query(Watering).filter(Watering.plant_id == plant.id).delete()
    now = datetime.now(timezone.utc)
    for days in (36, 29, 22, 15, 8, 1):
        db_session.add(Watering(plant_id=plant.id, watered_at=now - timedelta(days=days)))
    plant.last_watered = now - timedelta(days=1)
    db_session.commit()

    watered = client.post(f"/api/plants/{plant.id}/water?season=post-monsoon").json()
    assert watered["milestone"] == "7"
    assert watered["current_streak"] == 7
    assert client.delete(f"/api/plants/{plant.id}").status_code == 204
    assert db_session.scalar(select(func.count()).select_from(Watering).where(Watering.plant_id == plant.id)) == 0
