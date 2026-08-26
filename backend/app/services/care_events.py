from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.care_event import CareEvent
from app.models.plant import Plant
from app.schemas.care_event import CareAction, CareEventCreate, CareResult


def list_care_events(db: Session, plant_id: int) -> list[CareEvent]:
    statement = (
        select(CareEvent)
        .where(CareEvent.plant_id == plant_id)
        .order_by(CareEvent.occurred_at.desc(), CareEvent.id.desc())
    )
    return list(db.scalars(statement).all())


def create_care_event(db: Session, plant: Plant, payload: CareEventCreate) -> CareEvent:
    result = payload.result
    if result is None:
        result = CareResult.watered if payload.action == CareAction.water else CareResult.completed

    event = CareEvent(
        plant_id=plant.id,
        action=payload.action.value,
        occurred_at=payload.occurred_at,
        amount_ml=payload.amount_ml,
        result=result.value,
        notes=payload.notes,
    )
    db.add(event)

    if (
        payload.action == CareAction.water
        and result == CareResult.watered
        and payload.occurred_at >= _as_utc(plant.last_watered)
    ):
        plant.last_watered = payload.occurred_at

    db.commit()
    db.refresh(event)
    return event


def record_watering_now(db: Session, plant: Plant) -> CareEvent:
    return create_care_event(
        db,
        plant,
        CareEventCreate(
            action=CareAction.water,
            occurred_at=datetime.now(timezone.utc),
            result=CareResult.watered,
        ),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
