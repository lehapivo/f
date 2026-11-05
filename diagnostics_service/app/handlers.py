"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.gateways.warehouse_gateway import WarehouseGateway
from app.messaging import RabbitPublisher
from app.repositories.db_diagnostic_repo import DiagnosticRepo
from app.services.diagnostic_service import DiagnosticService

QUEUE = "autoservice.diagnostics"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            getattr(DiagnosticService(DiagnosticRepo(db), RabbitPublisher(), WarehouseGateway()), method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {"order.created": _handler("on_order_created")}
