"""T8 · Consultar y cancelar reserva (issue #16).

Trazabilidad: O5 → RF-10, RF-11, RF-12 → BR-06, BR-07, BR-09, BR-10
→ AC-13, AC-14, AC-15, AC-18, AC-19, AC-20 (decisiones D8 / PR #18).
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.clock import get_now
from app.domain.rules import TZ
from app.main import app

BOOKING_START = datetime(2026, 12, 1, 10, 0, tzinfo=TZ)
PHONE = "6123-4567"

clock: dict[str, datetime] = {}


@pytest.fixture(autouse=True)
def fixed_clock(clean_bookings) -> None:
    clock["now"] = BOOKING_START - timedelta(hours=3)  # 07:00
    app.dependency_overrides[get_now] = lambda: clock["now"]
    yield
    app.dependency_overrides.pop(get_now, None)


async def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(method, url, **kwargs)


def call(method: str, url: str, **kwargs: Any) -> httpx.Response:
    return asyncio.run(_request(method, url, **kwargs))


def _ids(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT 'barber_' || name AS key, id FROM barbers "
                "UNION ALL SELECT 'service_' || name AS key, id FROM services"
            )
        )
    return {row.key: row.id for row in rows}


def book(engine: Engine, start: datetime = BOOKING_START, name: str = "Ana Pérez") -> dict:
    ids = _ids(engine)
    response = call(
        "POST",
        "/api/v1/bookings",
        json={
            "barber_id": ids["barber_Carlos"],
            "service_id": ids["service_Corte"],
            "start_at": start.isoformat(),
            "client_name": name,
            "client_phone": PHONE,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def cancel(code: str, phone: str = PHONE) -> httpx.Response:
    return call("POST", f"/api/v1/bookings/{code}/cancel", json={"phone": phone})


def lookup(code: str, phone: str = PHONE) -> httpx.Response:
    return call("GET", f"/api/v1/bookings/{code}", params={"phone": phone})


def db_row(engine: Engine, code: str):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT status, cancelled_at FROM bookings WHERE code = :code"),
            {"code": code},
        ).one()


def error_code(response: httpx.Response) -> str:
    return response.json()["error"]["code"]


# ------------------------------------------------------------- Consultar
def test_lookup_returns_booking(engine: Engine) -> None:
    """RF-10: código + teléfono correctos → misma forma que el 201."""
    created = book(engine)

    for phone in ("6123-4567", "61234567"):
        response = lookup(created["code"], phone)
        assert response.status_code == 200
        assert response.json() == created


def test_lookup_code_case_insensitive(engine: Engine) -> None:
    """AC-20 · BR-10: el código no distingue mayúsculas."""
    created = book(engine)

    response = lookup(created["code"].lower())

    assert response.status_code == 200
    assert response.json()["code"] == created["code"]


def test_lookup_requires_phone(engine: Engine) -> None:
    """AC-15 · BR-10: código correcto + teléfono incorrecto → 404."""
    created = book(engine)

    response = lookup(created["code"], "6999-9999")

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


def test_lookup_unknown_code_same_message_as_wrong_phone(engine: Engine) -> None:
    """No revela qué códigos existen: mismo 404 y mismo mensaje."""
    created = book(engine)

    wrong_phone = lookup(created["code"], "6999-9999")
    unknown_code = lookup("ZZZZZZ")

    assert unknown_code.status_code == wrong_phone.status_code == 404
    assert unknown_code.json() == wrong_phone.json()


def test_lookup_invalid_phone_format(engine: Engine) -> None:
    """BR-09: un teléfono con formato inválido → 422 con field=phone."""
    created = book(engine)

    response = lookup(created["code"], "1234")

    assert response.status_code == 422
    assert error_code(response) == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["field"] == "phone"


# -------------------------------------------------------------- Cancelar
def test_cancel_frees_slot(engine: Engine) -> None:
    """AC-13 · BR-07: cancelar con 3 h de anticipación libera el horario."""
    created = book(engine)

    response = cancel(created["code"])

    assert response.status_code == 200
    assert response.json() == {"code": created["code"], "status": "CANCELADA"}
    status, cancelled_at = db_row(engine, created["code"])
    assert status == "CANCELADA"
    assert cancelled_at == clock["now"]

    ids = _ids(engine)
    availability = call(
        "GET",
        "/api/v1/availability",
        params={
            "barber_id": ids["barber_Carlos"],
            "service_id": ids["service_Corte"],
            "date": "2026-12-01",
        },
    )
    assert "10:00" in availability.json()["slots"]

    other = book(engine, name="Luis Gómez")  # otro cliente toma el mismo horario
    assert other["start_at"] == created["start_at"]


def test_cancel_window_closed(engine: Engine) -> None:
    """AC-14 · BR-06: faltan 90 min → 409 y la reserva sigue confirmada."""
    clock["now"] = BOOKING_START - timedelta(minutes=90)
    created = book(engine)

    response = cancel(created["code"])

    assert response.status_code == 409
    assert error_code(response) == "CANCEL_WINDOW_CLOSED"
    assert db_row(engine, created["code"]).status == "CONFIRMADA"


def test_cancel_exactly_two_hours_before(engine: Engine) -> None:
    """AC-18 · BR-06 (D8): exactamente 2 h antes sí se puede cancelar."""
    clock["now"] = BOOKING_START - timedelta(hours=2)
    created = book(engine)

    response = cancel(created["code"])

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELADA"


def test_cancel_one_minute_inside_window_is_rejected(engine: Engine) -> None:
    """BR-06: con 1 h 59 min ya no se puede."""
    clock["now"] = BOOKING_START - timedelta(hours=2) + timedelta(minutes=1)
    created = book(engine)

    response = cancel(created["code"])

    assert response.status_code == 409
    assert error_code(response) == "CANCEL_WINDOW_CLOSED"


def test_cancel_already_cancelled(engine: Engine) -> None:
    """AC-19 (D8): cancelar dos veces → 409 ALREADY_CANCELLED."""
    created = book(engine)
    assert cancel(created["code"]).status_code == 200

    response = cancel(created["code"])

    assert response.status_code == 409
    assert error_code(response) == "ALREADY_CANCELLED"


def test_cancel_wrong_phone_does_not_cancel(engine: Engine) -> None:
    """BR-10: sin el teléfono correcto no se cancela nada."""
    created = book(engine)

    response = cancel(created["code"], "6999-9999")

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"
    assert db_row(engine, created["code"]).status == "CONFIRMADA"


def test_cancel_code_case_insensitive(engine: Engine) -> None:
    """BR-10: también al cancelar el código no distingue mayúsculas."""
    created = book(engine)

    response = cancel(created["code"].lower())

    assert response.status_code == 200
    assert response.json()["code"] == created["code"]


def test_cancel_missing_phone(engine: Engine) -> None:
    """Sin teléfono en el cuerpo → 422 con el formato común."""
    created = book(engine)

    response = call("POST", f"/api/v1/bookings/{created['code']}/cancel", json={})

    assert response.status_code == 422
    assert error_code(response) == "VALIDATION_ERROR"
