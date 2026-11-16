"""T9 · Agenda del día para el admin (RF-13 · D8)."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, DomainError
from app.domain.rules import TZ
from app.models.barber import Barber
from app.models.booking import Booking
from app.repositories import bookings as bookings_repository
from app.repositories.catalog import get_barber, list_active_barbers
from app.schemas.agenda import AgendaBarber, AgendaBooking, AgendaOut


def _hhmm(booking_time: datetime) -> str:
    return booking_time.astimezone(TZ).strftime("%H:%M")


def _to_item(booking: Booking) -> AgendaBooking:
    # Sin teléfono: la agenda no expone datos de contacto (D8).
    return AgendaBooking(
        start=_hhmm(booking.start_at),
        end=_hhmm(booking.end_at),
        service=booking.service.name,
        client=booking.client_name,
        code=booking.code,
    )


def get_agenda(db: Session, day: date, barber_id: int | None = None) -> AgendaOut:
    if barber_id is not None and get_barber(db, barber_id) is None:
        raise DomainError(NOT_FOUND, "El barbero no existe")

    bookings = bookings_repository.confirmed_bookings_for_agenda(db, day, barber_id)

    # D8: todos los barberos ACTIVOS (aunque no tengan citas) + los inactivos
    # que sí tengan reservas CONFIRMADA ese día.
    barbers: dict[int, Barber] = {
        b.id: b
        for b in list_active_barbers(db)
        if barber_id is None or b.id == barber_id
    }
    for booking in bookings:
        barbers.setdefault(booking.barber.id, booking.barber)

    grouped: dict[int, list[AgendaBooking]] = {barber: [] for barber in barbers}
    for booking in bookings:
        grouped[booking.barber_id].append(_to_item(booking))

    return AgendaOut(
        date=day,
        barbers=[
            AgendaBarber(barber=barbers[barber].name, bookings=grouped[barber])
            for barber in sorted(barbers)
        ],
    )
