from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.barber import Barber
from app.models.service import Service


def list_active_barbers(db: Session) -> list[Barber]:
    return list(
        db.scalars(
            select(Barber).where(Barber.active.is_(True)).order_by(Barber.id)
        )
    )


def list_services(db: Session) -> list[Service]:
    return list(db.scalars(select(Service).order_by(Service.id)))
