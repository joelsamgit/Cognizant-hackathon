from datetime import date, datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Sunlight(str, Enum):
    direct_sun = "Direct Sun"
    indirect_light = "Indirect Light"
    low_light = "Low Light"


class PlantDetails(BaseModel):
    indian_name: str = Field(max_length=200)
    common_name: str = Field(max_length=160)
    scientific_name: str = Field(max_length=200)
    difficulty: str = Field(max_length=100)
    category: str = Field(max_length=120)
    tagline: str = Field(max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    vibe: str = Field(max_length=200)
    ideal_spot: str = Field(max_length=500)
    name_origin: str = Field(max_length=2000)
    cultural_context: str = Field(max_length=2000)
    fun_fact: str = Field(max_length=2000)
    symbolism: str = Field(max_length=500)


class PlantCareGuide(BaseModel):
    sunlight: str = Field(max_length=300)
    sunlight_detail: str = Field(max_length=2000)
    watering_frequency_days: int = Field(gt=0, le=365)
    water_amount_ml: int = Field(gt=0, le=10000)
    watering_method: str = Field(max_length=2000)
    pro_tip: str = Field(max_length=2000)
    common_mistake: str = Field(max_length=2000)


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
    catalog_key: str | None = Field(default=None, max_length=100)
    details: PlantDetails | None = None
    care_guide: PlantCareGuide | None = None

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
    watering_frequency: int | None = Field(default=None, gt=0, le=365)


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
    catalog_key: str | None = Field(default=None, max_length=100)
    details: PlantDetails | None = None
    care_guide: PlantCareGuide | None = None

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


class WateringHistoryDay(BaseModel):
    date: date
    status: Literal["watered", "overdue", "ontrack"]


class PlantResponse(PlantFields):
    id: int
    created_at: datetime
    updated_at: datetime
    days_since_watered: int
    days_until_due: int
    watering_locked: bool
    next_watering_in_days: int
    risk_score: int
    status: str
    current_streak: int
    longest_streak: int
    consistency_pct: int
    total_waterings: int
    xp: int
    growth_stage: int = Field(ge=1, le=5)
    mood: Literal["happy", "doubtful", "sad"]
    history: list[WateringHistoryDay]
    milestone: str | None = None
    pet_safety: str | None = None
    pet_severity: str | None = None
    toxic_cats: bool | None = None
    toxic_dogs: bool | None = None
    placement_tip: str | None = None
    season: str
    base_watering_frequency: int
    effective_watering_frequency: int
    season_factor: float

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
