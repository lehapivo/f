from uuid import uuid4

import pytest

from app.errors import ConflictError, NotFoundError
from app.messaging import MemoryPublisher
from app.models.stock import PartCreate
from app.repositories.local_stock_repo import PartRepo, PurchaseOrderRepo, ReservationRepo
from app.services.stock_service import StockService


@pytest.fixture()
def service():
    s = StockService(PartRepo(), ReservationRepo(), PurchaseOrderRepo(), MemoryPublisher())
    s.add_part(PartCreate(sku="BP-001", name="Колодки", price=3500, quantity=4))
    s.add_part(PartCreate(sku="BD-002", name="Диск", price=6200, quantity=1))
    return s


def approved(order_id, *lines):
    return {"order_id": str(order_id), "parts": [{"sku": s, "qty": q} for s, q in lines]}


def test_reserve_when_in_stock(service):
    order_id = uuid4()
    service.on_order_approved(approved(order_id, ("BP-001", 2)))
    part = service.get_part("BP-001")
    assert (part.reserved, part.available) == (2, 2)
    assert service.publisher.keys() == ["parts.reserved"]


def test_shortage_creates_purchase_order(service):
    order_id = uuid4()
    service.on_order_approved(approved(order_id, ("BP-001", 1), ("BD-002", 2)))
    assert service.publisher.sent[-1] == ("parts.shortage", {"order_id": order_id,
                                                             "missing": [{"sku": "BD-002", "qty": 1}]})
    purchase = service.list_purchases("ordered")[0]
    assert (purchase.sku, purchase.qty) == ("BD-002", 1)


def test_receive_completes_waiting_reservation(service):
    order_id = uuid4()
    service.on_order_approved(approved(order_id, ("BD-002", 2)))
    service.receive(service.list_purchases("ordered")[0].id)
    assert service.get_part("BD-002").reserved == 2
    assert service.publisher.keys()[-1] == "parts.reserved"


def test_repair_completed_writes_off_parts(service):
    order_id = uuid4()
    service.on_order_approved(approved(order_id, ("BP-001", 2)))
    service.on_repair_completed({"order_id": str(order_id)})
    part = service.get_part("BP-001")
    assert (part.quantity, part.reserved) == (2, 0)


def test_low_stock_and_errors(service):
    assert [p.sku for p in service.list_parts(low_stock=True)] == ["BD-002"]
    with pytest.raises(ConflictError):
        service.add_part(PartCreate(sku="BP-001", name="Дубль", price=1, quantity=1))
    with pytest.raises(NotFoundError):
        service.get_part("NOPE")


def test_repeated_approval_is_ignored(service):
    order_id = uuid4()
    service.on_order_approved(approved(order_id, ("BP-001", 2)))
    service.on_order_approved(approved(order_id, ("BP-001", 2)))
    assert service.get_part("BP-001").reserved == 2
