from datetime import date as Date
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import get_now
from app.db import get_db
from app.schemas.availability import AvailabilityOut
from app.services.availability import get_availability

router = APIRouter(prefix="/api/v1", tags=["availability"])


@router.get("/availability", response_model=AvailabilityOut)
def availability(
    barber_id: int,
    service_id: int,
    date: Date,
    db: Session = Depends(get_db),
    now: datetime = Depends(get_now),
):
    return get_availability(db, barber_id, service_id, date, now)
