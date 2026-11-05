from uuid import uuid4

import pytest

from app.messaging import MemoryPublisher
from app.models.invoice import InvoiceStatus
from app.repositories.local_invoice_repo import InvoiceRepo
from app.services.invoice_service import InvoiceService

EVENT = {"works": [{"code": "W-01", "name": "Замена колодок", "price": 2500}],
         "parts": [{"sku": "BP-001", "name": "Колодки", "qty": 2, "price": 3500}]}


@pytest.fixture()
def service():
    return InvoiceService(InvoiceRepo(), MemoryPublisher())


def issue(service):
    order_id = uuid4()
    service.on_order_completed({"order_id": str(order_id), "client_id": str(uuid4()), **EVENT})
    return service.list(order_id=order_id)[0]


def test_total_is_works_plus_parts(service):
    invoice = issue(service)
    assert invoice.total == 2500 + 2 * 3500
    assert [line.kind for line in invoice.lines] == ["work", "part"]
    assert service.publisher.keys() == ["invoice.issued"]


def test_one_invoice_per_order(service):
    order_id, client_id = uuid4(), str(uuid4())
    service.on_order_completed({"order_id": str(order_id), "client_id": client_id, **EVENT})
    service.on_order_completed({"order_id": str(order_id), "client_id": client_id, **EVENT})
    assert len(service.list(order_id=order_id)) == 1


def test_payment_marks_invoice_paid_once(service):
    invoice = issue(service)
    payment = {"invoice_id": str(invoice.id), "payment_id": str(uuid4())}
    service.on_payment_succeeded(payment)
    service.on_payment_succeeded(payment)
    assert service.get(invoice.id).status == InvoiceStatus.PAID
    assert service.publisher.keys().count("invoice.paid") == 1
