import asyncio
from datetime import datetime

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.clock import get_now
from app.domain.rules import TZ
from app.main import app

FIXED_NOW = datetime(2026, 12, 1, 8, 0, tzinfo=TZ)


@pytest.fixture(autouse=True)
def fixed_clock(clean_bookings) -> None:
    app.dependency_overrides[get_now] = lambda: FIXED_NOW
    yield
    app.dependency_overrides.pop(get_now, None)


async def get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.get(path)


def catalog_ids(engine: Engine) -> tuple[int, int, int]:
    with engine.connect() as conn:
        carlos_id = conn.execute(
            text("SELECT id FROM barbers WHERE name = 'Carlos'")
        ).scalar_one()
        corte_id = conn.execute(
            text("SELECT id FROM services WHERE name = 'Corte'")
        ).scalar_one()
        combo_id = conn.execute(
            text("SELECT id FROM services WHERE name = 'Corte+Barba'")
        ).scalar_one()
    return carlos_id, corte_id, combo_id


def insert_booking(
    engine: Engine,
    *,
    code: str,
    barber_id: int,
    service_id: int,
    start_at: datetime,
    end_at: datetime,
    status: str = "CONFIRMADA",
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (
                    code, barber_id, service_id, client_name, client_phone,
                    start_at, end_at, status
                ) VALUES (
                    :code, :barber_id, :service_id, 'Cliente Prueba',
                    '60000000', :start_at, :end_at, :status
                )
                """
            ),
            {
                "code": code,
                "barber_id": barber_id,
                "service_id": service_id,
                "start_at": start_at,
                "end_at": end_at,
                "status": status,
            },
        )


def availability_url(barber_id: int, service_id: int, day: str) -> str:
    return (
        "/api/v1/availability"
        f"?barber_id={barber_id}&service_id={service_id}&date={day}"
    )


def test_availability_excludes_taken(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)
    insert_booking(
        engine,
        code="T5A001",
        barber_id=carlos_id,
        service_id=corte_id,
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-01"))
    )

    assert response.status_code == 200
    body = response.json()
    assert body["date"] == "2026-12-01"
    assert body["barber_id"] == carlos_id
    assert body["service_id"] == corte_id
    assert body["reason"] is None
    assert "09:30" in body["slots"]
    assert "09:45" not in body["slots"]
    assert "10:00" not in body["slots"]
    assert "10:15" not in body["slots"]
    assert "10:30" in body["slots"]
    assert body["slots"][-1] == "18:30"


def test_availability_closed_day(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-06"))
    )

    assert response.status_code == 200
    assert response.json()["slots"] == []
    assert response.json()["reason"] == "CLOSED"


def test_last_slot_depends_on_duration(engine: Engine) -> None:
    carlos_id, _, combo_id = catalog_ids(engine)

    response = asyncio.run(
        get(availability_url(carlos_id, combo_id, "2026-12-01"))
    )

    assert response.status_code == 200
    assert response.json()["slots"][-1] == "18:15"


def test_cancelled_booking_does_not_block(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)
    insert_booking(
        engine,
        code="T5A002",
        barber_id=carlos_id,
        service_id=corte_id,
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
        status="CANCELADA",
    )

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-01"))
    )

    assert response.status_code == 200
    assert "10:00" in response.json()["slots"]


def test_today_excludes_past_slots(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)
    app.dependency_overrides[get_now] = lambda: datetime(
        2026, 12, 1, 12, 10, tzinfo=TZ
    )

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-01"))
    )

    assert response.status_code == 200
    assert response.json()["slots"][0] == "12:15"


def test_availability_past_and_too_far(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)

    past_response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-11-30"))
    )
    future_response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-16"))
    )

    assert past_response.status_code == 200
    assert past_response.json()["slots"] == []
    assert past_response.json()["reason"] == "PAST_DATE"
    assert future_response.status_code == 200
    assert future_response.json()["slots"] == []
    assert future_response.json()["reason"] == "TOO_FAR_AHEAD"


def test_availability_inactive_barber(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = false WHERE id = :id"),
                {"id": carlos_id},
            )

        response = asyncio.run(
            get(availability_url(carlos_id, corte_id, "2026-12-01"))
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "BARBER_INACTIVE"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = true WHERE id = :id"),
                {"id": carlos_id},
            )


def test_availability_unknown_service(engine: Engine) -> None:
    carlos_id, _, _ = catalog_ids(engine)

    response = asyncio.run(
        get(availability_url(carlos_id, 999_999, "2026-12-01"))
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_availability_unknown_barber(engine: Engine) -> None:
    _, corte_id, _ = catalog_ids(engine)

    response = asyncio.run(
        get(availability_url(999_999, corte_id, "2026-12-01"))
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_other_barber_booking_does_not_block(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)
    with engine.connect() as conn:
        luis_id = conn.execute(
            text("SELECT id FROM barbers WHERE name = 'Luis'")
        ).scalar_one()
    insert_booking(
        engine,
        code="T5A003",
        barber_id=luis_id,
        service_id=corte_id,
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-01"))
    )

    assert response.status_code == 200
    assert "10:00" in response.json()["slots"]


def test_availability_day_fourteen_is_allowed(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)

    response = asyncio.run(
        get(availability_url(carlos_id, corte_id, "2026-12-15"))
    )

    assert response.status_code == 200
    assert response.json()["reason"] is None
    assert response.json()["slots"]


def test_availability_missing_param_common_format(engine: Engine) -> None:
    carlos_id, corte_id, _ = catalog_ids(engine)

    response = asyncio.run(
        get(
            "/api/v1/availability"
            f"?barber_id={carlos_id}&service_id={corte_id}"
        )
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "Solicitud inválida"
    assert response.json()["error"]["details"] == {"field": "date"}
