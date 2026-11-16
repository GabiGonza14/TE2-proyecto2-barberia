import asyncio
from datetime import datetime
from typing import Any

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


async def post_booking(payload: dict[str, Any]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/bookings", json=payload)


def catalog_ids(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT 'barber_' || name AS key, id FROM barbers
                UNION ALL
                SELECT 'service_' || name AS key, id FROM services
                """
            )
        )
    return {row.key: row.id for row in rows}


def payload(
    ids: dict[str, int],
    *,
    barber: str = "Carlos",
    service: str = "Corte",
    start_at: str = "2026-12-01T10:00:00-05:00",
    client_name: str = "Ana Pérez",
    client_phone: str = "6123-4567",
) -> dict[str, Any]:
    return {
        "barber_id": ids[f"barber_{barber}"],
        "service_id": ids[f"service_{service}"],
        "start_at": start_at,
        "client_name": client_name,
        "client_phone": client_phone,
    }


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
                    :code, :barber_id, :service_id, 'Cliente Existente',
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


def booking_count(engine: Engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()


def test_create_booking_success(engine: Engine) -> None:
    ids = catalog_ids(engine)

    response = asyncio.run(post_booking(payload(ids)))

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "code",
        "status",
        "barber",
        "service",
        "start_at",
        "end_at",
    }
    assert len(body["code"]) == 6
    assert body["status"] == "CONFIRMADA"
    assert body["barber"] == "Carlos"
    assert body["service"] == "Corte"
    assert body["start_at"] == "2026-12-01T10:00:00-05:00"
    assert body["end_at"] == "2026-12-01T10:30:00-05:00"
    with engine.connect() as conn:
        stored = conn.execute(
            text("SELECT client_name, client_phone FROM bookings")
        ).one()
    assert stored.client_name == "Ana Pérez"
    assert stored.client_phone == "61234567"


def test_double_booking_rejected(engine: Engine) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="AAA222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    response = asyncio.run(post_booking(payload(ids)))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"
    assert booking_count(engine) == 1


def test_partial_overlap_rejected(engine: Engine) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="BBB222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte+Barba"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 45, tzinfo=TZ),
    )

    response = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T10:30:00-05:00")
        )
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"
    assert booking_count(engine) == 1


def test_buffer_after_booking(engine: Engine) -> None:
    """AC-04 · BR-12: tras una cita 10:00–10:30, 10:30 choca con la limpieza
    (bloqueado hasta 10:40); 10:45 ya se puede reservar."""
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="CCC222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    adjacent = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T10:30:00-05:00")
        )
    )

    assert adjacent.status_code == 409
    assert adjacent.json()["error"]["code"] == "SLOT_TAKEN"
    assert booking_count(engine) == 1

    later = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T10:45:00-05:00")
        )
    )

    assert later.status_code == 201
    assert booking_count(engine) == 2


def test_buffer_before_existing_booking(engine: Engine) -> None:
    """AC-23 · BR-12: una cita 09:30–10:00 choca con la limpieza de la cita
    existente 10:00–10:30 (bloqueada desde 09:50); 09:15–09:45 sí cabe."""
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="GGG222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    before = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T09:30:00-05:00")
        )
    )

    assert before.status_code == 409
    assert before.json()["error"]["code"] == "SLOT_TAKEN"
    assert booking_count(engine) == 1

    earlier = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T09:15:00-05:00")
        )
    )

    assert earlier.status_code == 201
    assert earlier.json()["end_at"] == "2026-12-01T09:45:00-05:00"
    assert booking_count(engine) == 2


def test_buffer_may_end_after_closing(engine: Engine) -> None:
    """AC-25 · BR-02/BR-12: el Corte 18:30–19:00 es válido aunque la limpieza
    termine 19:10; la limpieza no tiene que caber antes del cierre."""
    ids = catalog_ids(engine)

    response = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T18:30:00-05:00")
        )
    )

    assert response.status_code == 201
    assert response.json()["end_at"] == "2026-12-01T19:00:00-05:00"
    with engine.connect() as conn:
        blocked_until = conn.execute(
            text("SELECT blocked_until FROM bookings")
        ).scalar_one()
    assert blocked_until == datetime(2026, 12, 1, 19, 10, tzinfo=TZ)


def test_same_time_different_barber_allowed(engine: Engine) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="DDD222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )

    response = asyncio.run(post_booking(payload(ids, barber="Luis")))

    assert response.status_code == 201
    assert booking_count(engine) == 2


def test_outside_business_hours(engine: Engine) -> None:
    ids = catalog_ids(engine)

    monday = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-07T10:00:00-05:00")
        )
    )
    after_closing = asyncio.run(
        post_booking(
            payload(
                ids,
                service="Corte+Barba",
                start_at="2026-12-01T18:30:00-05:00",
            )
        )
    )

    assert monday.status_code == 422
    assert monday.json()["error"]["code"] == "OUTSIDE_BUSINESS_HOURS"
    assert after_closing.status_code == 422
    assert after_closing.json()["error"]["code"] == (
        "OUTSIDE_BUSINESS_HOURS"
    )


def test_start_not_on_grid(engine: Engine) -> None:
    ids = catalog_ids(engine)

    response = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-01T10:10:00-05:00")
        )
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_START_TIME"


def test_booking_window(engine: Engine) -> None:
    ids = catalog_ids(engine)
    app.dependency_overrides[get_now] = lambda: datetime(
        2026, 12, 2, 8, 0, tzinfo=TZ
    )

    past = asyncio.run(post_booking(payload(ids)))
    too_far = asyncio.run(
        post_booking(
            payload(ids, start_at="2026-12-17T10:00:00-05:00")
        )
    )

    assert past.status_code == 422
    assert past.json()["error"]["code"] == "PAST_DATE"
    assert too_far.status_code == 422
    assert too_far.json()["error"]["code"] == "TOO_FAR_AHEAD"


def test_client_validation(engine: Engine) -> None:
    ids = catalog_ids(engine)

    invalid_phone = asyncio.run(
        post_booking(payload(ids, client_phone="1234"))
    )
    invalid_name = asyncio.run(
        post_booking(
            payload(ids, client_name="", client_phone="1234")
        )
    )

    assert invalid_phone.status_code == 422
    assert invalid_phone.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": (
            "Teléfono inválido: use 8 dígitos que empiecen por 6 "
            "(6XXX-XXXX)"
        ),
        "details": {"field": "client_phone"},
    }
    assert invalid_name.status_code == 422
    assert invalid_name.json()["error"]["code"] == "VALIDATION_ERROR"
    assert invalid_name.json()["error"]["details"] == {
        "field": "client_name"
    }


def test_cancelled_booking_does_not_block(engine: Engine) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="EEE222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
        status="CANCELADA",
    )

    response = asyncio.run(post_booking(payload(ids)))

    assert response.status_code == 201
    assert booking_count(engine) == 2


def test_booking_naive_datetime_rejected(engine: Engine) -> None:
    ids = catalog_ids(engine)

    response = asyncio.run(
        post_booking(payload(ids, start_at="2026-12-01T10:00:00"))
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"] == {"field": "start_at"}


def test_booking_inactive_barber(engine: Engine) -> None:
    ids = catalog_ids(engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = false WHERE id = :id"),
                {"id": ids["barber_Carlos"]},
            )

        response = asyncio.run(post_booking(payload(ids)))

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "BARBER_INACTIVE"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = true WHERE id = :id"),
                {"id": ids["barber_Carlos"]},
            )


def test_booking_unknown_service(engine: Engine) -> None:
    ids = catalog_ids(engine)
    request = payload(ids)
    request["service_id"] = 999_999

    response = asyncio.run(post_booking(request))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_booking_unknown_barber(engine: Engine) -> None:
    ids = catalog_ids(engine)
    request = payload(ids)
    request["barber_id"] = 999_999

    response = asyncio.run(post_booking(request))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_db_layer_returns_slot_taken(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="FFF222",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 10, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 10, 30, tzinfo=TZ),
    )
    monkeypatch.setattr(
        "app.repositories.bookings.find_overlapping",
        lambda *_args, **_kwargs: [],
    )

    response = asyncio.run(post_booking(payload(ids)))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SLOT_TAKEN"
    assert booking_count(engine) == 1


def test_booking_code_collision_retries(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = catalog_ids(engine)
    insert_booking(
        engine,
        code="ABC234",
        barber_id=ids["barber_Carlos"],
        service_id=ids["service_Corte"],
        start_at=datetime(2026, 12, 1, 9, 0, tzinfo=TZ),
        end_at=datetime(2026, 12, 1, 9, 30, tzinfo=TZ),
    )
    codes = iter(["ABC234", "DEF567"])
    monkeypatch.setattr(
        "app.services.booking.rules.generate_booking_code",
        lambda: next(codes),
    )

    response = asyncio.run(post_booking(payload(ids)))

    assert response.status_code == 201
    assert response.json()["code"] == "DEF567"
    assert booking_count(engine) == 2
