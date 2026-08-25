from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.plant import Plant
from app.schemas.plant import PlantCreate, PlantPatch, PlantPut, PlantResponse
from app.services.risk import calculate_care_metrics


def to_response(plant: Plant, *, now: datetime | None = None) -> PlantResponse:
    metrics = calculate_care_metrics(
        plant.last_watered,
        plant.watering_frequency,
        now=now,
    )
    return PlantResponse.model_validate(
        {
            "id": plant.id,
            "nickname": plant.nickname,
            "species": plant.species,
            "room": plant.room,
            "sunlight": plant.sunlight,
            "watering_frequency": plant.watering_frequency,
            "last_watered": plant.last_watered,
            "notes": plant.notes,
            "created_at": plant.created_at,
            "updated_at": plant.updated_at,
            **metrics.__dict__,
        }
    )


def list_plants(db: Session, *, room: str | None = None) -> list[PlantResponse]:
    statement = select(Plant)
    if room:
        statement = statement.where(func.lower(Plant.room) == room.strip().lower())

    plants = list(db.scalars(statement).all())
    current = datetime.now(timezone.utc)
    responses = [to_response(plant, now=current) for plant in plants]
    return sorted(responses, key=lambda plant: (-plant.risk_score, plant.nickname.lower()))


def get_plant(db: Session, plant_id: int) -> Plant | None:
    return db.get(Plant, plant_id)


def create_plant(db: Session, payload: PlantCreate) -> Plant:
    plant = Plant(**payload.model_dump(mode="python"))
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


def replace_plant(db: Session, plant: Plant, payload: PlantPut) -> Plant:
    for field, value in payload.model_dump(mode="python").items():
        setattr(plant, field, value)
    db.commit()
    db.refresh(plant)
    return plant


def update_plant(db: Session, plant: Plant, payload: PlantPatch) -> Plant:
    for field, value in payload.model_dump(exclude_unset=True, mode="python").items():
        setattr(plant, field, value)
    db.commit()
    db.refresh(plant)
    return plant


def delete_plant(db: Session, plant: Plant) -> None:
    db.delete(plant)
    db.commit()


def water_plant(db: Session, plant: Plant) -> Plant:
    plant.last_watered = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plant)
    return plant

