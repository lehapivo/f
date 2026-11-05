from uuid import uuid4

import pytest

from app.errors import ConflictError
from app.messaging import MemoryPublisher
from app.models.repair import PartsStatus, RepairStatus
from app.repositories.local_repair_repo import PartsStateRepo, RepairRepo
from app.services.repair_service import RepairService

WORKS = [{"code": "W-01", "name": "Замена колодок", "price": 2500}]
PARTS = [{"sku": "BP-001", "name": "Колодки", "qty": 1, "price": 3500}]


@pytest.fixture()
def ctx():
    service = RepairService(RepairRepo(), PartsStateRepo(), MemoryPublisher())
    order_id = uuid4()
    service.on_order_approved({"order_id": str(order_id), "vehicle_id": str(uuid4()), "works": WORKS, "parts": PARTS})
    return service, order_id, service.list(order_id=order_id)[0].id


def test_repair_planned_from_approved_order(ctx):
    service, order_id, repair_id = ctx
    repair = service.get(repair_id)
    assert repair.status == RepairStatus.PLANNED and repair.parts_status == PartsStatus.PENDING


def test_cannot_start_without_parts(ctx):
    service, order_id, repair_id = ctx
    service.on_parts_shortage({"order_id": str(order_id)})
    with pytest.raises(ConflictError) as err:
        service.start(repair_id, "Петров")
    assert err.value.code == "parts_not_ready"


def test_start_and_complete(ctx):
    service, order_id, repair_id = ctx
    service.on_parts_reserved({"order_id": str(order_id)})
    assert service.start(repair_id, "Петров").status == RepairStatus.IN_PROGRESS
    repair = service.complete(repair_id, "Колодки заменены")
    assert repair.status == RepairStatus.COMPLETED
    assert service.publisher.keys() == ["repair.started", "repair.completed"]


def test_repeated_completion(ctx):
    service, order_id, repair_id = ctx
    service.on_parts_reserved({"order_id": str(order_id)})
    service.start(repair_id, "Петров")
    service.complete(repair_id)
    with pytest.raises(ConflictError) as err:
        service.complete(repair_id)
    assert err.value.code == "already_completed"


def test_late_shortage_does_not_override_reserved(ctx):
    service, order_id, repair_id = ctx
    service.on_parts_reserved({"order_id": str(order_id)})
    service.on_parts_shortage({"order_id": str(order_id)})
    assert service.get(repair_id).parts_status == PartsStatus.RESERVED


def test_repair_without_parts_can_start():
    service = RepairService(RepairRepo(), PartsStateRepo(), MemoryPublisher())
    order_id = uuid4()
    service.on_order_approved({"order_id": str(order_id), "vehicle_id": str(uuid4()), "works": WORKS, "parts": []})
    repair_id = service.list(order_id=order_id)[0].id
    assert service.start(repair_id, "Иванов").mechanic == "Иванов"
