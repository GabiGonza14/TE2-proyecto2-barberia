"""RNF-06: no se registran teléfonos completos en logs.

El access log de uvicorn imprime la URL con su query string, así que
`GET /api/v1/bookings/{code}?phone=...` (RF-10) dejaba el teléfono completo.
"""

import logging

import pytest

from app.core.logging import PhoneMaskingFilter, mask_phone_in_text


def _access_record(path: str) -> logging.LogRecord:
    # Mismo formato y args que usa uvicorn.access (uvicorn/protocols/http).
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:5000", "GET", path, "1.1", 404),
        exc_info=None,
    )


@pytest.mark.parametrize(
    "raw",
    [
        "6123-4567",
        "61234567",
        "6123%2D4567",
        "%2B50761234567",
        "%2B507+6123-4567",  # espacio codificado como en un form
    ],
)
def test_access_log_masks_phone(raw: str) -> None:
    record = _access_record(f"/api/v1/bookings/ABCDEF?phone={raw}")

    assert PhoneMaskingFilter().filter(record) is True
    message = record.getMessage()

    assert "phone=***4567" in message
    assert "6123" not in message
    assert "ABCDEF" in message  # el resto del log se conserva


def test_access_log_masks_phone_among_other_params() -> None:
    record = _access_record("/api/v1/bookings/ABCDEF?x=1&phone=6123-4567&y=2")

    PhoneMaskingFilter().filter(record)

    assert record.getMessage().endswith(
        '"GET /api/v1/bookings/ABCDEF?x=1&phone=***4567&y=2 HTTP/1.1" 404'
    )


def test_log_without_phone_is_unchanged() -> None:
    record = _access_record("/api/v1/availability?barber_id=1&date=2026-11-20")
    before = record.getMessage()

    PhoneMaskingFilter().filter(record)

    assert record.getMessage() == before


def test_mask_short_or_empty_phone() -> None:
    assert mask_phone_in_text("?phone=") == "?phone="
    assert mask_phone_in_text("?phone=12") == "?phone=***"


def test_uvicorn_access_logger_has_phone_filter() -> None:
    import app.main  # noqa: F401  (instala el filtro al importar la app)

    access_logger = logging.getLogger("uvicorn.access")
    assert any(isinstance(f, PhoneMaskingFilter) for f in access_logger.filters)
