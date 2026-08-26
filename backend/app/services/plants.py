from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.care_event import CareEvent
from app.models.plant import Plant, Watering
from app.schemas.plant import PlantCreate, PlantPatch, PlantPut, PlantResponse
from app.services.pet_safety import fields_for_species
from app.services.risk import HIGH_RISK, HEALTHY, calculate_care_metrics
from app.services.seasons import SeasonContext, season_context
from app.services.streaks import (
    build_history,
    compute_consistency,
    compute_streaks,
    growth_stage,
)


MILESTONES = (7, 14, 30, 50, 100)


@dataclass(frozen=True)
class GamificationStats:
    current_streak: int
    longest_streak: int
    consistency_pct: int
    total_waterings: int
    history: list[dict[str, object]]


@dataclass(frozen=True)
class WaterPlantResult:
    plant: Plant
    waterings: list[Watering]
    milestone: str | None


class WateringLockedError(RuntimeError):
    pass


def load_waterings(db: Session, plant_ids: list[int]) -> dict[int, list[Watering]]:
    grouped: dict[int, list[Watering]] = defaultdict(list)
    if not plant_ids:
        return grouped
    statement = (
        select(Watering)
        .where(Watering.plant_id.in_(plant_ids))
        .order_by(Watering.plant_id, Watering.watered_at.desc())
    )
    for watering in db.scalars(statement).all():
        grouped[watering.plant_id].append(watering)
    return grouped


def gamification_stats(
    waterings: list[Watering],
    frequency: int,
    now: datetime,
) -> GamificationStats:
    dates = [watering.watered_at for watering in waterings]
    streaks = compute_streaks(dates, frequency, now)
    return GamificationStats(
        current_streak=streaks.current,
        longest_streak=streaks.longest,
        consistency_pct=compute_consistency(dates, frequency, now),
        total_waterings=len(waterings),
        history=[day.__dict__ for day in build_history(dates, frequency, now)],
    )


def to_response(
    plant: Plant,
    *,
    now: datetime | None = None,
    waterings: list[Watering] | None = None,
    season: SeasonContext | None = None,
    season_override: str | None = None,
    milestone: str | None = None,
) -> PlantResponse:
    current = now or datetime.now(timezone.utc)
    context = season or season_context(current, override=season_override)
    effective = context.frequency(plant.watering_frequency)
    metrics = calculate_care_metrics(
        plant.last_watered,
        plant.watering_frequency,
        now=current,
        frequency_override=effective,
    )
    watering_locked = metrics.days_since_watered < effective
    records = waterings if waterings is not None else list(plant.waterings)
    stats = gamification_stats(records, effective, current)
    mood = (
        "happy"
        if metrics.status == HEALTHY
        else "sad"
        if metrics.status == HIGH_RISK
        else "doubtful"
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
            "catalog_key": plant.catalog_key,
            "details": plant.details,
            "care_guide": plant.care_guide,
            "created_at": plant.created_at,
            "updated_at": plant.updated_at,
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "consistency_pct": stats.consistency_pct,
            "total_waterings": stats.total_waterings,
            "xp": plant.xp,
            "growth_stage": growth_stage(plant.xp),
            "mood": mood,
            "history": stats.history,
            "milestone": milestone,
            "pet_safety": plant.pet_safety,
            "pet_severity": plant.pet_severity,
            "toxic_cats": plant.toxic_cats,
            "toxic_dogs": plant.toxic_dogs,
            "placement_tip": plant.placement_tip,
            "season": context.season,
            "base_watering_frequency": plant.watering_frequency,
            "effective_watering_frequency": effective,
            "season_factor": context.factor,
            "watering_locked": watering_locked,
            "next_watering_in_days": max(0, effective - metrics.days_since_watered),
            **metrics.__dict__,
        }
    )


def list_plants(
    db: Session,
    user_id: int,
    *,
    room: str | None = None,
    season_override: str | None = None,
) -> list[PlantResponse]:
    statement = select(Plant).where(Plant.user_id == user_id)
    if room:
        statement = statement.where(func.lower(Plant.room) == room.strip().lower())

    plants = list(db.scalars(statement).all())
    current = datetime.now(timezone.utc)
    context = season_context(current, override=season_override)
    by_plant = load_waterings(db, [plant.id for plant in plants])
    responses = [
        to_response(
            plant,
            now=current,
            waterings=by_plant[plant.id],
            season=context,
        )
        for plant in plants
    ]
    return sorted(responses, key=lambda plant: (-plant.risk_score, plant.nickname.lower()))


def get_plant(db: Session, plant_id: int, user_id: int) -> Plant | None:
    return db.scalar(
        select(Plant).where(Plant.id == plant_id, Plant.user_id == user_id)
    )


def response_for_plant(
    db: Session,
    plant: Plant,
    *,
    season_override: str | None = None,
    milestone: str | None = None,
) -> PlantResponse:
    records = load_waterings(db, [plant.id])[plant.id]
    return to_response(
        plant,
        waterings=records,
        season_override=season_override,
        milestone=milestone,
    )


def _apply_pet_safety(data: dict[str, object], plant: Plant | None = None) -> None:
    species = str(data.get("species", plant.species if plant else ""))
    sunlight_value = data.get("sunlight", plant.sunlight if plant else "")
    sunlight = getattr(sunlight_value, "value", sunlight_value)
    data.update(fields_for_species(species, str(sunlight)))


def create_plant(db: Session, payload: PlantCreate, user_id: int) -> Plant:
    data = payload.model_dump(mode="python")
    if data.get("details") is None:
        from app.database.seed import lookup_catalog_by_species

        match = lookup_catalog_by_species(data["species"])
        if match is not None:
            catalog_key, details, care_guide = match
            data["catalog_key"] = catalog_key
            data["details"] = details
            data["care_guide"] = care_guide
            if data.get("watering_frequency") is None:
                data["watering_frequency"] = int(care_guide["watering_frequency_days"])
    if data.get("watering_frequency") is None:
        data["watering_frequency"] = 7
    _apply_pet_safety(data)

    plant = Plant(user_id=user_id, **data)
    db.add(plant)
    db.flush()
    db.add_all(
        [
            Watering(plant_id=plant.id, watered_at=plant.last_watered),
            CareEvent(
                plant_id=plant.id,
                action="water",
                occurred_at=plant.last_watered,
                result="watered",
                notes="Initial watering record",
            ),
        ]
    )
    db.commit()
    db.refresh(plant)
    return plant


def replace_plant(db: Session, plant: Plant, payload: PlantPut) -> Plant:
    data = payload.model_dump(mode="python")
    _apply_pet_safety(data, plant)
    for field, value in data.items():
        setattr(plant, field, value)
    db.commit()
    db.refresh(plant)
    return plant


def update_plant(db: Session, plant: Plant, payload: PlantPatch) -> Plant:
    data = payload.model_dump(exclude_unset=True, mode="python")
    if "species" in data or "sunlight" in data:
        _apply_pet_safety(data, plant)
    for field, value in data.items():
        setattr(plant, field, value)
    db.commit()
    db.refresh(plant)
    return plant


def delete_plant(db: Session, plant: Plant) -> None:
    db.delete(plant)
    db.commit()


def water_plant(
    db: Session,
    plant: Plant,
    *,
    season_override: str | None = None,
) -> WaterPlantResult:
    now = datetime.now(timezone.utc)
    context = season_context(now, override=season_override)
    effective = context.frequency(plant.watering_frequency)
    records = load_waterings(db, [plant.id])[plant.id]
    before = gamification_stats(records, effective, now).current_streak
    gap_days = max(0, (now.date() - plant.last_watered.date()).days)
    award = 15 if gap_days <= effective + 1 and before >= 3 else 10
    if gap_days > effective + 1:
        award = 3

    watering = Watering(plant_id=plant.id, watered_at=now)
    plant.xp += award
    plant.last_watered = now
    db.add_all(
        [
            watering,
            CareEvent(
                plant_id=plant.id,
                action="water",
                occurred_at=now,
                result="watered",
            ),
        ]
    )
    db.commit()
    db.refresh(plant)
    db.refresh(watering)

    updated_records = [watering, *records]
    after = gamification_stats(updated_records, effective, now).current_streak
    crossed = [value for value in MILESTONES if before < value <= after]
    milestone = str(crossed[-1]) if crossed else None
    return WaterPlantResult(plant=plant, waterings=updated_records, milestone=milestone)
