from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PlantWateringSchedule(BaseModel):
    plant_name: str = Field(..., min_length=1, max_length=100)
    species: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    specific_spot: str = Field(..., min_length=1, max_length=200)
    frequency_days: int = Field(..., ge=1, le=30)
    amount_ml: int = Field(..., ge=0, le=10000)
    last_watered: datetime
    notes: Optional[str] = Field(default="", max_length=500)
    base_frequency_days: Optional[int] = Field(default=None, ge=1, le=365)
    pet_safety: Optional[str] = None
    toxic_cats: Optional[bool] = None
    toxic_dogs: Optional[bool] = None
    placement_tip: Optional[str] = Field(default=None, max_length=300)


class VacationModeRequest(BaseModel):
    vacation_start: datetime
    vacation_end: datetime
    plants: list[PlantWateringSchedule] = Field(..., min_length=1)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    additional_notes: Optional[str] = Field(default="", max_length=1000)
    season: Optional[str] = None
    season_factor: Optional[float] = Field(default=None, gt=0)

    @field_validator('vacation_end')
    @classmethod
    def validate_dates(cls, v, info):
        if 'vacation_start' in info.data and v <= info.data['vacation_start']:
            raise ValueError("vacation_end must be after vacation_start")
        return v


class VacationModeResponse(BaseModel):
    vacation_id: str
    vacation_start: datetime
    vacation_end: datetime
    plant_count: int
    risk_level: RiskLevel
    watering_schedule: list[PlantWateringSchedule]
    caretaker_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "vacation-mode"
    version: str = "1.0.0"
