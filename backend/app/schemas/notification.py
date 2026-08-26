from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=512)
    auth: str = Field(min_length=1, max_length=256)


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(min_length=1, max_length=4096)
    keys: PushKeys
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    reminder_time: str = Field(default="09:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown timezone") from exc
        return value


class PushSubscriptionDelete(BaseModel):
    endpoint: str = Field(min_length=1, max_length=4096)


class PushSubscriptionResponse(BaseModel):
    id: int
    timezone: str
    reminder_time: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationConfigResponse(BaseModel):
    enabled: bool
    public_key: str | None


class NotificationDispatchResponse(BaseModel):
    subscriptions_checked: int
    notifications_queued: int
    notifications_sent: int
    notifications_failed: int


class NotificationRequestedEvent(BaseModel):
    version: Literal[1] = 1
    event_type: Literal["plant.notification.requested"] = "plant.notification.requested"
    delivery_id: int = Field(gt=0)


class PubSubMessage(BaseModel):
    data: str = Field(min_length=1)
    message_id: str | None = Field(default=None, alias="messageId")

    model_config = ConfigDict(populate_by_name=True)


class PubSubPushEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None
