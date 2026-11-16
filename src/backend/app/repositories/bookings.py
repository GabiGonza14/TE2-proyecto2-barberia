from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.domain.rules import TZ
from app.models.booking import STATUS_CONFIRMED, Booking


def confirmed_bookings_for_day(
    db: Session, barber_id: int, day: date
) -> list[Booking]:
    day_start = datetime.combine(day, time.min, TZ)
    day_end = day_start + timedelta(days=1)
    return list(
        db.scalars(
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.status == STATUS_CONFIRMED,
                Booking.start_at < day_end,
                Booking.end_at > day_start,
            )
            .order_by(Booking.start_at)
        )
    )


def find_overlapping(
    db: Session, barber_id: int, start: datetime, end: datetime
) -> list[Booking]:
    return list(
        db.scalars(
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.status == STATUS_CONFIRMED,
                Booking.start_at < end,
                Booking.end_at > start,
            )
            .order_by(Booking.start_at)
        )
    )


def add_booking(
    db: Session,
    *,
    code: str,
    barber_id: int,
    service_id: int,
    client_name: str,
    client_phone: str,
    start_at: datetime,
    end_at: datetime,
) -> Booking:
    booking = Booking(
        code=code,
        barber_id=barber_id,
        service_id=service_id,
        client_name=client_name,
        client_phone=client_phone,
        start_at=start_at,
        end_at=end_at,
        status=STATUS_CONFIRMED,
    )
    db.add(booking)
    db.flush()
    return booking


def get_by_code(
    db: Session, code: str, *, for_update: bool = False
) -> Booking | None:
    """Busca una reserva por código. Con for_update bloquea la fila
    (SELECT … FOR UPDATE) para que dos cancelaciones simultáneas no
    pisen la misma reserva."""
    statement = select(Booking).where(Booking.code == code)
    if for_update:
        statement = statement.with_for_update()
    return db.scalars(statement).one_or_none()



def confirmed_bookings_for_agenda(
    db: Session, day: date, barber_id: int | None = None
) -> list[Booking]:
    """Reservas CONFIRMADA que caen en `day` (America/Panama), con barbero y
    servicio cargados en la misma consulta (sin N+1), ordenadas por hora."""
    day_start = datetime.combine(day, time.min, TZ)
    day_end = day_start + timedelta(days=1)
    statement = (
        select(Booking)
        .options(joinedload(Booking.barber), joinedload(Booking.service))
        .where(
            Booking.status == STATUS_CONFIRMED,
            Booking.start_at < day_end,
            Booking.end_at > day_start,
        )
        .order_by(Booking.start_at, Booking.id)
    )
    if barber_id is not None:
        statement = statement.where(Booking.barber_id == barber_id)
    return list(db.scalars(statement))
