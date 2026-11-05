from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.gateways.billing_gateway import BillingGateway
from app.gateways.payment_provider import PaymentProvider
from app.messaging import RabbitPublisher
from app.models.payment import Payment, PaymentCreate
from app.repositories.db_payment_repo import PaymentRepo
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(PaymentRepo(db), RabbitPublisher(), BillingGateway(), PaymentProvider())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_payment(data: PaymentCreate, service: PaymentService = Depends(get_service)) -> Payment:
    return service.pay(data)


@router.get("")
def list_payments(invoice_id: UUID | None = None, offset: int = Query(0, ge=0),
                  count: int = Query(20, ge=1, le=100),
                  service: PaymentService = Depends(get_service)) -> list[Payment]:
    return service.list(invoice_id, offset, count)


@router.get("/{payment_id}")
def get_payment(payment_id: UUID, service: PaymentService = Depends(get_service)) -> Payment:
    return service.get(payment_id)
