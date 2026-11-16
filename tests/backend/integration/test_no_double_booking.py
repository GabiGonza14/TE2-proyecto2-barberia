from datetime import datetime, timedelta, timezone

import pytest
from psycopg.errors import ExclusionViolation
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

INSERT_BOOKING = text(
    """
    INSERT INTO bookings (
        code, barber_id, service_id, client_name, client_phone,
        start_at, end_at, blocked_until, status
    )
    VALUES (
        :code, :barber_id, :service_id, :client_name, :client_phone,
        :start_at, :end_at, :blocked_until, :status
    )
    """
)

BASE_START = datetime(2026, 12, 1, 15, 0, tzinfo=timezone.utc)


def seed_ids(engine: Engine) -> tuple[int, int]:
    with engine.connect() as conn:
        barber_id = conn.execute(
            text("SELECT id FROM barbers ORDER BY id LIMIT 1")
        ).scalar_one()
        service_id = conn.execute(
            text("SELECT id FROM services WHERE name = 'Corte'")
        ).scalar_one()
    return barber_id, service_id


def insert_booking(
    engine: Engine,
    *,
    code: str,
    barber_id: int,
    service_id: int,
    start_at: datetime,
    end_at: datetime,
    status: str = "CONFIRMADA",
    blocked_until: datetime | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            INSERT_BOOKING,
            {
                "code": code,
                "barber_id": barber_id,
                "service_id": service_id,
                "client_name": "Cliente Prueba",
                "client_phone": "60000000",
                "start_at": start_at,
                "end_at": end_at,
                "blocked_until": (
                    blocked_until
                    if blocked_until is not None
                    else end_at + timedelta(minutes=10)
                ),
                "status": status,
            },
        )


def test_db_rejects_overlapping_bookings(
    engine: Engine, clean_bookings: None
) -> None:
    barber_id, service_id = seed_ids(engine)
    insert_booking(
        engine,
        code="AAA111",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
    )

    with pytest.raises(IntegrityError) as excinfo:
        insert_booking(
            engine,
            code="BBB222",
            barber_id=barber_id,
            service_id=service_id,
            start_at=BASE_START + timedelta(minutes=15),
            end_at=BASE_START + timedelta(minutes=45),
        )

    assert isinstance(excinfo.value.orig, ExclusionViolation)

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    assert total == 1


def test_db_allows_overlap_if_cancelled(
    engine: Engine, clean_bookings: None
) -> None:
    barber_id, service_id = seed_ids(engine)
    insert_booking(
        engine,
        code="CCC333",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
        status="CANCELADA",
    )
    insert_booking(
        engine,
        code="DDD444",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
        status="CONFIRMADA",
    )

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    assert total == 2


def test_db_rejects_adjacent_bookings(
    engine: Engine, clean_bookings: None
) -> None:
    """BR-12 en la BD: 10:00–10:30 bloquea hasta 10:40; 10:30 ya no entra."""
    barber_id, service_id = seed_ids(engine)
    insert_booking(
        engine,
        code="EEE555",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
    )

    with pytest.raises(IntegrityError) as excinfo:
        insert_booking(
            engine,
            code="FFF666",
            barber_id=barber_id,
            service_id=service_id,
            start_at=BASE_START + timedelta(minutes=30),
            end_at=BASE_START + timedelta(minutes=60),
        )

    assert isinstance(excinfo.value.orig, ExclusionViolation)

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    assert total == 1


def test_db_enforces_buffer(
    engine: Engine, clean_bookings: None
) -> None:
    """AC-24 · RNF-01: la BD rechaza una cita que choca con la limpieza de
    otra CONFIRMADA; si la primera está CANCELADA, se acepta."""
    barber_id, service_id = seed_ids(engine)
    insert_booking(
        engine,
        code="HHH777",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
    )

    with pytest.raises(IntegrityError) as excinfo:
        insert_booking(
            engine,
            code="III888",
            barber_id=barber_id,
            service_id=service_id,
            start_at=BASE_START + timedelta(minutes=30),
            end_at=BASE_START + timedelta(minutes=60),
            blocked_until=BASE_START + timedelta(minutes=70),
        )

    assert isinstance(excinfo.value.orig, ExclusionViolation)

    # La cancelada no bloquea la limpieza (BR-07): el mismo hueco se acepta.
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE bookings SET status = 'CANCELADA' WHERE code = :code"),
            {"code": "HHH777"},
        )

    insert_booking(
        engine,
        code="III888",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START + timedelta(minutes=30),
        end_at=BASE_START + timedelta(minutes=60),
        blocked_until=BASE_START + timedelta(minutes=70),
    )

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    assert total == 2
