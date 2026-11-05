"""Модели контекста «Расчеты и выставление счетов»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class InvoiceStatus(str, enum.Enum):
    ISSUED = "issued"
    PAID = "paid"


class InvoiceLine(BaseModel):
    kind: str            # work | part
    name: str
    qty: int = Field(ge=1)
    price: int = Field(ge=0)
    amount: int = Field(ge=0)


class Invoice(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    client_id: UUID
    lines: list[InvoiceLine] = []
    total: int = Field(ge=0, default=0)
    status: InvoiceStatus = InvoiceStatus.ISSUED
    payment_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paid_at: datetime | None = None
