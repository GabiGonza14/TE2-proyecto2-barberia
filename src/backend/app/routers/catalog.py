from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.catalog import list_active_barbers, list_services
from app.schemas.catalog import BarberOut, ServiceOut

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/barbers", response_model=list[BarberOut])
def get_barbers(db: Session = Depends(get_db)):
    return list_active_barbers(db)


@router.get("/services", response_model=list[ServiceOut])
def get_services(db: Session = Depends(get_db)):
    return list_services(db)
