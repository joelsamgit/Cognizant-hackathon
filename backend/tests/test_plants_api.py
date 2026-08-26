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
    created = client.post("/api/plants?season=post-monsoon", json=plant_payload())
    assert created.status_code == 201
    plant = created.json()
    assert plant["risk_score"] == 57
    assert plant["status"] == "Needs Water Soon"

    plant_id = plant["id"]
    fetched = client.get(f"/api/plants/{plant_id}?season=post-monsoon")
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


def test_structured_profile_and_care_guide_round_trip(client: TestClient):
    response = client.post(
        "/api/plants",
        json=plant_payload(
            catalog_key="money_plant_pothos",
            details={
                "indian_name": "Money Plant / Paisa Bel",
                "common_name": "Golden Pothos",
                "scientific_name": "Epipremnum aureum",
                "difficulty": "Super Easy",
                "category": "Classic Indian Vine",
                "tagline": "A familiar evergreen vine.",
                "image_url": None,
                "vibe": "Lush and auspicious",
                "ideal_spot": "A bright living room corner",
                "name_origin": "Its leaves are associated with abundance.",
                "cultural_context": "Often grown in water bottles in Indian homes.",
                "fun_fact": "It can grow in water for long periods.",
                "symbolism": "Prosperity and positive energy.",
            },
            care_guide={
                "sunlight": "Bright Indirect Light",
                "sunlight_detail": "Keep away from harsh afternoon sun.",
                "watering_frequency_days": 6,
                "water_amount_ml": 300,
                "watering_method": "Water after the top layer dries.",
                "pro_tip": "Train the vine upward.",
                "common_mistake": "Leaving roots in stale water.",
            },
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["catalog_key"] == "money_plant_pothos"
    assert body["details"]["scientific_name"] == "Epipremnum aureum"
    assert body["details"]["fun_fact"] == "It can grow in water for long periods."
    assert body["care_guide"]["water_amount_ml"] == 300


def test_room_filters_are_dynamic_and_case_insensitive(client: TestClient):
    client.post("/api/plants", json=plant_payload(room="Kitchen"))
    client.post("/api/plants", json=plant_payload(nickname="Moss", room="Office"))

    response = client.get("/api/plants", params={"room": "KITCHEN"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["room"] == "Kitchen"


def test_watering_and_manual_care_are_recorded_in_history(client: TestClient):
    created = client.post("/api/plants", json=plant_payload()).json()
    plant_id = created["id"]

    watered = client.post(f"/api/plants/{plant_id}/water")
    assert watered.status_code == 200

    checked = client.post(
        f"/api/plants/{plant_id}/events",
        json={
            "action": "check",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "result": "still_damp",
            "notes": "Soil is damp below the surface",
        },
    )
    assert checked.status_code == 201
    assert checked.json()["result"] == "still_damp"

    history = client.get(f"/api/plants/{plant_id}/events")
    assert history.status_code == 200
    assert [event["action"] for event in history.json()] == ["check", "water", "water"]
    assert history.json()[-1]["notes"] == "Initial watering record"
