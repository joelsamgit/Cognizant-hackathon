from datetime import datetime
from enum import Enum
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PetType(str, Enum):
    no_pets = "No pets"
    dogs = "Dogs"
    cats = "Cats"
    birds = "Birds"
    fish = "Fish"
    small_pets = "Small pets"
    reptiles = "Reptiles"
    other = "Other"


class ProfileFields(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    place: str = Field(min_length=2, max_length=160)
    pets: list[PetType] = Field(min_length=1, max_length=8)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @field_validator("full_name", "place")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("pets")
    @classmethod
    def validate_pets(cls, value: list[PetType]) -> list[PetType]:
        unique = list(dict.fromkeys(value))
        if PetType.no_pets in unique and len(unique) > 1:
            raise ValueError("No pets cannot be combined with another pet type")
        return unique

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown timezone") from exc
        return value


class UserSignup(ProfileFields):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=10000)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    place: str | None = Field(default=None, min_length=2, max_length=160)
    pets: list[PetType] | None = Field(default=None, min_length=1, max_length=8)

    @field_validator("full_name", "place")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("pets")
    @classmethod
    def validate_optional_pets(cls, value: list[PetType] | None) -> list[PetType] | None:
        if value is None:
            return None
        unique = list(dict.fromkeys(value))
        if PetType.no_pets in unique and len(unique) > 1:
            raise ValueError("No pets cannot be combined with another pet type")
        return unique


class UserProfileUpdate(ProfileFields):
    pass


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    place: str
    pets: list[PetType]
    timezone: str
    created_at: datetime
    updated_at: datetime
    account_current_streak: int = 0
    account_longest_streak: int = 0
    account_xp: int = 0
    account_growth_stage: int = Field(default=1, ge=1, le=5)
    account_mood: Literal["happy", "doubtful", "sad"] = "happy"
    account_total_waterings: int = 0

    model_config = ConfigDict(from_attributes=True)
