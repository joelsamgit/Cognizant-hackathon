from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.services.pet_safety import load_pet_safety_data, resolve_species


def payload(species: str):
    return {
        "nickname": "Pet test",
        "species": species,
        "room": "Office",
        "sunlight": "Indirect Light",
        "watering_frequency": 7,
        "last_watered": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "notes": None,
    }


def test_resolution_exact_normalized_substring_and_unknown():
    assert len(load_pet_safety_data()) >= 60
    assert resolve_species("Golden Pothos").severity == "toxic"
    assert resolve_species("golden-pothos!!!").severity == "toxic"
    assert resolve_species("Calathea Orbifolia plant").severity == "safe"
    assert resolve_species("Uncatalogued Moon Plant") is None


def test_pet_safety_persists_and_re_resolves(client: TestClient):
    created = client.post("/api/plants", json=payload("Golden Pothos"))
    assert created.status_code == 201
    body = created.json()
    assert body["pet_safety"] == "toxic"
    assert body["toxic_cats"] is True
    assert "above" in body["placement_tip"].lower()

    updated = client.patch(f"/api/plants/{body['id']}", json={"species": "Sweet Basil"})
    assert updated.json()["pet_safety"] == "safe"
    assert updated.json()["toxic_cats"] is False

    unknown = client.patch(f"/api/plants/{body['id']}", json={"species": "Moon Plant"})
    assert unknown.json()["pet_safety"] is None
    assert unknown.json()["placement_tip"] is None
