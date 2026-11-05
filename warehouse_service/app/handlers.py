"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.messaging import RabbitPublisher
from app.repositories.db_stock_repo import PartRepo, PurchaseOrderRepo, ReservationRepo
from app.services.stock_service import StockService

QUEUE = "autoservice.warehouse"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            service = StockService(PartRepo(db), ReservationRepo(db), PurchaseOrderRepo(db), RabbitPublisher())
            getattr(service, method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {
    "order.approved": _handler("on_order_approved"),
    "repair.completed": _handler("on_repair_completed"),
}
