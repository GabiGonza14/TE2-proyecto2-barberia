"""Modelos iniciales, no_double_booking y datos semilla (T2).

Revision ID: 0001_t2_schema
Revises:
Create Date: 2026-11-15
"""

from collections.abc import Sequence
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0001_t2_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "barbers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("duration_min", sa.SmallInteger(), nullable=False),
        sa.Column("price", sa.Numeric(6, 2), nullable=False),
        sa.CheckConstraint(
            "duration_min > 0", name="ck_services_duration_positive"
        ),
        sa.CheckConstraint("price >= 0", name="ck_services_price_non_negative"),
        sa.UniqueConstraint("name", name="uq_services_name"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.CHAR(length=6), nullable=False),
        sa.Column("barber_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=60), nullable=False),
        sa.Column("client_phone", sa.String(length=8), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=12),
            nullable=False,
            server_default=sa.text("'CONFIRMADA'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "end_at > start_at", name="ck_bookings_end_after_start"
        ),
        sa.CheckConstraint(
            "status IN ('CONFIRMADA', 'CANCELADA')", name="ck_bookings_status"
        ),
        sa.ForeignKeyConstraint(["barber_id"], ["barbers.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.UniqueConstraint("code", name="uq_bookings_code"),
    )

    op.create_index(
        "ix_bookings_barber_id_start_at", "bookings", ["barber_id", "start_at"]
    )

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

    barbers = sa.table(
        "barbers",
        sa.column("name", sa.String),
        sa.column("active", sa.Boolean),
    )
    op.bulk_insert(
        barbers,
        [
            {"name": "Carlos", "active": True},
            {"name": "Luis", "active": True},
            {"name": "Andrés", "active": True},
        ],
    )

    services = sa.table(
        "services",
        sa.column("name", sa.String),
        sa.column("duration_min", sa.SmallInteger),
        sa.column("price", sa.Numeric),
    )
    op.bulk_insert(
        services,
        [
            {"name": "Corte", "duration_min": 30, "price": Decimal("8.00")},
            {"name": "Barba", "duration_min": 20, "price": Decimal("5.00")},
            {
                "name": "Corte+Barba",
                "duration_min": 45,
                "price": Decimal("12.00"),
            },
            {
                "name": "Diseño/Fade",
                "duration_min": 40,
                "price": Decimal("10.00"),
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_barber_id_start_at", table_name="bookings")
    op.drop_table("bookings")
    op.drop_table("services")
    op.drop_table("barbers")
