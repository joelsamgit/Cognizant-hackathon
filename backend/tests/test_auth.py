from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserSession


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


def signup_payload(**overrides):
    payload = {
        "email": "new.gardener@example.com",
        "password": "strong-password-123",
        "full_name": "Asha Nair",
        "place": "Kochi",
        "pets": ["Cats"],
        "timezone": "Asia/Kolkata",
    }
    payload.update(overrides)
    return payload


def test_signup_creates_a_secure_session_and_required_profile(
    anonymous_client: TestClient,
    db_session: Session,
):
    response = anonymous_client.post("/api/auth/signup", json=signup_payload())

    assert response.status_code == 201
    assert response.json()["full_name"] == "Asha Nair"
    assert response.json()["place"] == "Kochi"
    assert response.json()["pets"] == ["Cats"]
    assert "password" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]

    raw_token = anonymous_client.cookies.get("plant_guardian_session")
    stored_session = db_session.scalar(select(UserSession))
    assert raw_token
    assert stored_session is not None
    assert stored_session.token_hash != raw_token
    assert len(stored_session.token_hash) == 64


def test_signup_requires_valid_pet_selection(anonymous_client: TestClient):
    missing = anonymous_client.post(
        "/api/auth/signup",
        json=signup_payload(email="missing-pets@example.com", pets=[]),
    )
    contradictory = anonymous_client.post(
        "/api/auth/signup",
        json=signup_payload(
            email="contradictory@example.com",
            pets=["No pets", "Dogs"],
        ),
    )

    assert missing.status_code == 422
    assert contradictory.status_code == 422


def test_login_profile_update_and_logout(anonymous_client: TestClient):
    anonymous_client.post("/api/auth/signup", json=signup_payload())
    logout = anonymous_client.post("/api/auth/logout")
    assert logout.status_code == 204
    assert anonymous_client.get("/api/auth/me").status_code == 401

    invalid = anonymous_client.post(
        "/api/auth/login",
        json={"email": "new.gardener@example.com", "password": "wrong-password"},
    )
    assert invalid.status_code == 401

    login = anonymous_client.post(
        "/api/auth/login",
        json={
            "email": "NEW.GARDENER@example.com",
            "password": "strong-password-123",
        },
    )
    assert login.status_code == 200

    updated = anonymous_client.patch(
        "/api/profile",
        json={
            "full_name": "Asha Menon",
            "place": "Thrissur",
            "pets": ["Cats", "Dogs"],
            "timezone": "Asia/Kolkata",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Asha Menon"
    assert updated.json()["pets"] == ["Cats", "Dogs"]


def test_duplicate_email_is_rejected(anonymous_client: TestClient):
    first = anonymous_client.post("/api/auth/signup", json=signup_payload())
    second = anonymous_client.post("/api/auth/signup", json=signup_payload())

    assert first.status_code == 201
    assert second.status_code == 409


def test_plant_data_is_private_to_each_account(client: TestClient):
    created = client.post("/api/plants", json=plant_payload(nickname="Private Fern"))
    assert created.status_code == 201
    plant_id = created.json()["id"]

    client.post("/api/auth/logout")
    second_signup = client.post(
        "/api/auth/signup",
        json=signup_payload(email="second.gardener@example.com"),
    )
    assert second_signup.status_code == 201

    assert client.get(f"/api/plants/{plant_id}").status_code == 404
    assert client.get("/api/plants").json() == []


def test_plant_api_requires_authentication(anonymous_client: TestClient):
    assert anonymous_client.get("/api/plants").status_code == 401
