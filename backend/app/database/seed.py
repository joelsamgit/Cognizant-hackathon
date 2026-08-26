import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.care_event import CareEvent
from app.models.plant import Plant, Watering
from app.models.user import User
from app.services.pet_safety import fields_for_species


CATALOG_PATH = Path(__file__).with_name("plant_catalog.json")
ROOMS = ("Living Room", "Kitchen", "Bedroom", "Office", "Balcony")
CATALOG_OWNER_EMAIL = "legacy-garden@plantguardian.local"
DEMO_PROFILES = {
    "tulsi_holy_basil": {
        "nickname": "Pesto",
        "species": "Sweet Basil",
        "frequency": 3,
        "last_watered_days": 1,
        "xp": 150,
        "gaps": [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
    },
    "money_plant_pothos": {
        "nickname": "Greeny",
        "species": "Golden Pothos",
        "frequency": 7,
        "last_watered_days": 2,
        "xp": 75,
        "gaps": [2, 12, 19, 26, 33],
    },
    "snake_plant_sansevieria": {
        "nickname": "Sage",
        "species": "Snake Plant",
        "frequency": 14,
        "last_watered_days": 5,
        "xp": 80,
        "gaps": [5, 19, 33],
    },
    "boston_fern": {
        "nickname": "Nori",
        "species": "Bird's Nest Fern",
        "frequency": 5,
        "last_watered_days": 8,
        "xp": 70,
        "gaps": [8, 13, 18, 23, 28, 33],
    },
    "calathea_rattlesnake": {
        "nickname": "Moss",
        "species": "Calathea Orbifolia",
        "frequency": 7,
        "last_watered_days": 2,
        "xp": 145,
        "gaps": [2, 9, 16, 23, 30],
    },
}


def _load_catalog() -> list[dict[str, object]]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        records = json.load(catalog_file)
    if not isinstance(records, list):
        raise ValueError("Plant catalog must contain a JSON list")
    return records


def _sunlight_value(guide_label: str) -> str:
    label = guide_label.casefold()
    if "low light" in label:
        return "Low Light"
    if "indirect" in label or "filtered" in label or "shade" in label:
        return "Indirect Light"
    if "direct" in label or "full sun" in label or "bright sun" in label:
        return "Direct Sun"
    return "Indirect Light"


def _details(record: dict[str, object]) -> dict[str, object]:
    front = record["front"]
    story = record["story"]
    assert isinstance(front, dict) and isinstance(story, dict)
    return {
        "indian_name": record["indian_name"],
        "common_name": record["common_name"],
        "scientific_name": record["scientific_name"],
        "difficulty": record["difficulty"],
        "category": record["category"],
        "tagline": front["tagline"],
        "image_url": front.get("image_url"),
        "vibe": front["vibe"],
        "ideal_spot": front["ideal_spot"],
        "name_origin": story["name_origin"],
        "cultural_context": story["cultural_context"],
        "fun_fact": story["fun_fact"],
        "symbolism": story["symbolism"],
    }


def _aliases(record: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for field in ("name", "common_name", "scientific_name", "indian_name"):
        value = record.get(field)
        if value:
            raw = str(value).strip().casefold()
            names.add(raw)
            for part in raw.split("/"):
                names.add(part.strip())
    return names


def lookup_catalog_by_species(
    species: str,
) -> tuple[str, dict[str, object], dict[str, object]] | None:
    """Match a species string against the catalog.

    Returns ``(catalog_key, details, care_guide)`` on match, or ``None``.
    """
    query = species.strip().casefold()
    if not query:
        return None
    catalog = _load_catalog()
    for record in catalog:
        if query in _aliases(record):
            catalog_key = str(record["id"])
            details = _details(record)
            guide = record["care_guide"]
            assert isinstance(guide, dict)
            return catalog_key, details, guide
    return None


def _days_since_watered(frequency: int, index: int) -> int:
    ratios = (0.25, 0.55, 0.85)
    return max(0, math.ceil(frequency * ratios[index % len(ratios)]))


def _seed_values(
    record: dict[str, object],
    guide: dict[str, object],
    index: int,
    now: datetime,
) -> tuple[str, str, int, datetime, int, list[datetime]]:
    profile = DEMO_PROFILES.get(str(record["id"]))
    if profile:
        gaps = [int(value) for value in profile["gaps"]]
        return (
            str(profile["nickname"]),
            str(profile["species"]),
            int(profile["frequency"]),
            now - timedelta(days=int(profile["last_watered_days"])),
            int(profile["xp"]),
            [now - timedelta(days=gap) for gap in gaps],
        )
    frequency = int(guide["watering_frequency_days"])
    last_watered = now - timedelta(days=_days_since_watered(frequency, index))
    stage_xp = (0, 25, 65, 125, 205)[index % 5]
    dates = [
        last_watered - timedelta(days=frequency * offset)
        for offset in range(6)
    ]
    return (
        str(record["name"]),
        str(record["common_name"]),
        frequency,
        last_watered,
        stage_xp,
        dates,
    )


def _add_watering_history(db, plant: Plant, dates: list[datetime]) -> None:
    db.add_all(
        [Watering(plant_id=plant.id, watered_at=watered_at) for watered_at in dates]
    )


def seed_database() -> None:
    catalog = _load_catalog()
    with SessionLocal() as db:
        catalog_owner = _ensure_catalog_owner(db)
        existing_plants = list(
            db.scalars(select(Plant).where(Plant.user_id == catalog_owner.id)).all()
        )
        by_catalog_key = {
            plant.catalog_key: plant for plant in existing_plants if plant.catalog_key
        }
        unmatched_existing = {plant.id: plant for plant in existing_plants if not plant.catalog_key}
        now = datetime.now(timezone.utc)
        created_count = 0
        enriched_count = 0

        for index, record in enumerate(catalog):
            catalog_key = str(record["id"])
            details = _details(record)
            guide = record["care_guide"]
            assert isinstance(guide, dict)
            plant = by_catalog_key.get(catalog_key)

            if plant is None:
                aliases = _aliases(record)
                plant = next(
                    (
                        candidate
                        for candidate in unmatched_existing.values()
                        if candidate.nickname.strip().casefold() in aliases
                        or candidate.species.strip().casefold() in aliases
                    ),
                    None,
                )

            if plant is not None:
                plant.catalog_key = catalog_key
                plant.details = details
                plant.care_guide = guide
                unmatched_existing.pop(plant.id, None)
                enriched_count += 1
                continue

            nickname, species, frequency, last_watered, xp, watering_dates = _seed_values(
                record,
                guide,
                index,
                now,
            )
            sunlight = _sunlight_value(str(guide["sunlight"]))
            plant = Plant(
                user_id=catalog_owner.id,
                nickname=nickname,
                species=species,
                room=ROOMS[index % len(ROOMS)],
                sunlight=sunlight,
                watering_frequency=frequency,
                last_watered=last_watered,
                xp=xp,
                notes=str(details["tagline"]),
                catalog_key=catalog_key,
                details=details,
                care_guide=guide,
                **fields_for_species(species, sunlight),
            )
            db.add(plant)
            db.flush()
            _add_watering_history(db, plant, watering_dates)
            db.add(
                CareEvent(
                    plant_id=plant.id,
                    action="water",
                    occurred_at=plant.last_watered,
                    result="watered",
                    notes="Initial seeded watering record",
                )
            )
            created_count += 1

        db.commit()
        print(
            f"Plant catalog synchronized: {created_count} created, "
            f"{enriched_count} refreshed."
        )


def seed_starter_garden(db, user_id: int) -> int:
    catalog = _load_catalog()
    existing_keys = set(
        db.scalars(
            select(Plant.catalog_key).where(
                Plant.user_id == user_id,
                Plant.catalog_key.is_not(None),
            )
        ).all()
    )
    now = datetime.now(timezone.utc)
    created_count = 0

    for index, record in enumerate(catalog):
        catalog_key = str(record["id"])
        if catalog_key in existing_keys:
            continue
        guide = record["care_guide"]
        assert isinstance(guide, dict)
        details = _details(record)
        nickname, species, frequency, last_watered, xp, watering_dates = _seed_values(
            record,
            guide,
            index,
            now,
        )
        sunlight = _sunlight_value(str(guide["sunlight"]))
        plant = Plant(
            user_id=user_id,
            nickname=nickname,
            species=species,
            room=ROOMS[index % len(ROOMS)],
            sunlight=sunlight,
            watering_frequency=frequency,
            last_watered=last_watered,
            xp=xp,
            notes=str(details["tagline"]),
            catalog_key=catalog_key,
            details=details,
            care_guide=guide,
            **fields_for_species(species, sunlight),
        )
        db.add(plant)
        db.flush()
        _add_watering_history(db, plant, watering_dates)
        db.add(
            CareEvent(
                plant_id=plant.id,
                action="water",
                occurred_at=plant.last_watered,
                result="watered",
                notes="Starter garden watering record",
            )
        )
        created_count += 1

    return created_count


def _ensure_catalog_owner(db) -> User:
    owner = db.scalar(select(User).where(User.email == CATALOG_OWNER_EMAIL))
    if owner is not None:
        return owner
    owner = User(
        email=CATALOG_OWNER_EMAIL,
        password_hash="!disabled",
        full_name="Legacy Garden",
        place="Local installation",
        pets=["No pets"],
        timezone="UTC",
        is_active=False,
    )
    db.add(owner)
    db.flush()
    return owner


if __name__ == "__main__":
    seed_database()
