"""Модели контекста «Управление ремонтом»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class RepairStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PartsStatus(str, enum.Enum):
    PENDING = "pending"      # склад еще не ответил
    RESERVED = "reserved"
    SHORTAGE = "shortage"


class Work(BaseModel):
    code: str
    name: str
    price: int = Field(ge=0)


class PartLine(BaseModel):
    sku: str
    name: str = ""
    qty: int = Field(ge=1)
    price: int = Field(ge=0, default=0)


class Repair(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    vehicle_id: UUID
    works: list[Work] = []
    parts: list[PartLine] = []
    status: RepairStatus = RepairStatus.PLANNED
    mechanic: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class PartsState(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    order_id: UUID
    status: PartsStatus
    updated_at: datetime = Field(default_factory=now)


class RepairOut(Repair):
    parts_status: PartsStatus


class RepairStart(BaseModel):
    mechanic: str = Field(min_length=1, max_length=100)


class RepairComplete(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
