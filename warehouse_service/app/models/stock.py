"""Модели контекста «Складской учет и заказ запчастей»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class Part(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
    quantity: int = Field(ge=0)          # на складе
    reserved: int = Field(ge=0, default=0)
    min_quantity: int = Field(ge=0, default=2)
    created_at: datetime = Field(default_factory=now)


class PartCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
    quantity: int = Field(ge=0)
    min_quantity: int = Field(ge=0, default=2)


class PartOut(Part):
    available: int


class ReservationStatus(str, enum.Enum):
    RESERVED = "reserved"
    WAITING = "waiting"      # ждет поставки
    ISSUED = "issued"        # выдана механику и списана


class Reservation(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    sku: str
    qty: int = Field(ge=1)
    status: ReservationStatus
    created_at: datetime = Field(default_factory=now)


class PurchaseStatus(str, enum.Enum):
    ORDERED = "ordered"
    RECEIVED = "received"


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    sku: str
    qty: int = Field(ge=1)
    order_id: UUID | None = None
    status: PurchaseStatus = PurchaseStatus.ORDERED
    created_at: datetime = Field(default_factory=now)
    received_at: datetime | None = None
