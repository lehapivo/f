from uuid import uuid4

import pytest

from app.models.payment import Payment
from app.repositories.db_payment_repo import PaymentRepo

pytestmark = pytest.mark.integration


def test_payment_roundtrip_and_filter(db_session):
    repo = PaymentRepo(db_session)
    invoice_id = uuid4()
    payment = repo.add(Payment(invoice_id=invoice_id, amount=9500, method="card", status="succeeded",
                               external_id="PS-TEST"))
    repo.add(Payment(invoice_id=uuid4(), amount=10, method="cash", status="succeeded"))
    assert repo.get(payment.id).external_id == "PS-TEST"
    assert [p.id for p in repo.list(invoice_id=invoice_id, status="succeeded")] == [payment.id]
