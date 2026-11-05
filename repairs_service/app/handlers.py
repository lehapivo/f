"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.messaging import RabbitPublisher
from app.repositories.db_repair_repo import PartsStateRepo, RepairRepo
from app.services.repair_service import RepairService

QUEUE = "autoservice.repairs"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            getattr(RepairService(RepairRepo(db), PartsStateRepo(db), RabbitPublisher()), method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {
    "order.approved": _handler("on_order_approved"),
    "parts.reserved": _handler("on_parts_reserved"),
    "parts.shortage": _handler("on_parts_shortage"),
}
