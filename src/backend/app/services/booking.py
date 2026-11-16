import secrets
from dataclasses import dataclass
from datetime import datetime

from psycopg.errors import (
    DeadlockDetected,
    ExclusionViolation,
    SerializationFailure,
    UniqueViolation,
)
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.errors import (
    ALREADY_CANCELLED,
    BARBER_INACTIVE,
    CANCEL_WINDOW_CLOSED,
    INVALID_START_TIME,
    NOT_FOUND,
    OUTSIDE_BUSINESS_HOURS,
    PAST_DATE,
    SLOT_TAKEN,
    TOO_FAR_AHEAD,
    VALIDATION_ERROR,
    DomainError,
)
from app.domain import rules
from app.models.booking import STATUS_CANCELLED, STATUS_CONFIRMED, Booking
from app.repositories import bookings as bookings_repository
from app.repositories.catalog import get_barber, get_service
from app.schemas.bookings import BookingCreate, BookingOut, CancelOut

MAX_CODE_ATTEMPTS = 5
SLOT_TAKEN_MESSAGE = "El barbero ya tiene una cita en ese horario"
# BR-10: el mismo mensaje si el código no existe o el teléfono no coincide,
# para no revelar qué códigos existen.
BOOKING_NOT_FOUND_MESSAGE = "No encontramos una reserva con ese código y teléfono"

# Dos INSERT simultáneos que chocan en no_double_booking pueden terminar en
# deadlock (cada uno espera al otro) en lugar de ExclusionViolation.
# Se reintenta UNA vez: en el reintento la capa 1 ya ve al ganador → 409.
# Ver docs/decisions.md (D7) y tests/backend/integration/test_concurrency.py.
RACE_ERRORS = (DeadlockDetected, SerializationFailure)
MAX_RACE_ATTEMPTS = 2


@dataclass(frozen=True)
class _ValidatedBooking:
    client_name: str
    client_phone: str
    start: datetime
    end: datetime
    barber_name: str
    service_name: str


def _window_message(code: str) -> str:
    if code == PAST_DATE:
        return "No se puede reservar en el pasado"
    if code == TOO_FAR_AHEAD:
        return "Solo se puede reservar hasta con 14 días de anticipación"
    return "La fecha de reserva no es válida"


def _is_code_collision(exc: IntegrityError) -> bool:
    constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    return isinstance(exc.orig, UniqueViolation) and constraint == (
        "uq_bookings_code"
    )


def _validate_booking(
    db: Session, data: BookingCreate, now: datetime
) -> _ValidatedBooking:
    client_name = rules.validate_name(data.client_name)
    client_phone = rules.normalize_phone(data.client_phone)

    if data.start_at.tzinfo is None or data.start_at.utcoffset() is None:
        raise DomainError(
            VALIDATION_ERROR,
            "La fecha y hora debe incluir zona horaria",
            field="start_at",
        )
    start = data.start_at.astimezone(rules.TZ)

    service = get_service(db, data.service_id)
    if service is None:
        raise DomainError(NOT_FOUND, "Servicio no encontrado")
    barber = get_barber(db, data.barber_id)
    if barber is None:
        raise DomainError(NOT_FOUND, "Barbero no encontrado")
    if not barber.active:
        raise DomainError(BARBER_INACTIVE, "El barbero está inactivo")

    if not rules.is_on_grid(start):
        raise DomainError(
            INVALID_START_TIME,
            "La hora de inicio debe estar en la grilla de 15 minutos",
            field="start_at",
        )

    window_error = rules.check_booking_window(start, now)
    if window_error is not None:
        raise DomainError(window_error, _window_message(window_error))

    end = rules.compute_end(start, service.duration_min)
    if not rules.is_within_business_hours(start, end):
        raise DomainError(
            OUTSIDE_BUSINESS_HOURS,
            "La reserva está fuera del horario laboral",
            field="start_at",
        )

    if bookings_repository.find_overlapping(
        db, data.barber_id, start, end
    ):
        raise DomainError(
            SLOT_TAKEN, SLOT_TAKEN_MESSAGE
        )

    return _ValidatedBooking(
        client_name=client_name,
        client_phone=client_phone,
        start=start,
        end=end,
        barber_name=barber.name,
        service_name=service.name,
    )


def _persist_booking(
    db: Session, data: BookingCreate, validated: _ValidatedBooking
) -> str:
    for attempt in range(MAX_CODE_ATTEMPTS):
        code = rules.generate_booking_code()
        try:
            bookings_repository.add_booking(
                db,
                code=code,
                barber_id=data.barber_id,
                service_id=data.service_id,
                client_name=validated.client_name,
                client_phone=validated.client_phone,
                start_at=validated.start,
                end_at=validated.end,
            )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            if isinstance(exc.orig, ExclusionViolation):
                raise DomainError(
                    SLOT_TAKEN,
                    SLOT_TAKEN_MESSAGE,
                ) from exc
            if _is_code_collision(exc) and attempt < MAX_CODE_ATTEMPTS - 1:
                continue
            raise

        return code

    raise RuntimeError("No se pudo generar un código de reserva")


def _book_once(
    db: Session, data: BookingCreate, now: datetime
) -> tuple[_ValidatedBooking, str]:
    validated = _validate_booking(db, data, now)
    return validated, _persist_booking(db, data, validated)


def create_booking(
    db: Session, data: BookingCreate, now: datetime
) -> BookingOut:
    for attempt in range(MAX_RACE_ATTEMPTS):
        try:
            validated, code = _book_once(db, data, now)
            break
        except OperationalError as exc:
            if not isinstance(exc.orig, RACE_ERRORS):
                raise
            db.rollback()
            if attempt == MAX_RACE_ATTEMPTS - 1:
                raise DomainError(
                    SLOT_TAKEN,
                    SLOT_TAKEN_MESSAGE,
                ) from exc
    return BookingOut(
        code=code,
        status=STATUS_CONFIRMED,
        barber=validated.barber_name,
        service=validated.service_name,
        start_at=validated.start,
        end_at=validated.end,
    )



# ------------------------------------------------- T8 · consultar y cancelar
def _phone_param(phone: str) -> str:
    """BR-09 sobre el parámetro `phone` (consultar / cancelar)."""
    try:
        return rules.normalize_phone(phone)
    except DomainError as exc:
        raise DomainError(exc.code, exc.message, field="phone") from exc


def _find_owned_booking(
    db: Session, code: str, phone: str, *, for_update: bool = False
) -> Booking:
    """BR-10 · código (sin distinguir mayúsculas) + teléfono. Si el código no
    existe o el teléfono no coincide → el mismo 404."""
    normalized_phone = _phone_param(phone)
    booking = bookings_repository.get_by_code(
        db, rules.normalize_booking_code(code), for_update=for_update
    )
    if booking is None or not secrets.compare_digest(
        booking.client_phone, normalized_phone
    ):
        raise DomainError(NOT_FOUND, BOOKING_NOT_FOUND_MESSAGE)
    return booking


def _to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        code=booking.code,
        status=booking.status,
        barber=booking.barber.name,
        service=booking.service.name,
        start_at=booking.start_at.astimezone(rules.TZ),
        end_at=booking.end_at.astimezone(rules.TZ),
    )


def get_booking(db: Session, code: str, phone: str) -> BookingOut:
    """RF-10 · consultar una reserva con código + teléfono."""
    return _to_out(_find_owned_booking(db, code, phone))


def cancel_booking(db: Session, code: str, phone: str, now: datetime) -> CancelOut:
    """RF-11/RF-12 · cancelar con 2 h o más de anticipación (BR-06). La
    reserva CANCELADA deja de contar para no_double_booking (BR-07)."""
    try:
        booking = _find_owned_booking(db, code, phone, for_update=True)
        if booking.status == STATUS_CANCELLED:
            raise DomainError(ALREADY_CANCELLED, "La reserva ya estaba cancelada")
        if not rules.can_cancel(booking.start_at, now):
            raise DomainError(
                CANCEL_WINDOW_CLOSED,
                "Solo se puede cancelar con 2 horas o más de anticipación",
            )
        booking.status = STATUS_CANCELLED
        booking.cancelled_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise
    return CancelOut(code=booking.code, status=booking.status)
