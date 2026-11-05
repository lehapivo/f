from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.errors import BusinessRuleError, ConflictError
from app.messaging import MemoryPublisher
from app.models.appointment import AppointmentCreate, AppointmentStatus
from app.repositories.local_appointment_repo import AppointmentRepo
from app.services.appointment_service import AppointmentService


class FakeClients:
    def __init__(self):
        self.vehicles = {}

    def get_vehicle(self, vehicle_id):
        return self.vehicles.get(vehicle_id)


@pytest.fixture()
def ctx():
    clients = FakeClients()
    service = AppointmentService(AppointmentRepo(), MemoryPublisher(), clients)
    client_id, vehicle_id = uuid4(), uuid4()
    clients.vehicles[vehicle_id] = {"client_id": str(client_id), "mileage": 0}
    when = (datetime.now(timezone.utc) + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    return service, AppointmentCreate(client_id=client_id, vehicle_id=vehicle_id, scheduled_at=when, reason="ТО-60")


def test_create_and_confirm(ctx):
    service, data = ctx
    appointment = service.create(data)
    assert service.confirm(appointment.id).status == AppointmentStatus.CONFIRMED
    assert service.publisher.keys() == ["appointment.created", "appointment.confirmed"]


def test_slot_taken(ctx):
    service, data = ctx
    service.create(data)
    with pytest.raises(ConflictError):
        service.create(data)


def test_cancelled_slot_is_free_again(ctx):
    service, data = ctx
    service.cancel(service.create(data).id)
    assert service.create(data).status == AppointmentStatus.CREATED


def test_past_time_rejected(ctx):
    service, data = ctx
    data.scheduled_at = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(BusinessRuleError):
        service.create(data)


def test_foreign_vehicle_rejected(ctx):
    service, data = ctx
    data.client_id = uuid4()
    with pytest.raises(BusinessRuleError) as err:
        service.create(data)
    assert err.value.code == "vehicle_of_other_client"


def test_order_created_marks_arrival(ctx):
    service, data = ctx
    appointment = service.create(data)
    order_id = uuid4()
    service.on_order_created({"order_id": str(order_id), "appointment_id": str(appointment.id)})
    saved = service.get(appointment.id)
    assert saved.status == AppointmentStatus.ARRIVED and saved.order_id == order_id
    with pytest.raises(ConflictError):
        service.cancel(appointment.id)
