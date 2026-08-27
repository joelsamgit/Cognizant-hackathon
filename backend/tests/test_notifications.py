import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.main import app
from app.models.notification import NotificationDelivery, PushSubscription
from app.models.plant import Plant
from app.models.user import User
from app.services import google_identity, notifications as notification_service
from app.services.notifications import (
    DispatchResult,
    InvalidNotificationEvent,
    NotificationDeliveryError,
    decode_notification_event,
    deliver_queued_notification,
    dispatch_due_notifications,
)


def subscription_payload(**overrides):
    payload = {
        "endpoint": "https://push.example.test/subscription/1",
        "keys": {"p256dh": "public-encryption-key", "auth": "auth-secret"},
        "timezone": "UTC",
        "reminder_time": "09:00",
    }
    payload.update(overrides)
    return payload


def create_user(db_session: Session, email: str = "notifications@example.com") -> User:
    user = User(
        email=email,
        password_hash="!test-only",
        full_name="Notification Tester",
        place="Bengaluru",
        pets=["No pets"],
        timezone="UTC",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_notification_config_is_disabled_without_vapid_keys(client: TestClient):
    response = client.get("/api/notifications/config")

    assert response.status_code == 200
    assert response.json() == {"enabled": False, "public_key": None}


def test_subscription_can_be_saved_updated_and_removed(client: TestClient):
    created = client.post("/api/notifications/subscriptions", json=subscription_payload())
    assert created.status_code == 201
    assert created.json()["reminder_time"] == "09:00"

    updated = client.post(
        "/api/notifications/subscriptions",
        json=subscription_payload(reminder_time="18:30"),
    )
    assert updated.status_code == 201
    assert updated.json()["id"] == created.json()["id"]
    assert updated.json()["reminder_time"] == "18:30"

    deleted = client.request(
        "DELETE",
        "/api/notifications/subscriptions",
        json={"endpoint": subscription_payload()["endpoint"]},
    )
    assert deleted.status_code == 204


def test_dispatch_sends_once_per_plant_and_local_day(db_session: Session):
    now = datetime(2026, 8, 25, 9, 5, tzinfo=timezone.utc)
    user = create_user(db_session)
    plant = Plant(
        user_id=user.id,
        nickname="Nori",
        species="Calathea Orbifolia",
        room="Office",
        sunlight="Indirect Light",
        watering_frequency=5,
        last_watered=now - timedelta(days=7),
    )
    subscription = PushSubscription(
        user_id=user.id,
        endpoint="https://push.example.test/subscription/1",
        p256dh="public-encryption-key",
        auth="auth-secret",
        timezone="UTC",
        reminder_time="09:00",
        enabled=True,
    )
    db_session.add_all([plant, subscription])
    db_session.commit()

    calls = []

    def fake_sender(**kwargs):
        calls.append(kwargs)

    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        app_env="test",
        vapid_public_key="public-vapid-key",
        vapid_private_key="private-vapid-key",
        vapid_subject="mailto:test@example.com",
    )

    first = dispatch_due_notifications(db_session, settings, now=now, sender=fake_sender)
    second = dispatch_due_notifications(db_session, settings, now=now, sender=fake_sender)

    assert first.subscriptions_checked == 1
    assert first.sent == 1
    assert first.queued == 0
    assert first.failed == 0
    assert second.subscriptions_checked == 1
    assert second.sent == 0
    assert len(calls) == 1
    assert "Nori is overdue" in calls[0]["data"]


def test_dispatch_sends_needs_water_soon_on_next_scheduler_run(db_session: Session):
    now = datetime(2026, 8, 25, 12, 5, tzinfo=timezone.utc)
    user = create_user(db_session, "soon@example.com")
    plant = Plant(
        user_id=user.id,
        nickname="Fern",
        species="Calathea Orbifolia",
        room="Office",
        sunlight="Indirect Light",
        watering_frequency=7,
        last_watered=now - timedelta(days=4),
    )
    subscription = PushSubscription(
        user_id=user.id,
        endpoint="https://push.example.test/subscription/soon",
        p256dh="public-encryption-key",
        auth="auth-secret",
        timezone="UTC",
        reminder_time="09:00",
        enabled=True,
    )
    db_session.add_all([plant, subscription])
    db_session.commit()

    calls = []

    def fake_sender(**kwargs):
        calls.append(kwargs)

    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        app_env="test",
        vapid_public_key="public-vapid-key",
        vapid_private_key="private-vapid-key",
        vapid_subject="mailto:test@example.com",
    )

    result = dispatch_due_notifications(db_session, settings, now=now, sender=fake_sender)

    assert result.sent == 1
    assert "needs water soon" in calls[0]["data"]


def test_pubsub_dispatch_queues_and_worker_delivers_idempotently(db_session: Session):
    now = datetime(2026, 8, 25, 9, 5, tzinfo=timezone.utc)
    user = create_user(db_session, "pubsub@example.com")
    plant = Plant(
        user_id=user.id,
        nickname="Nori",
        species="Calathea Orbifolia",
        room="Office",
        sunlight="Indirect Light",
        watering_frequency=5,
        last_watered=now - timedelta(days=7),
    )
    subscription = PushSubscription(
        user_id=user.id,
        endpoint="https://push.example.test/subscription/1",
        p256dh="public-encryption-key",
        auth="auth-secret",
        timezone="UTC",
        reminder_time="09:00",
        enabled=True,
    )
    db_session.add_all([plant, subscription])
    db_session.commit()

    published: list[int] = []
    sent: list[dict] = []

    def fake_publisher(delivery_id: int, settings: Settings) -> str:
        published.append(delivery_id)
        return "message-1"

    def fake_sender(**kwargs):
        sent.append(kwargs)

    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        app_env="test",
        vapid_public_key="public-vapid-key",
        vapid_private_key="private-vapid-key",
        vapid_subject="mailto:test@example.com",
        gcp_project_id="plant-guardian-test",
        pubsub_notification_topic="plant-care-notifications",
        pubsub_push_service_account="pubsub-push@example.iam.gserviceaccount.com",
        pubsub_push_audience="https://backend.example.run.app",
    )

    result = dispatch_due_notifications(
        db_session,
        settings,
        now=now,
        sender=fake_sender,
        publisher=fake_publisher,
    )
    duplicate_scan = dispatch_due_notifications(
        db_session,
        settings,
        now=now,
        sender=fake_sender,
        publisher=fake_publisher,
    )

    assert result.queued == 1
    assert result.sent == 0
    assert duplicate_scan.queued == 0
    assert len(published) == 1
    assert sent == []

    def transient_failure(**kwargs):
        raise RuntimeError("temporary push provider outage")

    with pytest.raises(NotificationDeliveryError):
        deliver_queued_notification(
            db_session,
            published[0],
            settings,
            now=now,
            sender=transient_failure,
        )
    pending_delivery = db_session.get(NotificationDelivery, published[0])
    assert pending_delivery is not None
    assert pending_delivery.status == "pending"

    first_delivery = deliver_queued_notification(
        db_session,
        published[0],
        settings,
        now=now,
        sender=fake_sender,
    )
    duplicate_delivery = deliver_queued_notification(
        db_session,
        published[0],
        settings,
        now=now,
        sender=fake_sender,
    )

    assert first_delivery == "sent"
    assert duplicate_delivery == "ignored"
    assert len(sent) == 1
    delivery = db_session.get(NotificationDelivery, published[0])
    assert delivery is not None
    assert delivery.status == "sent"


def test_pubsub_event_decoder_validates_the_envelope_data():
    encoded = base64.b64encode(
        json.dumps(
            {
                "version": 1,
                "event_type": "plant.notification.requested",
                "delivery_id": 42,
            }
        ).encode("utf-8")
    ).decode("ascii")

    assert decode_notification_event(encoded).delivery_id == 42

    with pytest.raises(InvalidNotificationEvent):
        decode_notification_event("not-base64")


def test_google_oidc_verification_enforces_service_account_claims(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        google_identity.id_token,
        "verify_oauth2_token",
        lambda token, request, audience: {
            "email": "pubsub-push@example.iam.gserviceaccount.com",
            "email_verified": True,
            "aud": audience,
        },
    )

    claims = google_identity.verify_google_oidc_token(
        "signed-token",
        audience="https://backend.example.run.app",
        expected_email="pubsub-push@example.iam.gserviceaccount.com",
    )
    assert claims["email_verified"] is True

    with pytest.raises(google_identity.GoogleIdentityError):
        google_identity.verify_google_oidc_token(
            "signed-token",
            audience="https://backend.example.run.app",
            expected_email="different@example.iam.gserviceaccount.com",
        )


def test_pubsub_push_endpoint_verifies_google_identity(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        app_env="production",
        vapid_public_key="public-vapid-key",
        vapid_private_key="private-vapid-key",
        vapid_subject="mailto:test@example.com",
        gcp_project_id="plant-guardian-test",
        pubsub_notification_topic="plant-care-notifications",
        pubsub_push_service_account="pubsub-push@example.iam.gserviceaccount.com",
        pubsub_push_audience="https://backend.example.run.app",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    delivered: list[int] = []
    monkeypatch.setattr(
        google_identity,
        "verify_google_oidc_token",
        lambda *args, **kwargs: {"email_verified": True},
    )
    monkeypatch.setattr(
        notification_service,
        "deliver_queued_notification",
        lambda db, delivery_id, settings: delivered.append(delivery_id),
    )
    event_data = base64.b64encode(
        json.dumps(
            {
                "version": 1,
                "event_type": "plant.notification.requested",
                "delivery_id": 42,
            }
        ).encode("utf-8")
    ).decode("ascii")
    payload = {"message": {"data": event_data, "messageId": "message-1"}}

    unauthorized = client.post("/internal/notifications/pubsub", json=payload)
    accepted = client.post(
        "/internal/notifications/pubsub",
        json=payload,
        headers={"Authorization": "Bearer signed-google-token"},
    )

    assert unauthorized.status_code == 401
    assert accepted.status_code == 204
    assert delivered == [42]


def test_scheduler_dispatch_endpoint_supports_oidc(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        app_env="production",
        vapid_public_key="public-vapid-key",
        vapid_private_key="private-vapid-key",
        vapid_subject="mailto:test@example.com",
        scheduler_service_account="scheduler@example.iam.gserviceaccount.com",
        scheduler_audience="https://backend.example.run.app",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(
        google_identity,
        "verify_google_oidc_token",
        lambda *args, **kwargs: {"email_verified": True},
    )
    monkeypatch.setattr(
        notification_service,
        "dispatch_due_notifications",
        lambda db, settings: DispatchResult(subscriptions_checked=0),
    )

    unauthorized = client.post("/internal/notifications/dispatch")
    accepted = client.post(
        "/internal/notifications/dispatch",
        headers={"Authorization": "Bearer signed-google-token"},
    )

    assert unauthorized.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json() == {
        "subscriptions_checked": 0,
        "notifications_queued": 0,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }
