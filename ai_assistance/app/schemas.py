from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class CareAction(str, Enum):
    WATER = "water"
    FERTILIZE = "fertilize"
    PRUNE = "prune"
    REPOT = "repot"
    MIST = "mist"
    CHECK = "check"
    MOVE = "move"
    OTHER = "other"


class CareInstructionRequest(BaseModel):
    plant_name: str = Field(..., min_length=1, max_length=100, description="Name of the plant")
    species: str = Field(..., min_length=1, max_length=100, description="Scientific or common species name")
    location: str = Field(..., min_length=1, max_length=200, description="General location (e.g., living room, balcony)")
    specific_spot: str = Field(..., min_length=1, max_length=200, description="Exact spot (e.g., near east window, shelf 2)")
    action: CareAction = Field(..., description="Care action to perform")
    amount_ml: Optional[int] = Field(default=None, ge=0, le=10000, description="Amount in milliliters (for water/fertilize)")
    notes: Optional[str] = Field(default="", max_length=500, description="Additional care notes")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the care was performed")

    @field_validator('amount_ml')
    @classmethod
    def validate_amount_for_action(cls, v, info):
        return v

    @model_validator(mode='after')
    def validate_amount_matches_action(self):
        action = self.action
        if action in [CareAction.WATER, CareAction.FERTILIZE, CareAction.MIST] and self.amount_ml is None:
            raise ValueError(f"amount_ml is required for action '{action.value}'")
        if action not in [CareAction.WATER, CareAction.FERTILIZE, CareAction.MIST] and self.amount_ml is not None:
            raise ValueError(f"amount_ml should not be provided for action '{action.value}'")
        return self


class CareInstructionResponse(BaseModel):
    instruction: str = Field(..., description="Generated care instruction")
    plant_name: str
    species: str
    location: str
    specific_spot: str
    action: CareAction
    amount_ml: Optional[int]
    notes: Optional[str]
    timestamp: datetime
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "ai-care-assistant"
    version: str = "1.0.0"


class WateringScheduleItem(BaseModel):
    plant_name: str = Field(..., min_length=1, max_length=100)
    species: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    specific_spot: str = Field(..., min_length=1, max_length=200)
    frequency_days: int = Field(..., ge=1, le=30, description="Watering frequency in days")
    amount_ml: int = Field(..., ge=0, le=10000, description="Amount per watering in ml")
    last_watered: datetime = Field(..., description="Last watering timestamp")
    notes: Optional[str] = Field(default="", max_length=500)
    base_frequency_days: Optional[int] = Field(default=None, ge=1, le=365)
    pet_safety: Optional[str] = None
    toxic_cats: Optional[bool] = None
    toxic_dogs: Optional[bool] = None
    placement_tip: Optional[str] = Field(default=None, max_length=300)


class VacationCareRequest(BaseModel):
    vacation_start: datetime = Field(..., description="Vacation start date/time")
    vacation_end: datetime = Field(..., description="Vacation end date/time")
    plants: list[WateringScheduleItem] = Field(..., min_length=1, description="Plants needing care during vacation")
    risk_level: Optional[str] = Field(default="medium", description="Overall risk level: low, medium, high")
    additional_notes: Optional[str] = Field(default="", max_length=1000, description="Any additional care context")
    season: Optional[str] = None
    season_factor: Optional[float] = Field(default=None, gt=0)

    @field_validator('vacation_end')
    @classmethod
    def validate_vacation_dates(cls, v, info):
        if 'vacation_start' in info.data and v <= info.data['vacation_start']:
            raise ValueError("vacation_end must be after vacation_start")
        return v

    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v):
        allowed = {"low", "medium", "high"}
        if v.lower() not in allowed:
            raise ValueError(f"risk_level must be one of: {allowed}")
        return v.lower()


class VacationCareResponse(BaseModel):
    caretaker_message: str = Field(..., description="Generated caretaker instructions for vacation period")
    vacation_start: datetime
    vacation_end: datetime
    plant_count: int
    risk_level: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
