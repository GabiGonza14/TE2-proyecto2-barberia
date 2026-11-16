from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.rules import TZ
from app.models.booking import STATUS_CONFIRMED, Booking


def confirmed_bookings_for_day(
    db: Session, barber_id: int, day: date
) -> list[Booking]:
    day_start = datetime.combine(day, time.min, TZ)
    day_end = day_start + timedelta(days=1)
    return list(
        db.scalars(
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.status == STATUS_CONFIRMED,
                Booking.start_at < day_end,
                Booking.end_at > day_start,
            )
            .order_by(Booking.start_at)
        )
    )
