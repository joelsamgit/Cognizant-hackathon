from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.plant import Plant


def seed_database() -> None:
    with SessionLocal() as db:
        existing_count = db.scalar(select(func.count()).select_from(Plant)) or 0
        if existing_count:
            print(f"Seed skipped: {existing_count} plant records already exist.")
            return

        now = datetime.now(timezone.utc)
        plants = [
            Plant(
                nickname="Moss",
                species="Bird's Nest Fern",
                room="Living Room",
                sunlight="Indirect Light",
                watering_frequency=7,
                last_watered=now - timedelta(days=1),
                notes="Turn the pot a quarter turn after watering.",
            ),
            Plant(
                nickname="Greeny",
                species="Golden Pothos",
                room="Kitchen",
                sunlight="Indirect Light",
                watering_frequency=7,
                last_watered=now - timedelta(days=4),
                notes="A new vine is reaching toward the east window.",
            ),
            Plant(
                nickname="Sage",
                species="Snake Plant",
                room="Bedroom",
                sunlight="Low Light",
                watering_frequency=14,
                last_watered=now - timedelta(days=12),
                notes="Let the soil dry fully between waterings.",
            ),
            Plant(
                nickname="Pesto",
                species="Sweet Basil",
                room="Kitchen",
                sunlight="Direct Sun",
                watering_frequency=3,
                last_watered=now - timedelta(days=2),
                notes="Pinch flower buds to encourage leaf growth.",
            ),
            Plant(
                nickname="Nori",
                species="Calathea Orbifolia",
                room="Office",
                sunlight="Indirect Light",
                watering_frequency=5,
                last_watered=now - timedelta(days=8),
                notes="Prefers filtered water and steady humidity.",
            ),
        ]
        db.add_all(plants)
        db.commit()
        print(f"Seeded {len(plants)} demo plants.")


if __name__ == "__main__":
    seed_database()

