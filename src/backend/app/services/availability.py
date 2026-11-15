from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import (
    BARBER_INACTIVE,
    NOT_FOUND,
    PAST_DATE,
    TOO_FAR_AHEAD,
    DomainError,
)
from app.domain.rules import (
    MAX_DAYS_AHEAD,
    OPENING_TIME,
    SLOT_MINUTES,
    TZ,
    check_booking_window,
    compute_end,
    is_open_day,
    is_within_business_hours,
    overlaps,
)
from app.repositories.bookings import confirmed_bookings_for_day
from app.repositories.catalog import get_barber, get_service


def _empty_result(
    day: date, barber_id: int, service_id: int, reason: str
) -> dict[str, Any]:
    return {
        "date": day,
        "barber_id": barber_id,
        "service_id": service_id,
        "slots": [],
        "reason": reason,
    }


def get_availability(
    db: Session,
    barber_id: int,
    service_id: int,
    day: date,
    now: datetime,
) -> dict[str, Any]:
    service = get_service(db, service_id)
    if service is None:
        raise DomainError(NOT_FOUND, "Servicio no encontrado")

    barber = get_barber(db, barber_id)
    if barber is None:
        raise DomainError(NOT_FOUND, "Barbero no encontrado")
    if not barber.active:
        raise DomainError(BARBER_INACTIVE, "El barbero está inactivo")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Se requiere datetime con zona horaria")
    today = now.astimezone(TZ).date()
    if day < today:
        return _empty_result(day, barber_id, service_id, PAST_DATE)
    if (day - today).days > MAX_DAYS_AHEAD:
        return _empty_result(day, barber_id, service_id, TOO_FAR_AHEAD)
    if not is_open_day(day):
        return _empty_result(day, barber_id, service_id, "CLOSED")

    bookings = confirmed_bookings_for_day(db, barber_id, day)
    slots: list[str] = []
    start = datetime.combine(day, OPENING_TIME, TZ)
    while True:
        end = compute_end(start, service.duration_min)
        if not is_within_business_hours(start, end):
            break
        if day == today and check_booking_window(start, now) is not None:
            start += timedelta(minutes=SLOT_MINUTES)
            continue
        if not any(
            overlaps(start, end, booking.start_at, booking.end_at)
            for booking in bookings
        ):
            slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=SLOT_MINUTES)

    return {
        "date": day,
        "barber_id": barber_id,
        "service_id": service_id,
        "slots": slots,
        "reason": None,
    }
