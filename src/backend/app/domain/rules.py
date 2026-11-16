"""Reglas de negocio puras (sin BD ni HTTP). Ver specs/business-rules.md."""

import re
import secrets
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.errors import PAST_DATE, TOO_FAR_AHEAD, VALIDATION_ERROR, DomainError

# BR-11 · zona horaria del negocio
TZ = ZoneInfo("America/Panama")

# BR-02 · martes (1) a sábado (5), 09:00–19:00
OPEN_WEEKDAYS = frozenset({1, 2, 3, 4, 5})
OPENING_TIME = time(9, 0)
CLOSING_TIME = time(19, 0)

# BR-04 · grilla de inicio
SLOT_MINUTES = 15

# BR-05 · anticipación máxima
MAX_DAYS_AHEAD = 14

# BR-06 · se puede cancelar con 2 h o más de anticipación (D8: 2 h exactas sí)
CANCEL_MIN_NOTICE = timedelta(hours=2)

# BR-12 · limpieza de 10 min tras cada cita del mismo barbero (CR-01)
CLEANUP_BUFFER = timedelta(minutes=10)

# BR-09 · datos del cliente
# Se usa [0-9] y no \d a propósito: en Python \d acepta dígitos Unicode (p. ej. "٦١٢٣").
_PHONE_RE = re.compile(r"^6[0-9]{3}-?[0-9]{4}$")
NAME_MIN, NAME_MAX = 2, 60

# BR-10 · sin caracteres ambiguos (I, O, 0, 1)
BOOKING_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _local(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Se requiere datetime con zona horaria (BR-11)")
    return dt.astimezone(TZ)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """BR-01 · intervalos semiabiertos [inicio, fin): las citas pegadas no chocan."""
    for dt in (a_start, a_end, b_start, b_end):
        _local(dt)
    return a_start < b_end and a_end > b_start


def compute_end(start: datetime, duration_min: int) -> datetime:
    """BR-03 · fin = inicio + duración del servicio."""
    _local(start)
    if duration_min <= 0:
        raise ValueError("La duración debe ser positiva")
    return start + timedelta(minutes=duration_min)


def blocked_until(end: datetime) -> datetime:
    """BR-12 · fin del bloqueo del barbero: fin real + limpieza (10 min).

    El fin real (`end_at`) sigue siendo el que devuelve la API; este valor solo
    se usa para detectar choques y lo persiste la BD en `blocked_until`.
    """
    return _local(end) + CLEANUP_BUFFER


def is_open_day(day: date) -> bool:
    """BR-02 · domingo y lunes cerrado."""
    return day.weekday() in OPEN_WEEKDAYS


def is_within_business_hours(start: datetime, end: datetime) -> bool:
    """BR-02 · la cita empieza y termina dentro del horario de un día abierto.

    Precondición verificada: end > start.
    """
    start_l, end_l = _local(start), _local(end)
    if end_l <= start_l:
        return False
    if not is_open_day(start_l.date()):
        return False
    opening = datetime.combine(start_l.date(), OPENING_TIME, TZ)
    closing = datetime.combine(start_l.date(), CLOSING_TIME, TZ)
    return opening <= start_l and end_l <= closing


def is_on_grid(start: datetime) -> bool:
    """BR-04 · inicio en múltiplos de 15 minutos exactos."""
    s = _local(start)
    return s.minute % SLOT_MINUTES == 0 and s.second == 0 and s.microsecond == 0


def check_booking_window(start: datetime, now: datetime) -> str | None:
    """BR-05 · None si es válido; si no, el código de error."""
    start_l, now_l = _local(start), _local(now)
    if start_l < now_l:
        return PAST_DATE
    if (start_l.date() - now_l.date()).days > MAX_DAYS_AHEAD:
        return TOO_FAR_AHEAD
    return None


def normalize_phone(phone: str) -> str:
    """BR-09 · teléfono de Panamá 6XXX-XXXX (guion opcional) → 8 dígitos."""
    value = (phone or "").strip()
    if not _PHONE_RE.fullmatch(value):
        raise DomainError(
            VALIDATION_ERROR,
            "Teléfono inválido: use 8 dígitos que empiecen por 6 (6XXX-XXXX)",
            field="client_phone",
        )
    return value.replace("-", "")


def validate_name(name: str) -> str:
    """BR-09 · nombre de 2 a 60 caracteres (sin espacios extremos)."""
    value = (name or "").strip()
    if not NAME_MIN <= len(value) <= NAME_MAX:
        raise DomainError(
            VALIDATION_ERROR,
            f"El nombre debe tener entre {NAME_MIN} y {NAME_MAX} caracteres",
            field="client_name",
        )
    return value


def generate_booking_code() -> str:
    """BR-10 · código criptográficamente aleatorio de 6 caracteres."""
    return "".join(secrets.choice(BOOKING_CODE_ALPHABET) for _ in range(6))


def can_cancel(start: datetime, now: datetime) -> bool:
    """BR-06 · True si faltan 2 horas o más para el inicio (2 h exactas: sí)."""
    return _local(start) - _local(now) >= CANCEL_MIN_NOTICE


def normalize_booking_code(code: str) -> str:
    """BR-10 · el código no distingue mayúsculas: se normaliza a mayúsculas."""
    return (code or "").strip().upper()
