from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Barber(Base):
    __tablename__ = "barbers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="barber")
