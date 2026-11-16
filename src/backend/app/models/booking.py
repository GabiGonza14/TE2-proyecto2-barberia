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
    event,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.rules import CLEANUP_BUFFER
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
        CheckConstraint(
            "blocked_until = end_at + interval '10 minutes'",
            name="ck_bookings_blocked_until",
        ),
        Index("ix_bookings_barber_id_start_at", "barber_id", "start_at"),
        ExcludeConstraint(
            (text("tstzrange(start_at, blocked_until, '[)')"), "&&"),
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
    # BR-12: fin del bloqueo = end_at + CLEANUP_BUFFER. Es una columna (y no
    # `end_at + interval`) porque los índices GiST exigen expresiones IMMUTABLE.
    blocked_until: Mapped[datetime] = mapped_column(
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


@event.listens_for(Booking, "before_insert")
def _fill_blocked_until(
    mapper: object, connection: object, target: Booking
) -> None:
    """BR-12: calcula la limpieza al crear la reserva, también con el ORM en
    los tests. La BD mantiene el CHECK de igualdad como red de seguridad."""
    if target.blocked_until is None and target.end_at is not None:
        target.blocked_until = target.end_at + CLEANUP_BUFFER
