"""CR-01: limpieza de 10 min entre citas del mismo barbero (T13).

Revision ID: 0002_t13_cleanup
Revises: 0001_t2_schema
Create Date: 2026-11-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_t13_cleanup"
down_revision: str | None = "0001_t2_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Columna nueva (nullable mientras se rellena).
    op.add_column(
        "bookings",
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
    )

    # 2) Backfill: cada cita existente bloquea hasta end_at + 10 min.
    op.execute(
        "UPDATE bookings SET blocked_until = end_at + interval '10 minutes'"
    )

    # 3) NOT NULL + CHECK de igualdad: la limpieza siempre es 10 min.
    op.alter_column("bookings", "blocked_until", nullable=False)
    op.create_check_constraint(
        "ck_bookings_blocked_until",
        "bookings",
        "blocked_until = end_at + interval '10 minutes'",
    )

    # 4) BR-01/BR-12: el rango excluido incluye la limpieza. No se puede usar
    #    `end_at + interval` dentro del índice GiST (no es IMMUTABLE).
    op.execute("ALTER TABLE bookings DROP CONSTRAINT no_double_booking")
    op.execute(
        """
        ALTER TABLE bookings ADD CONSTRAINT no_double_booking
          EXCLUDE USING gist (
            barber_id WITH =,
            tstzrange(start_at, blocked_until, '[)') WITH &&
          )
          WHERE (status = 'CONFIRMADA')
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT no_double_booking")
    op.execute(
        """
        ALTER TABLE bookings ADD CONSTRAINT no_double_booking
          EXCLUDE USING gist (
            barber_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
          )
          WHERE (status = 'CONFIRMADA')
        """
    )
    op.drop_constraint(
        "ck_bookings_blocked_until", "bookings", type_="check"
    )
    op.drop_column("bookings", "blocked_until")
