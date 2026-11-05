from uuid import uuid4

import pytest

from app.errors import BusinessRuleError, ConflictError
from app.messaging import MemoryPublisher
from app.models.order import OrderCreate, OrderStatus
from app.repositories.local_order_repo import OrderRepo
from app.services.order_service import OrderService


class FakeClients:
    """Подмена синхронного вызова сервиса клиентов."""
    def __init__(self):
        self.vehicles = {}

    def get_vehicle(self, vehicle_id):
        return self.vehicles.get(vehicle_id)


@pytest.fixture()
def ctx():
    clients, publisher = FakeClients(), MemoryPublisher()
    service = OrderService(OrderRepo(), publisher, clients)
    client_id, vehicle_id = uuid4(), uuid4()
    clients.vehicles[vehicle_id] = {"id": str(vehicle_id), "client_id": str(client_id), "mileage": 50000}
    data = OrderCreate(client_id=client_id, vehicle_id=vehicle_id, complaint="Стук в подвеске", mileage=51000)
    return service, publisher, data


DIAG = {"faults": ["Износ колодок"],
        "works": [{"code": "W-01", "name": "Замена колодок", "price": 2500},
                  {"code": "W-02", "name": "Проточка дисков", "price": 1800}],
        "parts": [{"sku": "BP-001", "name": "Колодки", "qty": 1, "price": 3500}]}


def test_create_order_publishes_event(ctx):
    service, publisher, data = ctx
    order = service.create_order(data)
    assert order.status == OrderStatus.CREATED
    assert publisher.keys() == ["order.created"]


def test_create_order_unknown_vehicle(ctx):
    service, _, data = ctx
    data.vehicle_id = uuid4()
    with pytest.raises(BusinessRuleError) as err:
        service.create_order(data)
    assert err.value.code == "vehicle_not_found"


def test_create_order_vehicle_of_other_client(ctx):
    service, _, data = ctx
    data.client_id = uuid4()
    with pytest.raises(BusinessRuleError):
        service.create_order(data)


def test_mileage_cannot_decrease(ctx):
    service, _, data = ctx
    data.mileage = 1000
    with pytest.raises(BusinessRuleError):
        service.create_order(data)


def test_diagnostics_sets_estimate(ctx):
    service, _, data = ctx
    order = service.create_order(data)
    service.on_diagnostics_completed({"order_id": str(order.id), **DIAG})
    order = service.get_order(order.id)
    assert order.status == OrderStatus.DIAGNOSED
    assert order.estimate == 2500 + 1800 + 3500


def test_partial_approve_recalculates_estimate(ctx):
    service, publisher, data = ctx
    order = service.create_order(data)
    service.on_diagnostics_completed({"order_id": str(order.id), **DIAG})
    order = service.approve(order.id, ["W-01"])
    assert [w.code for w in order.works] == ["W-01"]
    assert order.estimate == 2500 + 3500
    assert publisher.keys()[-1] == "order.approved"


def test_approve_requires_diagnosis(ctx):
    service, _, data = ctx
    order = service.create_order(data)
    with pytest.raises(ConflictError):
        service.approve(order.id)


def test_full_lifecycle_until_closed(ctx):
    service, publisher, data = ctx
    order = service.create_order(data)
    service.on_diagnostics_completed({"order_id": str(order.id), **DIAG})
    service.approve(order.id)
    service.on_repair_completed({"order_id": str(order.id)})
    invoice_id = uuid4()
    service.on_invoice_issued({"order_id": str(order.id), "invoice_id": str(invoice_id)})
    service.on_invoice_paid({"order_id": str(order.id), "invoice_id": str(invoice_id)})
    order = service.close(order.id, mileage=51010)
    assert order.status == OrderStatus.CLOSED and order.invoice_id == invoice_id
    assert publisher.keys() == ["order.created", "order.approved", "order.completed", "order.closed"]


def test_close_requires_payment(ctx):
    service, _, data = ctx
    order = service.create_order(data)
    with pytest.raises(ConflictError):
        service.close(order.id)


def test_repeated_diagnostics_event_is_ignored(ctx):
    service, _, data = ctx
    order = service.create_order(data)
    service.on_diagnostics_completed({"order_id": str(order.id), **DIAG})
    service.approve(order.id, ["W-02"])
    service.on_diagnostics_completed({"order_id": str(order.id), **DIAG})
    assert service.get_order(order.id).status == OrderStatus.APPROVED
