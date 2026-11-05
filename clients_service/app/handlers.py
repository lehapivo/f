"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.messaging import RabbitPublisher
from app.repositories.db_client_repo import ClientRepo, VehicleRepo
from app.services.client_service import ClientService

QUEUE = "autoservice.clients"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            getattr(ClientService(ClientRepo(db), VehicleRepo(db), RabbitPublisher()), method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {"order.closed": _handler("on_order_closed")}
