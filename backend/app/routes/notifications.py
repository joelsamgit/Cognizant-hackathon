import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationConfigResponse,
    NotificationDispatchResponse,
    PubSubPushEnvelope,
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    PushSubscriptionResponse,
)
from app.services import google_identity, notifications as notification_service


router = APIRouter(prefix="/notifications", tags=["notifications"])
internal_router = APIRouter(prefix="/internal/notifications", tags=["internal"])
DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(get_current_user)]
logger = logging.getLogger(__name__)


@router.get("/config", response_model=NotificationConfigResponse)
def notification_config(
    settings: AppSettings,
    user: CurrentUser,
) -> NotificationConfigResponse:
    return NotificationConfigResponse(
        enabled=settings.notifications_enabled,
        public_key=settings.vapid_public_key or None,
    )


@router.post(
    "/subscriptions",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_subscription(
    payload: PushSubscriptionCreate,
    db: DbSession,
    user: CurrentUser,
) -> PushSubscriptionResponse:
    return PushSubscriptionResponse.model_validate(
        notification_service.upsert_subscription(db, payload, user.id)
    )


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def remove_subscription(
    payload: PushSubscriptionDelete,
    db: DbSession,
    user: CurrentUser,
) -> Response:
    notification_service.delete_subscription(db, payload.endpoint, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/test", status_code=status.HTTP_204_NO_CONTENT)
def test_notification(
    payload: PushSubscriptionDelete,
    db: DbSession,
    settings: AppSettings,
    user: CurrentUser,
) -> Response:
    try:
        found = notification_service.send_test_notification(
            db,
            payload.endpoint,
            user.id,
            settings,
        )
    except notification_service.NotificationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except notification_service.NotificationDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push subscription not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@internal_router.post("/dispatch", response_model=NotificationDispatchResponse)
def dispatch_notifications(
    db: DbSession,
    settings: AppSettings,
    x_notification_token: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> NotificationDispatchResponse:
    _authenticate_dispatch_request(
        settings,
        notification_token=x_notification_token,
        authorization=authorization,
    )

    try:
        result = notification_service.dispatch_due_notifications(db, settings)
    except notification_service.NotificationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return NotificationDispatchResponse(
        subscriptions_checked=result.subscriptions_checked,
        notifications_queued=result.queued,
        notifications_sent=result.sent,
        notifications_failed=result.failed,
    )


@internal_router.post("/pubsub", status_code=status.HTTP_204_NO_CONTENT)
def receive_pubsub_notification(
    payload: PubSubPushEnvelope,
    db: DbSession,
    settings: AppSettings,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    if not settings.pubsub_notifications_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pub/Sub notification delivery is not configured",
        )

    _verify_google_request(
        authorization,
        audience=settings.pubsub_push_audience,
        expected_email=settings.pubsub_push_service_account,
    )

    try:
        event = notification_service.decode_notification_event(payload.message.data)
    except notification_service.InvalidNotificationEvent:
        logger.warning(
            "Acknowledging malformed Pub/Sub message %s",
            payload.message.message_id or "unknown",
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    try:
        notification_service.deliver_queued_notification(
            db,
            event.delivery_id,
            settings,
        )
    except notification_service.NotificationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except notification_service.NotificationDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification delivery will be retried",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _authenticate_dispatch_request(
    settings: Settings,
    *,
    notification_token: str | None,
    authorization: str | None,
) -> None:
    if (
        settings.notification_dispatch_token
        and notification_token == settings.notification_dispatch_token
    ):
        return

    oidc_configured = bool(settings.scheduler_service_account and settings.scheduler_audience)
    if oidc_configured and authorization:
        _verify_google_request(
            authorization,
            audience=settings.scheduler_audience,
            expected_email=settings.scheduler_service_account,
        )
        return

    authentication_configured = bool(settings.notification_dispatch_token or oidc_configured)
    if authentication_configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid notification dispatcher credentials",
        )
    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification dispatcher authentication is not configured",
        )


def _verify_google_request(
    authorization: str | None,
    *,
    audience: str,
    expected_email: str,
) -> None:
    token = _bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A Google OIDC bearer token is required",
        )
    try:
        google_identity.verify_google_oidc_token(
            token,
            audience=audience,
            expected_email=expected_email,
        )
    except google_identity.GoogleIdentityError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google OIDC credentials",
        ) from exc


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token
