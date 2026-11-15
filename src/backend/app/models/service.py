from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "duration_min > 0", name="ck_services_duration_positive"
        ),
        CheckConstraint("price >= 0", name="ck_services_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    duration_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")
