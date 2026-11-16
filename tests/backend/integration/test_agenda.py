"""T9 · Agenda del día para el admin (issue #17).

Trazabilidad: O4 → RF-13, RF-14 → AC-16, AC-17, AC-21, AC-22 (decisiones D8 / PR #18).
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

ADMIN_KEY = "test-admin-key"
AUTH = {"X-Admin-Key": ADMIN_KEY}
DAY = "2026-12-01"
URL = "/api/v1/admin/agenda"


@pytest.fixture(autouse=True)
def setup(clean_bookings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)
    app.dependency_overrides[get_now] = lambda: datetime(2026, 12, 1, 8, 0, tzinfo=TZ)
    yield
    app.dependency_overrides.pop(get_now, None)


async def _get(params: dict[str, Any] | None, headers: dict[str, str] | None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.get(URL, params=params, headers=headers)


def agenda(params: dict[str, Any] | None = None, headers: dict[str, str] | None = AUTH):
    return asyncio.run(_get(params, headers))


def _ids(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT 'barber_' || name AS key, id FROM barbers "
                "UNION ALL SELECT 'service_' || name AS key, id FROM services"
            )
        )
    return {row.key: row.id for row in rows}


def insert(
    engine: Engine,
    code: str,
    barber: str,
    service: str,
    start: datetime,
    minutes: int,
    *,
    client: str = "Ana Pérez",
    status: str = "CONFIRMADA",
) -> None:
    ids = _ids(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO bookings (code, barber_id, service_id, client_name,"
                " client_phone, start_at, end_at, status) VALUES (:code, :b, :s,"
                " :client, '61234567', :start, :end, :status)"
            ),
            {
                "code": code,
                "b": ids[f"barber_{barber}"],
                "s": ids[f"service_{service}"],
                "client": client,
                "start": start,
                "end": start + timedelta(minutes=minutes),
                "status": status,
            },
        )


def set_active(engine: Engine, barber: str, active: bool) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE barbers SET active = :a WHERE name = :n"),
            {"a": active, "n": barber},
        )


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 12, day, hour, minute, tzinfo=TZ)


def by_barber(body: dict) -> dict[str, list[dict]]:
    return {b["barber"]: b["bookings"] for b in body["barbers"]}


# ----------------------------------------------------------------- AC-16
def test_agenda_of_day(engine: Engine) -> None:
    """AC-16: reservas del día ordenadas por hora y agrupadas por barbero,
    sin las canceladas ni las de otros días."""
    insert(engine, "CAR100", "Carlos", "Corte", at(1, 10), 30, client="Ana Pérez")
    insert(engine, "CAR090", "Carlos", "Barba", at(1, 9), 20, client="Beto Ruiz")
    insert(engine, "LUI110", "Luis", "Corte+Barba", at(1, 11), 45, client="Carla Díaz")
    insert(engine, "CAN120", "Carlos", "Corte", at(1, 12), 30, status="CANCELADA")
    insert(engine, "AYE180", "Carlos", "Corte", datetime(2026, 11, 30, 18, 0, tzinfo=TZ), 30)
    insert(engine, "MAN090", "Luis", "Corte", at(2, 9), 30)

    response = agenda({"date": DAY})

    assert response.status_code == 200
    body = response.json()
    assert body["date"] == DAY
    grouped = by_barber(body)
    assert grouped["Carlos"] == [
        {"start": "09:00", "end": "09:20", "service": "Barba", "client": "Beto Ruiz", "code": "CAR090"},
        {"start": "10:00", "end": "10:30", "service": "Corte", "client": "Ana Pérez", "code": "CAR100"},
    ]
    assert grouped["Luis"] == [
        {"start": "11:00", "end": "11:45", "service": "Corte+Barba", "client": "Carla Díaz", "code": "LUI110"},
    ]


def test_agenda_does_not_expose_phone(engine: Engine) -> None:
    """Privacidad (D8): la agenda nunca incluye el teléfono del cliente."""
    insert(engine, "CAR100", "Carlos", "Corte", at(1, 10), 30)

    response = agenda({"date": DAY})

    assert "phone" not in response.text
    assert "61234567" not in response.text


# ----------------------------------------------------------------- AC-17
def test_agenda_requires_admin() -> None:
    """AC-17 · RF-14: sin X-Admin-Key → 401 UNAUTHORIZED con formato común."""
    response = agenda({"date": DAY}, headers=None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_agenda_wrong_key() -> None:
    response = agenda({"date": DAY}, headers={"X-Admin-Key": "otra-clave"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_agenda_admin_key_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si ADMIN_KEY no está configurada, nadie entra (ni con clave vacía)."""
    monkeypatch.delenv("ADMIN_KEY", raising=False)

    assert agenda({"date": DAY}, headers={"X-Admin-Key": ""}).status_code == 401
    assert agenda({"date": DAY}).status_code == 401


def test_agenda_auth_checked_before_validation() -> None:
    """Sin clave no se revela nada, ni siquiera errores de validación."""
    response = agenda({"date": "no-es-fecha"}, headers=None)

    assert response.status_code == 401


# ----------------------------------------------------------------- AC-21
def test_agenda_lists_barbers_without_bookings(engine: Engine) -> None:
    """AC-21 (D8): todo barbero activo aparece, aunque no tenga citas."""
    insert(engine, "CAR100", "Carlos", "Corte", at(1, 10), 30)

    grouped = by_barber(agenda({"date": DAY}).json())

    assert set(grouped) == {"Carlos", "Luis", "Andrés"}
    assert grouped["Luis"] == []
    assert grouped["Andrés"] == []


def test_agenda_barbers_in_stable_order() -> None:
    names = [b["barber"] for b in agenda({"date": DAY}).json()["barbers"]]
    assert names == ["Carlos", "Luis", "Andrés"]


def test_inactive_barber_only_with_bookings(engine: Engine) -> None:
    """D8: un barbero inactivo aparece solo si tiene reservas CONFIRMADA ese día."""
    set_active(engine, "Andrés", False)
    try:
        assert "Andrés" not in by_barber(agenda({"date": DAY}).json())

        insert(engine, "AND100", "Andrés", "Corte", at(1, 10), 30)
        grouped = by_barber(agenda({"date": DAY}).json())
        assert [b["code"] for b in grouped["Andrés"]] == ["AND100"]
    finally:
        set_active(engine, "Andrés", True)


# ----------------------------------------------------------------- AC-22
def test_agenda_defaults_to_today(engine: Engine) -> None:
    """AC-22 (D8): sin `date` se usa hoy (America/Panama, según get_now)."""
    insert(engine, "HOY100", "Carlos", "Corte", at(1, 10), 30)
    insert(engine, "MAN100", "Carlos", "Corte", at(2, 10), 30)

    body = agenda().json()

    assert body["date"] == DAY
    assert [b["code"] for b in by_barber(body)["Carlos"]] == ["HOY100"]


# --------------------------------------------------------------- Filtros
def test_agenda_filter_by_barber(engine: Engine) -> None:
    insert(engine, "CAR100", "Carlos", "Corte", at(1, 10), 30)
    insert(engine, "LUI100", "Luis", "Corte", at(1, 10), 30)
    luis = _ids(engine)["barber_Luis"]

    body = agenda({"date": DAY, "barber_id": luis}).json()

    assert [b["barber"] for b in body["barbers"]] == ["Luis"]
    assert [b["code"] for b in body["barbers"][0]["bookings"]] == ["LUI100"]


def test_agenda_unknown_barber() -> None:
    response = agenda({"date": DAY, "barber_id": 999})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_agenda_invalid_date() -> None:
    response = agenda({"date": "2026-13-45"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["field"] == "date"
