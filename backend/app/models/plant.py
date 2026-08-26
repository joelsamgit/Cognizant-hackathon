from datetime import datetime, timezone

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    species: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    room: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sunlight: Mapped[str] = mapped_column(String(40), nullable=False)
    watering_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    last_watered: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pet_safety: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pet_severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    toxic_cats: Mapped[bool | None] = mapped_column(nullable=True)
    toxic_dogs: Mapped[bool | None] = mapped_column(nullable=True)
    placement_tip: Mapped[str | None] = mapped_column(String(300), nullable=True)
    catalog_key: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    details: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    care_guide: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    waterings: Mapped[list["Watering"]] = relationship(
        back_populates="plant",
        cascade="all, delete-orphan",
        order_by="Watering.watered_at.desc()",
    )


class Watering(Base):
    __tablename__ = "waterings"
    __table_args__ = (
        Index("ix_waterings_plant_id_watered_at", "plant_id", text("watered_at DESC")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
    )
    watered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    plant: Mapped[Plant] = relationship(back_populates="waterings")
