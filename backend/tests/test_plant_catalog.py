from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import seed
from app.database.base import Base
from app.models.plant import Plant
from app.schemas.plant import PlantCareGuide, PlantDetails
from app.services.plants import to_response


def test_catalog_seeds_complete_plants_without_duplicates(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SeedSession = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(seed, "SessionLocal", SeedSession)

    catalog = seed._load_catalog()
    assert len(catalog) >= 20
    for record in catalog:
        PlantDetails.model_validate(seed._details(record))
        PlantCareGuide.model_validate(record["care_guide"])

    seed.seed_database()
    seed.seed_database()

    with SeedSession() as db:
        plants = list(db.scalars(select(Plant)).all())
        assert db.scalar(select(func.count()).select_from(Plant)) == len(catalog)
        assert all(plant.catalog_key for plant in plants)
        assert all(plant.details and plant.details["fun_fact"] for plant in plants)
        assert all(plant.care_guide and plant.care_guide["pro_tip"] for plant in plants)
        assert {to_response(plant).status for plant in plants} == {
            "Healthy",
            "Needs Water Soon",
            "Overdue / High Risk",
        }
