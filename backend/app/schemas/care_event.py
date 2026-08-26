from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CareAction(str, Enum):
    water = "water"
    check = "check"
    fertilize = "fertilize"
    mist = "mist"
    prune = "prune"
    repot = "repot"


class CareResult(str, Enum):
    watered = "watered"
    still_damp = "still_damp"
    completed = "completed"
    skipped = "skipped"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CareEventCreate(BaseModel):
    action: CareAction
    occurred_at: datetime = Field(default_factory=utc_now)
    amount_ml: int | None = Field(default=None, ge=0, le=10000)
    result: CareResult | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("care time cannot be in the future")
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_action_details(self):
        allowed_results = {
            CareAction.water: {CareResult.watered, CareResult.skipped},
            CareAction.check: {CareResult.completed, CareResult.still_damp, CareResult.skipped},
            CareAction.fertilize: {CareResult.completed, CareResult.skipped},
            CareAction.mist: {CareResult.completed, CareResult.skipped},
            CareAction.prune: {CareResult.completed, CareResult.skipped},
            CareAction.repot: {CareResult.completed, CareResult.skipped},
        }
        if self.result is not None and self.result not in allowed_results[self.action]:
            raise ValueError(f"result '{self.result.value}' is not valid for action '{self.action.value}'")
        if self.amount_ml is not None and self.action not in {
            CareAction.water,
            CareAction.fertilize,
            CareAction.mist,
        }:
            raise ValueError(f"amount_ml is not valid for action '{self.action.value}'")
        return self


class CareEventResponse(BaseModel):
    id: int
    plant_id: int
    action: CareAction
    occurred_at: datetime
    amount_ml: int | None
    result: CareResult
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
