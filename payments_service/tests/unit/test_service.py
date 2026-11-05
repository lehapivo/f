from uuid import uuid4

import pytest

from app.errors import BusinessRuleError, ConflictError
from app.gateways.payment_provider import PaymentProvider
from app.messaging import MemoryPublisher
from app.models.payment import PaymentCreate, PaymentStatus
from app.repositories.local_payment_repo import PaymentRepo
from app.services.payment_service import PaymentService


class FakeBilling:
    def __init__(self):
        self.invoices = {}

    def get_invoice(self, invoice_id):
        return self.invoices.get(invoice_id)


@pytest.fixture()
def ctx():
    billing = FakeBilling()
    service = PaymentService(PaymentRepo(), MemoryPublisher(), billing, PaymentProvider())
    invoice_id = uuid4()
    billing.invoices[invoice_id] = {"id": str(invoice_id), "order_id": str(uuid4()), "total": 9500, "status": "issued"}
    return service, billing, invoice_id


def test_successful_payment(ctx):
    service, _, invoice_id = ctx
    payment = service.pay(PaymentCreate(invoice_id=invoice_id, amount=9500, method="card"))
    assert payment.status == PaymentStatus.SUCCEEDED and payment.external_id.startswith("PS-")
    assert service.publisher.keys() == ["payment.succeeded"]


def test_amount_mismatch(ctx):
    service, _, invoice_id = ctx
    with pytest.raises(BusinessRuleError) as err:
        service.pay(PaymentCreate(invoice_id=invoice_id, amount=100, method="cash"))
    assert err.value.code == "amount_mismatch"


def test_double_payment_conflict(ctx):
    service, _, invoice_id = ctx
    service.pay(PaymentCreate(invoice_id=invoice_id, amount=9500, method="cash"))
    with pytest.raises(ConflictError):
        service.pay(PaymentCreate(invoice_id=invoice_id, amount=9500, method="cash"))


def test_unknown_invoice(ctx):
    service, _, _ = ctx
    with pytest.raises(BusinessRuleError):
        service.pay(PaymentCreate(invoice_id=uuid4(), amount=1, method="cash"))


def test_card_limit_declined(ctx):
    service, billing, _ = ctx
    invoice_id = uuid4()
    billing.invoices[invoice_id] = {"order_id": str(uuid4()), "total": 2_000_000, "status": "issued"}
    payment = service.pay(PaymentCreate(invoice_id=invoice_id, amount=2_000_000, method="card"))
    assert payment.status == PaymentStatus.DECLINED and payment.decline_reason == "limit_exceeded"
    assert service.publisher.keys() == ["payment.declined"]
