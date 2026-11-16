from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.clock import get_now
from app.db import get_db
from app.schemas.bookings import BookingCreate, BookingOut, CancelOut, CancelRequest
from app.services.booking import cancel_booking, create_booking, get_booking

router = APIRouter(prefix="/api/v1", tags=["bookings"])


@router.post("/bookings", status_code=201)
def post_booking(
    data: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    now: Annotated[datetime, Depends(get_now)],
) -> BookingOut:
    return create_booking(db, data, now)


@router.get("/bookings/{code}")
def get_booking_by_code(
    code: str,
    phone: Annotated[str, Query()],
    db: Annotated[Session, Depends(get_db)],
) -> BookingOut:
    return get_booking(db, code, phone)


@router.post("/bookings/{code}/cancel")
def post_cancel_booking(
    code: str,
    data: CancelRequest,
    db: Annotated[Session, Depends(get_db)],
    now: Annotated[datetime, Depends(get_now)],
) -> CancelOut:
    return cancel_booking(db, code, data.phone, now)
