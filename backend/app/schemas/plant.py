from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Sunlight(str, Enum):
    direct_sun = "Direct Sun"
    indirect_light = "Indirect Light"
    low_light = "Low Light"


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class PlantFields(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=1, max_length=160)
    room: str = Field(min_length=1, max_length=100)
    sunlight: Sunlight
    watering_frequency: int = Field(gt=0, le=365)
    last_watered: datetime
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("nickname", "species", "room")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("last_watered")
    @classmethod
    def validate_last_watered(cls, value: datetime) -> datetime:
        normalized = normalize_datetime(value)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("last watered cannot be in the future")
        return normalized


class PlantCreate(PlantFields):
    pass


class PlantPut(PlantFields):
    pass


class PlantPatch(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=100)
    species: str | None = Field(default=None, min_length=1, max_length=160)
    room: str | None = Field(default=None, min_length=1, max_length=100)
    sunlight: Sunlight | None = None
    watering_frequency: int | None = Field(default=None, gt=0, le=365)
    last_watered: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("nickname", "species", "room")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("notes")
    @classmethod
    def normalize_optional_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("last_watered")
    @classmethod
    def validate_optional_last_watered(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        normalized = normalize_datetime(value)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("last watered cannot be in the future")
        return normalized


class PlantResponse(PlantFields):
    id: int
    created_at: datetime
    updated_at: datetime
    days_since_watered: int
    days_until_due: int
    risk_score: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str

