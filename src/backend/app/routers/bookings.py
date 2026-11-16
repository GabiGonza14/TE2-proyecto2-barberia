from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import get_now
from app.db import get_db
from app.schemas.bookings import BookingCreate, BookingOut
from app.services.booking import create_booking

router = APIRouter(prefix="/api/v1", tags=["bookings"])


@router.post("/bookings", status_code=201)
def post_booking(
    data: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    now: Annotated[datetime, Depends(get_now)],
) -> BookingOut:
    return create_booking(db, data, now)
