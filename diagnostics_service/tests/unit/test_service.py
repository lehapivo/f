from uuid import uuid4

import pytest

from app.errors import BusinessRuleError, ConflictError
from app.messaging import MemoryPublisher
from app.models.diagnostic import DiagnosticResult, DiagnosticStatus
from app.repositories.local_diagnostic_repo import DiagnosticRepo
from app.services.diagnostic_service import DiagnosticService


class FakeWarehouse:
    parts = {"BP-001": {"sku": "BP-001", "name": "Колодки", "price": 3500, "available": 4},
             "BD-002": {"sku": "BD-002", "name": "Диск", "price": 6200, "available": 0}}

    def get_part(self, sku):
        return self.parts.get(sku)


RESULT = DiagnosticResult(faults=["Износ колодок"],
                          works=[{"code": "W-01", "name": "Замена колодок", "price": 2500}],
                          parts=[{"sku": "BP-001", "qty": 1}, {"sku": "BD-002", "qty": 2}])


@pytest.fixture()
def ctx():
    service = DiagnosticService(DiagnosticRepo(), MemoryPublisher(), FakeWarehouse())
    order_id = uuid4()
    service.on_order_created({"order_id": str(order_id), "vehicle_id": str(uuid4()), "complaint": "Скрип"})
    return service, order_id


def test_order_created_opens_diagnostic_once(ctx):
    service, order_id = ctx
    service.on_order_created({"order_id": str(order_id), "vehicle_id": str(uuid4()), "complaint": "Скрип"})
    assert len(service.list(order_id=order_id)) == 1


def test_complete_enriches_parts_from_warehouse(ctx):
    service, order_id = ctx
    diagnostic = service.complete(service.list(order_id=order_id)[0].id, RESULT)
    assert diagnostic.status == DiagnosticStatus.COMPLETED
    assert [(p.price, p.in_stock) for p in diagnostic.parts] == [(3500, True), (6200, False)]
    key, body = service.publisher.sent[-1]
    assert key == "diagnostics.completed" and body["order_id"] == order_id


def test_unknown_part_rejected(ctx):
    service, order_id = ctx
    bad = DiagnosticResult(faults=["x"], works=[{"code": "W", "name": "x", "price": 1}], parts=[{"sku": "NO", "qty": 1}])
    with pytest.raises(BusinessRuleError):
        service.complete(service.list(order_id=order_id)[0].id, bad)


def test_complete_twice_conflict(ctx):
    service, order_id = ctx
    diagnostic_id = service.list(order_id=order_id)[0].id
    service.complete(diagnostic_id, RESULT)
    with pytest.raises(ConflictError):
        service.complete(diagnostic_id, RESULT)
