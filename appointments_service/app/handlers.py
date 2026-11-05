"""Обработчики событий из очереди сервиса."""
from app.database import SessionLocal
from app.gateways.clients_gateway import ClientsGateway
from app.messaging import RabbitPublisher
from app.repositories.db_appointment_repo import AppointmentRepo
from app.services.appointment_service import AppointmentService

QUEUE = "autoservice.appointments"


def _handler(method: str):
    def handle(event: dict) -> None:
        db = SessionLocal()
        try:
            getattr(AppointmentService(AppointmentRepo(db), RabbitPublisher(), ClientsGateway()), method)(event)
        finally:
            db.close()
    return handle


HANDLERS = {"order.created": _handler("on_order_created")}
