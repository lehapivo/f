from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.messaging import RabbitPublisher
from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.db_invoice_repo import InvoiceRepo
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def get_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(InvoiceRepo(db), RabbitPublisher())


@router.get("")
def list_invoices(order_id: UUID | None = None, client_id: UUID | None = None,
                  status: InvoiceStatus | None = None, offset: int = Query(0, ge=0),
                  count: int = Query(20, ge=1, le=100),
                  service: InvoiceService = Depends(get_service)) -> list[Invoice]:
    return service.list(order_id, client_id, status.value if status else None, offset, count)


@router.get("/{invoice_id}")
def get_invoice(invoice_id: UUID, service: InvoiceService = Depends(get_service)) -> Invoice:
    return service.get(invoice_id)
