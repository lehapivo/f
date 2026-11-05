"""Модели контекста «Управление клиентами и автомобилями»."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class Client(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(pattern=r"^\+?\d{10,15}$")
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    created_at: datetime = Field(default_factory=now)


class Vehicle(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    vin: str = Field(min_length=17, max_length=17)
    plate: str = Field(min_length=1, max_length=12)
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1950, le=2100)
    mileage: int = Field(ge=0)
    created_at: datetime = Field(default_factory=now)


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(pattern=r"^\+?\d{10,15}$")
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class VehicleCreate(BaseModel):
    vin: str = Field(min_length=17, max_length=17)
    plate: str = Field(min_length=1, max_length=12)
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1950, le=2100)
    mileage: int = Field(ge=0)


class ClientCard(Client):
    vehicles: list[Vehicle] = []
