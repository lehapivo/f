"""Модели контекста «Управление платежами»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethod(str, enum.Enum):
    CARD = "card"
    CASH = "cash"


class PaymentStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    DECLINED = "declined"


class Payment(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    invoice_id: UUID
    amount: int = Field(gt=0)
    method: PaymentMethod
    status: PaymentStatus
    external_id: str | None = None
    decline_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: int = Field(gt=0)
    method: PaymentMethod
