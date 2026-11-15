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
        start_at, end_at, status
    )
    VALUES (
        :code, :barber_id, :service_id, :client_name, :client_phone,
        :start_at, :end_at, :status
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


def test_db_allows_adjacent_bookings(
    engine: Engine, clean_bookings: None
) -> None:
    barber_id, service_id = seed_ids(engine)
    insert_booking(
        engine,
        code="EEE555",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START,
        end_at=BASE_START + timedelta(minutes=30),
    )
    insert_booking(
        engine,
        code="FFF666",
        barber_id=barber_id,
        service_id=service_id,
        start_at=BASE_START + timedelta(minutes=30),
        end_at=BASE_START + timedelta(minutes=60),
    )

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM bookings")).scalar_one()
    assert total == 2
