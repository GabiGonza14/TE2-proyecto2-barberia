from datetime import datetime

from pydantic import BaseModel


class BookingCreate(BaseModel):
    barber_id: int
    service_id: int
    start_at: datetime
    client_name: str
    client_phone: str


class BookingOut(BaseModel):
    code: str
    status: str
    barber: str
    service: str
    start_at: datetime
    end_at: datetime
