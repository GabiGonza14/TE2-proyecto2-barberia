from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.clock import get_now
from app.core.security import require_admin
from app.db import get_db
from app.domain.rules import TZ
from app.schemas.agenda import AgendaOut
from app.services.agenda import get_agenda

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/agenda")
def get_admin_agenda(
    db: Annotated[Session, Depends(get_db)],
    now: Annotated[datetime, Depends(get_now)],
    day: Annotated[date | None, Query(alias="date")] = None,
    barber_id: Annotated[int | None, Query()] = None,
) -> AgendaOut:
    return get_agenda(db, day or now.astimezone(TZ).date(), barber_id)
