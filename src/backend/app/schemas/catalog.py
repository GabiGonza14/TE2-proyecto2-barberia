from pydantic import BaseModel, ConfigDict


class BarberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_min: int
    price: float
