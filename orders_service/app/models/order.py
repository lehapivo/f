"""Модели контекста «Управление заказ-нарядами» (анемичные, только данные)."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, enum.Enum):
    CREATED = "created"        # автомобиль принят, заказ-наряд создан
    DIAGNOSED = "diagnosed"    # результаты диагностики и стоимость получены
    APPROVED = "approved"      # работы согласованы с клиентом
    READY = "ready"            # ремонт завершен
    PAID = "paid"              # счет оплачен
    CLOSED = "closed"          # автомобиль выдан клиенту


class Work(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    price: int = Field(ge=0)


class PartLine(BaseModel):
    sku: str = Field(min_length=1)
    name: str = ""
    qty: int = Field(ge=1)
    price: int = Field(ge=0, default=0)


class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    vehicle_id: UUID
    appointment_id: UUID | None = None
    complaint: str = Field(min_length=1)
    mileage: int = Field(ge=0)
    status: OrderStatus = OrderStatus.CREATED
    faults: list[str] = []
    works: list[Work] = []
    parts: list[PartLine] = []
    estimate: int = 0
    invoice_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None


class OrderCreate(BaseModel):
    client_id: UUID
    vehicle_id: UUID
    appointment_id: UUID | None = None
    complaint: str = Field(min_length=1, max_length=1000)
    mileage: int = Field(ge=0)


class OrderApprove(BaseModel):
    work_codes: list[str] | None = None   # None — согласованы все рекомендованные работы


class OrderClose(BaseModel):
    mileage: int | None = Field(default=None, ge=0)
