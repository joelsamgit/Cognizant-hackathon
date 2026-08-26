from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CareEvent(Base):
    __tablename__ = "care_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('water', 'check', 'fertilize', 'mist', 'prune', 'repot')",
            name="ck_care_events_action_valid",
        ),
        CheckConstraint(
            "result IN ('watered', 'still_damp', 'completed', 'skipped')",
            name="ck_care_events_result_valid",
        ),
        CheckConstraint(
            "amount_ml IS NULL OR (amount_ml >= 0 AND amount_ml <= 10000)",
            name="ck_care_events_amount_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    amount_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(24), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
