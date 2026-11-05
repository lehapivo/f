from uuid import uuid4

import pytest

from app.models.invoice import Invoice, InvoiceLine
from app.repositories.db_invoice_repo import InvoiceRepo

pytestmark = pytest.mark.integration


def test_invoice_lines_roundtrip(db_session):
    repo = InvoiceRepo(db_session)
    invoice = repo.add(Invoice(order_id=uuid4(), client_id=uuid4(), total=9500,
                               lines=[InvoiceLine(kind="work", name="ТО", qty=1, price=9500, amount=9500)]))
    saved = repo.get(invoice.id)
    assert saved.total == 9500 and saved.lines[0].name == "ТО"


def test_filter_by_status(db_session):
    repo = InvoiceRepo(db_session)
    repo.add(Invoice(order_id=uuid4(), client_id=uuid4(), total=1))
    repo.add(Invoice(order_id=uuid4(), client_id=uuid4(), total=2, status="paid"))
    assert [i.total for i in repo.list(status="paid")] == [2]
