from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Plant(Base):
    __tablename__ = "plants"
    __table_args__ = (
        CheckConstraint("watering_frequency > 0", name="ck_plants_watering_frequency_positive"),
        CheckConstraint(
            "sunlight IN ('Direct Sun', 'Indirect Light', 'Low Light')",
            name="ck_plants_sunlight_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    species: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    room: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sunlight: Mapped[str] = mapped_column(String(40), nullable=False)
    watering_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    last_watered: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

