import base64
import binascii
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError
from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.notification import NotificationDelivery, PushSubscription
from app.models.plant import Plant
from app.schemas.notification import NotificationRequestedEvent, PushSubscriptionCreate
from app.services.risk import HIGH_RISK, NEEDS_WATER_SOON, calculate_care_metrics


logger = logging.getLogger(__name__)
PushSender = Callable[..., object]
NotificationPublisher = Callable[[int, Settings], str]


class NotificationConfigurationError(RuntimeError):
    pass


class NotificationDeliveryError(RuntimeError):
    pass


class InvalidNotificationEvent(RuntimeError):
    pass


@dataclass(frozen=True)
class DispatchResult:
    subscriptions_checked: int
    queued: int = 0
    sent: int = 0
    failed: int = 0


def upsert_subscription(
    db: Session,
    payload: PushSubscriptionCreate,
    user_id: int,
) -> PushSubscription:
    subscription = db.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    )
    if subscription is None:
        subscription = PushSubscription(endpoint=payload.endpoint, user_id=user_id)
        db.add(subscription)

    subscription.user_id = user_id
    subscription.p256dh = payload.keys.p256dh
    subscription.auth = payload.keys.auth
    subscription.timezone = payload.timezone
    subscription.reminder_time = payload.reminder_time
    subscription.enabled = True
    subscription.failure_count = 0
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db: Session, endpoint: str, user_id: int) -> bool:
    subscription = db.scalar(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user_id,
        )
    )
    if subscription is None:
        return False
    db.delete(subscription)
    db.commit()
    return True


def send_test_notification(
    db: Session,
    endpoint: str,
    user_id: int,
    settings: Settings,
    *,
    sender: PushSender = webpush,
) -> bool:
    _require_vapid(settings)
    subscription = db.scalar(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user_id,
            PushSubscription.enabled.is_(True),
        )
    )
    if subscription is None:
        return False

    try:
        _send(
            subscription,
            {
                "title": "Plant Guardian reminders are ready",
                "body": "You will be notified when a plant needs water soon or is overdue.",
                "tag": "plant-guardian-test",
                "url": "/",
            },
            settings,
            sender=sender,
        )
    except WebPushException as exc:
        subscription.failure_count += 1
        status_code = getattr(exc.response, "status_code", None)
        if status_code in {404, 410}:
            subscription.enabled = False
        db.commit()
        raise NotificationDeliveryError("The test notification could not be delivered") from exc
    _mark_success(db, subscription)
    return True


def dispatch_due_notifications(
    db: Session,
    settings: Settings,
    *,
    now: datetime | None = None,
    sender: PushSender = webpush,
    publisher: NotificationPublisher | None = None,
) -> DispatchResult:
    _require_vapid(settings)
    current = _as_utc(now or datetime.now(timezone.utc))
    subscriptions = list(
        db.scalars(
            select(PushSubscription).where(PushSubscription.enabled.is_(True))
        ).all()
    )
    user_ids = {subscription.user_id for subscription in subscriptions}
    plants = list(
        db.scalars(select(Plant).where(Plant.user_id.in_(user_ids))).all()
        if user_ids
        else []
    )
    plants_by_user: dict[int, list[Plant]] = {}
    for plant in plants:
        plants_by_user.setdefault(plant.user_id, []).append(plant)
    sent = 0
    queued = 0
    failed = 0
    publish = publisher or publish_notification_event

    for subscription in subscriptions:
        local_now = _local_time(current, subscription.timezone)
        delivery_date = local_now.date()

        for plant in plants_by_user.get(subscription.user_id, []):
            metrics = calculate_care_metrics(
                plant.last_watered,
                plant.watering_frequency,
                now=current,
            )
            if metrics.status not in {NEEDS_WATER_SOON, HIGH_RISK}:
                continue

            kind = "overdue" if metrics.status == HIGH_RISK else "soon"
            delivery = db.scalar(
                select(NotificationDelivery).where(
                    NotificationDelivery.subscription_id == subscription.id,
                    NotificationDelivery.plant_id == plant.id,
                    NotificationDelivery.kind == kind,
                    NotificationDelivery.care_date == delivery_date,
                )
            )
            if delivery is not None and delivery.status in {"pending", "sent"}:
                continue

            if delivery is None:
                delivery = NotificationDelivery(
                    subscription_id=subscription.id,
                    plant_id=plant.id,
                    kind=kind,
                    care_date=delivery_date,
                    status="pending",
                )
                db.add(delivery)
            else:
                delivery.status = "pending"
            db.commit()

            if settings.pubsub_notifications_enabled:
                try:
                    publish(delivery.id, settings)
                except Exception:
                    failed += 1
                    delivery.status = "failed"
                    logger.exception("Pub/Sub publish failed for delivery %s", delivery.id)
                    db.commit()
                else:
                    queued += 1
                continue

            try:
                _send(
                    subscription,
                    _notification_payload(plant, metrics.days_until_due, delivery_date.isoformat()),
                    settings,
                    sender=sender,
                )
            except WebPushException as exc:
                failed += 1
                delivery.status = "failed"
                subscription.failure_count += 1
                status_code = getattr(exc.response, "status_code", None)
                if status_code in {404, 410}:
                    subscription.enabled = False
                logger.warning("Push delivery failed for subscription %s: %s", subscription.id, exc)
                db.commit()
            except Exception:
                failed += 1
                delivery.status = "failed"
                subscription.failure_count += 1
                logger.exception(
                    "Unexpected push delivery failure for subscription %s",
                    subscription.id,
                )
                db.commit()
            else:
                sent += 1
                delivery.status = "sent"
                delivery.sent_at = current
                _mark_success(db, subscription, commit=False, at=current)
                db.commit()

    return DispatchResult(
        subscriptions_checked=len(subscriptions),
        queued=queued,
        sent=sent,
        failed=failed,
    )


def publish_notification_event(delivery_id: int, settings: Settings) -> str:
    from google.cloud import pubsub_v1

    event = NotificationRequestedEvent(delivery_id=delivery_id)
    publisher = pubsub_v1.PublisherClient()
    topic = settings.pubsub_notification_topic
    topic_path = (
        topic
        if topic.startswith("projects/")
        else publisher.topic_path(settings.gcp_project_id, topic)
    )
    future = publisher.publish(
        topic_path,
        event.model_dump_json().encode("utf-8"),
        event_type=event.event_type,
        delivery_id=str(delivery_id),
    )
    return future.result(timeout=30)


def decode_notification_event(encoded_data: str) -> NotificationRequestedEvent:
    try:
        raw = base64.b64decode(encoded_data, validate=True)
        return NotificationRequestedEvent.model_validate_json(raw)
    except (binascii.Error, UnicodeDecodeError, ValidationError) as exc:
        raise InvalidNotificationEvent("Invalid Pub/Sub notification event") from exc


def deliver_queued_notification(
    db: Session,
    delivery_id: int,
    settings: Settings,
    *,
    now: datetime | None = None,
    sender: PushSender = webpush,
) -> Literal["sent", "ignored", "cancelled", "discarded"]:
    _require_vapid(settings)
    current = _as_utc(now or datetime.now(timezone.utc))
    delivery = db.scalar(
        select(NotificationDelivery)
        .where(NotificationDelivery.id == delivery_id)
        .with_for_update()
    )
    if delivery is None or delivery.status in {"sent", "cancelled"}:
        return "ignored"

    subscription = db.get(PushSubscription, delivery.subscription_id)
    plant = db.get(Plant, delivery.plant_id)
    if subscription is None or plant is None or not subscription.enabled:
        delivery.status = "failed"
        db.commit()
        return "discarded"

    metrics = calculate_care_metrics(
        plant.last_watered,
        plant.watering_frequency,
        now=current,
    )
    if metrics.status not in {NEEDS_WATER_SOON, HIGH_RISK}:
        delivery.status = "cancelled"
        db.commit()
        return "cancelled"

    try:
        _send(
            subscription,
            _notification_payload(
                plant,
                metrics.days_until_due,
                delivery.care_date.isoformat(),
            ),
            settings,
            sender=sender,
        )
    except WebPushException as exc:
        subscription.failure_count += 1
        status_code = getattr(exc.response, "status_code", None)
        if status_code in {404, 410}:
            subscription.enabled = False
            delivery.status = "failed"
            db.commit()
            return "discarded"
        db.commit()
        raise NotificationDeliveryError("Push delivery failed and should be retried") from exc
    except Exception as exc:
        subscription.failure_count += 1
        db.commit()
        raise NotificationDeliveryError("Push delivery failed and should be retried") from exc

    delivery.status = "sent"
    delivery.sent_at = current
    _mark_success(db, subscription, commit=False, at=current)
    db.commit()
    return "sent"


def _notification_payload(plant: Plant, days_until_due: int, care_date: str) -> dict[str, str]:
    if days_until_due > 0:
        body = f"Water it within {days_until_due} {('day' if days_until_due == 1 else 'days')} to keep it healthy."
        title = f"{plant.nickname} needs water soon"
    else:
        overdue = abs(days_until_due)
        unit = "day" if overdue == 1 else "days"
        title = f"{plant.nickname} is overdue"
        body = f"It is {overdue} {unit} beyond its normal care window."
    return {
        "title": title,
        "body": body,
        "tag": f"plant-{plant.id}-care-{care_date}",
        "url": "/",
    }


def _send(
    subscription: PushSubscription,
    payload: dict[str, str],
    settings: Settings,
    *,
    sender: PushSender,
) -> None:
    sender(
        subscription_info={
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        },
        data=json.dumps(payload),
        vapid_private_key=settings.vapid_private_key,
        vapid_claims={"sub": settings.vapid_subject},
        ttl=3600,
    )


def _mark_success(
    db: Session,
    subscription: PushSubscription,
    *,
    commit: bool = True,
    at: datetime | None = None,
) -> None:
    subscription.failure_count = 0
    subscription.last_success_at = at or datetime.now(timezone.utc)
    if commit:
        db.commit()


def _require_vapid(settings: Settings) -> None:
    if not settings.notifications_enabled:
        raise NotificationConfigurationError("Web Push is not configured")


def _local_time(now: datetime, timezone_name: str) -> datetime:
    try:
        return now.astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return now


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
