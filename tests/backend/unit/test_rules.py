"""Tests unitarios de las reglas de dominio (T3 · issue #3).

Trazabilidad: BR-01, BR-02, BR-03, BR-04, BR-05, BR-09, BR-11
(specs/business-rules.md). Fecha base: martes 2026-12-01, America/Panama.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.core.errors import (
    PAST_DATE,
    TOO_FAR_AHEAD,
    VALIDATION_ERROR,
    DomainError,
)
from app.domain.rules import (
    TZ,
    check_booking_window,
    compute_end,
    is_on_grid,
    is_within_business_hours,
    normalize_phone,
    overlaps,
    validate_name,
)

PANAMA = ZoneInfo("America/Panama")


def at(day: int, hour: int, minute: int = 0, month: int = 12) -> datetime:
    """Fecha-hora local de Panamá en 2026."""
    return datetime(2026, month, day, hour, minute, tzinfo=PANAMA)


# ---------------------------------------------------------------- BR-11
def test_timezone_is_panama() -> None:
    assert TZ == PANAMA


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError):
        is_on_grid(datetime(2026, 12, 1, 10, 0))


# ---------------------------------------------------------------- BR-01
@pytest.mark.parametrize(
    "a, b",
    [
        ((at(1, 10), at(1, 10, 30)), (at(1, 10), at(1, 10, 30))),  # idénticas
        ((at(1, 10), at(1, 10, 45)), (at(1, 10, 30), at(1, 11))),  # parcial (AC-03)
        ((at(1, 10), at(1, 11)), (at(1, 10, 15), at(1, 10, 45))),  # contenida
        ((at(1, 10, 15), at(1, 10, 45)), (at(1, 10), at(1, 11))),  # contiene
    ],
)
def test_overlaps_true(a: tuple, b: tuple) -> None:
    assert overlaps(*a, *b) is True
    assert overlaps(*b, *a) is True


@pytest.mark.parametrize(
    "a, b",
    [
        ((at(1, 10), at(1, 10, 30)), (at(1, 10, 30), at(1, 11))),  # pegadas (AC-04)
        ((at(1, 9), at(1, 9, 30)), (at(1, 11), at(1, 11, 30))),  # separadas
    ],
)
def test_overlaps_false(a: tuple, b: tuple) -> None:
    assert overlaps(*a, *b) is False
    assert overlaps(*b, *a) is False


def test_overlaps_compares_instants_across_timezones() -> None:
    # 15:00 UTC == 10:00 Panamá
    utc_start = datetime(2026, 12, 1, 15, 0, tzinfo=timezone.utc)
    assert overlaps(utc_start, utc_start + timedelta(minutes=30), at(1, 10, 15), at(1, 10, 45))


# ---------------------------------------------------------------- BR-03
@pytest.mark.parametrize("minutes, end", [(30, (10, 30)), (20, (10, 20)), (45, (10, 45)), (40, (10, 40))])
def test_compute_end_uses_service_duration(minutes: int, end: tuple[int, int]) -> None:
    assert compute_end(at(1, 10), minutes) == at(1, *end)


@pytest.mark.parametrize("minutes", [0, -10])
def test_compute_end_rejects_non_positive_duration(minutes: int) -> None:
    with pytest.raises(ValueError):
        compute_end(at(1, 10), minutes)


# ---------------------------------------------------------------- BR-02
@pytest.mark.parametrize(
    "start, minutes",
    [
        (at(1, 9), 30),  # martes, apertura
        (at(1, 18, 30), 30),  # termina justo 19:00
        (at(5, 12), 45),  # sábado
    ],
)
def test_within_business_hours(start: datetime, minutes: int) -> None:
    assert is_within_business_hours(start, compute_end(start, minutes)) is True


@pytest.mark.parametrize(
    "start, minutes",
    [
        (at(30, 10, month=11), 30),  # lunes 30-nov: cerrado
        (at(6, 10), 30),  # domingo: cerrado
        (at(1, 8, 45), 30),  # antes de abrir
        (at(1, 18, 30), 45),  # Corte+Barba 18:30 → 19:15 (AC-07)
        (at(1, 19), 20),  # empieza al cierre
    ],
)
def test_outside_business_hours(start: datetime, minutes: int) -> None:
    assert is_within_business_hours(start, compute_end(start, minutes)) is False


def test_business_hours_evaluated_in_panama_time() -> None:
    # 14:00 UTC == 09:00 Panamá (dentro); 13:45 UTC == 08:45 Panamá (fuera)
    ok = datetime(2026, 12, 1, 14, 0, tzinfo=timezone.utc)
    early = datetime(2026, 12, 1, 13, 45, tzinfo=timezone.utc)
    assert is_within_business_hours(ok, ok + timedelta(minutes=30)) is True
    assert is_within_business_hours(early, early + timedelta(minutes=30)) is False


# ---------------------------------------------------------------- BR-04
@pytest.mark.parametrize("minute", [0, 15, 30, 45])
def test_on_grid(minute: int) -> None:
    assert is_on_grid(at(1, 10, minute)) is True


@pytest.mark.parametrize("start", [at(1, 10, 10), at(1, 10, 1), at(1, 10).replace(second=30)])
def test_start_not_on_grid(start: datetime) -> None:
    assert is_on_grid(start) is False


# ---------------------------------------------------------------- BR-05
NOW = at(1, 12)  # martes 2026-12-01 12:00


def test_booking_window_ok_same_day_and_limit() -> None:
    assert check_booking_window(at(1, 15), NOW) is None
    assert check_booking_window(at(15, 18), NOW) is None  # día 14


def test_booking_window_past() -> None:
    assert check_booking_window(at(1, 11), NOW) == PAST_DATE
    assert check_booking_window(at(30, 10, month=11), NOW) == PAST_DATE  # ayer


def test_booking_window_too_far_ahead() -> None:
    assert check_booking_window(at(16, 9), NOW) == TOO_FAR_AHEAD  # día 15


# ---------------------------------------------------------------- BR-09
@pytest.mark.parametrize("raw", ["6123-4567", "61234567", " 6123-4567 "])
def test_normalize_phone_valid(raw: str) -> None:
    assert normalize_phone(raw) == "61234567"


@pytest.mark.parametrize("raw", ["1234", "5123-4567", "6123-456", "612345678", "6abc-defg", ""])
def test_normalize_phone_invalid(raw: str) -> None:
    with pytest.raises(DomainError) as exc:
        normalize_phone(raw)
    assert exc.value.code == VALIDATION_ERROR
    assert exc.value.field == "client_phone"


@pytest.mark.parametrize("raw, expected", [("Ana Pérez", "Ana Pérez"), ("  Al  ", "Al"), ("x" * 60, "x" * 60)])
def test_validate_name_valid(raw: str, expected: str) -> None:
    assert validate_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "A", "x" * 61])
def test_validate_name_invalid(raw: str) -> None:
    with pytest.raises(DomainError) as exc:
        validate_name(raw)
    assert exc.value.code == VALIDATION_ERROR
    assert exc.value.field == "client_name"
