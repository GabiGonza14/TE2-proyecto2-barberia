from datetime import date

from pydantic import BaseModel


class AvailabilityOut(BaseModel):
    date: date
    barber_id: int
    service_id: int
    slots: list[str]
    reason: str | None
