"""Модели контекста «Диагностика автомобиля»."""
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Work(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    price: int = Field(ge=0)


class PartRequest(BaseModel):
    sku: str = Field(min_length=1)
    qty: int = Field(ge=1)


class PartLine(PartRequest):
    name: str
    price: int
    in_stock: bool


class Diagnostic(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    vehicle_id: UUID
    complaint: str
    status: DiagnosticStatus = DiagnosticStatus.PENDING
    faults: list[str] = []
    works: list[Work] = []
    parts: list[PartLine] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class DiagnosticResult(BaseModel):
    faults: list[str] = Field(min_length=1)
    works: list[Work] = Field(min_length=1)
    parts: list[PartRequest] = []
