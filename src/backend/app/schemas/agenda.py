from datetime import date

from pydantic import BaseModel


class AgendaBooking(BaseModel):
    start: str
    end: str
    service: str
    client: str
    code: str


class AgendaBarber(BaseModel):
    barber: str
    bookings: list[AgendaBooking]


class AgendaOut(BaseModel):
    date: date
    barbers: list[AgendaBarber]
