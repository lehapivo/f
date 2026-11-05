"""Модели контекста «Управление записью»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AppointmentStatus(str, enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    ARRIVED = "arrived"      # клиент приехал, по записи открыт заказ-наряд


class Appointment(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    client_id: UUID
    vehicle_id: UUID
    scheduled_at: datetime
    reason: str = Field(min_length=1, max_length=500)
    status: AppointmentStatus = AppointmentStatus.CREATED
    order_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AppointmentCreate(BaseModel):
    client_id: UUID
    vehicle_id: UUID
    scheduled_at: datetime
    reason: str = Field(min_length=1, max_length=500)
