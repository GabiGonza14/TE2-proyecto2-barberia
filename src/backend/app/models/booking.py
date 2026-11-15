from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.barber import Barber
    from app.models.service import Service

STATUS_CONFIRMED = "CONFIRMADA"
STATUS_CANCELLED = "CANCELADA"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(
            "end_at > start_at", name="ck_bookings_end_after_start"
        ),
        CheckConstraint(
            "status IN ('CONFIRMADA', 'CANCELADA')",
            name="ck_bookings_status",
        ),
        Index("ix_bookings_barber_id_start_at", "barber_id", "start_at"),
        ExcludeConstraint(
            (text("tstzrange(start_at, end_at, '[)')"), "&&"),
            ("barber_id", "="),
            name="no_double_booking",
            using="gist",
            where=text("status = 'CONFIRMADA'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(CHAR(6), nullable=False, unique=True)
    barber_id: Mapped[int] = mapped_column(
        ForeignKey("barbers.id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"), nullable=False
    )
    client_name: Mapped[str] = mapped_column(String(60), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(8), nullable=False)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        server_default=text("'CONFIRMADA'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    barber: Mapped["Barber"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
