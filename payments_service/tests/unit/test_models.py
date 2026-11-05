from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.payment import PaymentCreate


def test_amount_must_be_positive():
    with pytest.raises(ValidationError):
        PaymentCreate(invoice_id=uuid4(), amount=0, method="card")


def test_unknown_method_rejected():
    with pytest.raises(ValidationError):
        PaymentCreate(invoice_id=uuid4(), amount=100, method="crypto")
