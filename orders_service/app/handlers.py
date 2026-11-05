"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.gateways.clients_gateway import ClientsGateway
from app.messaging import RabbitPublisher
from app.repositories.db_order_repo import OrderRepo
from app.services.order_service import OrderService

QUEUE = "autoservice.orders"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            service = OrderService(OrderRepo(db), RabbitPublisher(), ClientsGateway())
            getattr(service, method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {
    "diagnostics.completed": _handler("on_diagnostics_completed"),
    "repair.completed": _handler("on_repair_completed"),
    "invoice.issued": _handler("on_invoice_issued"),
    "invoice.paid": _handler("on_invoice_paid"),
}
