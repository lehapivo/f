"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.messaging import RabbitPublisher
from app.repositories.db_invoice_repo import InvoiceRepo
from app.services.invoice_service import InvoiceService

QUEUE = "autoservice.billing"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            getattr(InvoiceService(InvoiceRepo(db), RabbitPublisher()), method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {
    "order.completed": _handler("on_order_completed"),
    "payment.succeeded": _handler("on_payment_succeeded"),
}
