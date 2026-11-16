from decimal import Decimal

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def test_migration_applies(engine: Engine) -> None:
    inspector = inspect(engine)
    assert {"barbers", "services", "bookings"} <= set(inspector.get_table_names())

    with engine.connect() as conn:
        has_btree_gist = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
        ).scalar_one_or_none()
        assert has_btree_gist == 1

        exclusion_constraints = (
            conn.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = 'bookings'::regclass AND contype = 'x'"
                )
            )
            .scalars()
            .all()
        )
        assert "no_double_booking" in exclusion_constraints

        check_constraints = {
            row.conname
            for row in conn.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid IN "
                    "('bookings'::regclass, 'services'::regclass) AND contype = 'c'"
                )
            )
        }
        assert {
            "ck_bookings_end_after_start",
            "ck_bookings_blocked_until",
            "ck_services_duration_positive",
            "ck_services_price_non_negative",
        } <= check_constraints


def test_seed_data(engine: Engine) -> None:
    with engine.connect() as conn:
        barbers = set(conn.execute(text("SELECT name FROM barbers")).scalars().all())
        assert barbers == {"Carlos", "Luis", "Andrés"}

        services = {
            name: (duration, price)
            for name, duration, price in conn.execute(
                text("SELECT name, duration_min, price FROM services")
            )
        }
        assert services == {
            "Corte": (30, Decimal("8.00")),
            "Barba": (20, Decimal("5.00")),
            "Corte+Barba": (45, Decimal("12.00")),
            "Diseño/Fade": (40, Decimal("10.00")),
        }
