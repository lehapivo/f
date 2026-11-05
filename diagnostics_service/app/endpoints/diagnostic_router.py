from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.gateways.warehouse_gateway import WarehouseGateway
from app.messaging import RabbitPublisher
from app.models.diagnostic import Diagnostic, DiagnosticResult, DiagnosticStatus
from app.repositories.db_diagnostic_repo import DiagnosticRepo
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


def get_service(db: Session = Depends(get_db)) -> DiagnosticService:
    return DiagnosticService(DiagnosticRepo(db), RabbitPublisher(), WarehouseGateway())


@router.get("")
def list_diagnostics(status: DiagnosticStatus | None = None, order_id: UUID | None = None,
                     offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
                     service: DiagnosticService = Depends(get_service)) -> list[Diagnostic]:
    return service.list(status.value if status else None, order_id, offset, count)


@router.get("/{diagnostic_id}")
def get_diagnostic(diagnostic_id: UUID, service: DiagnosticService = Depends(get_service)) -> Diagnostic:
    return service.get(diagnostic_id)


@router.post("/{diagnostic_id}:complete")
def complete_diagnostic(diagnostic_id: UUID, result: DiagnosticResult,
                        service: DiagnosticService = Depends(get_service)) -> Diagnostic:
    return service.complete(diagnostic_id, result)
