from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def plant_payload(**overrides):
    payload = {
        "nickname": "Greeny",
        "species": "Golden Pothos",
        "room": "Living Room",
        "sunlight": "Indirect Light",
        "watering_frequency": 7,
        "last_watered": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
        "notes": "New leaf growing",
    }
    payload.update(overrides)
    return payload


def test_full_crud_and_watering_flow(client: TestClient):
    created = client.post("/api/plants", json=plant_payload())
    assert created.status_code == 201
    plant = created.json()
    assert plant["risk_score"] == 57
    assert plant["status"] == "Needs Water Soon"

    plant_id = plant["id"]
    fetched = client.get(f"/api/plants/{plant_id}")
    assert fetched.status_code == 200
    assert fetched.json()["nickname"] == "Greeny"

    patched = client.patch(
        f"/api/plants/{plant_id}",
        json={"nickname": "Green Bean", "room": "Office"},
    )
    assert patched.status_code == 200
    assert patched.json()["nickname"] == "Green Bean"
    assert patched.json()["species"] == "Golden Pothos"

    filtered = client.get("/api/plants", params={"room": "office"})
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [plant_id]

    watered = client.post(f"/api/plants/{plant_id}/water")
    assert watered.status_code == 200
    assert watered.json()["risk_score"] == 0
    assert watered.json()["status"] == "Healthy"
    assert watered.json()["days_since_watered"] == 0

    deleted = client.delete(f"/api/plants/{plant_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/plants/{plant_id}").status_code == 404


def test_create_validation(client: TestClient):
    response = client.post("/api/plants", json=plant_payload(watering_frequency=0))

    assert response.status_code == 422


def test_room_filters_are_dynamic_and_case_insensitive(client: TestClient):
    client.post("/api/plants", json=plant_payload(room="Kitchen"))
    client.post("/api/plants", json=plant_payload(nickname="Moss", room="Office"))

    response = client.get("/api/plants", params={"room": "KITCHEN"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["room"] == "Kitchen"

