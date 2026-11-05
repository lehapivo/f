from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.messaging import RabbitPublisher
from app.models.repair import RepairComplete, RepairOut, RepairStart, RepairStatus
from app.repositories.db_repair_repo import PartsStateRepo, RepairRepo
from app.services.repair_service import RepairService

router = APIRouter(prefix="/repairs", tags=["Repairs"])


def get_service(db: Session = Depends(get_db)) -> RepairService:
    return RepairService(RepairRepo(db), PartsStateRepo(db), RabbitPublisher())


@router.get("")
def list_repairs(status: RepairStatus | None = None, order_id: UUID | None = None,
                 offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
                 service: RepairService = Depends(get_service)) -> list[RepairOut]:
    return service.list(status.value if status else None, order_id, offset, count)


@router.get("/{repair_id}")
def get_repair(repair_id: UUID, service: RepairService = Depends(get_service)) -> RepairOut:
    return service.get(repair_id)


@router.post("/{repair_id}:start")
def start_repair(repair_id: UUID, data: RepairStart, service: RepairService = Depends(get_service)) -> RepairOut:
    return service.start(repair_id, data.mechanic)


@router.post("/{repair_id}:complete")
def complete_repair(repair_id: UUID, data: RepairComplete | None = None,
                    service: RepairService = Depends(get_service)) -> RepairOut:
    return service.complete(repair_id, data.note if data else None)
