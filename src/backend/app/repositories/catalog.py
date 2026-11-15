from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.barber import Barber
from app.models.service import Service


def get_barber(db: Session, barber_id: int) -> Barber | None:
    return db.get(Barber, barber_id)


def get_service(db: Session, service_id: int) -> Service | None:
    return db.get(Service, service_id)


def list_active_barbers(db: Session) -> list[Barber]:
    return list(
        db.scalars(
            select(Barber).where(Barber.active.is_(True)).order_by(Barber.id)
        )
    )


def list_services(db: Session) -> list[Service]:
    return list(db.scalars(select(Service).order_by(Service.id)))
