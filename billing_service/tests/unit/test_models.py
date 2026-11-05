from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus


def test_new_invoice_is_issued():
    assert Invoice(order_id=uuid4(), client_id=uuid4()).status == InvoiceStatus.ISSUED


def test_line_quantity_positive():
    with pytest.raises(ValidationError):
        InvoiceLine(kind="part", name="x", qty=0, price=1, amount=0)
