import pytest
from pydantic import ValidationError

from app.models.stock import PartCreate, PurchaseOrder, PurchaseStatus


def test_negative_price_rejected():
    with pytest.raises(ValidationError):
        PartCreate(sku="BP-001", name="Колодки", price=-1, quantity=1)


def test_purchase_order_defaults():
    po = PurchaseOrder(sku="BP-001", qty=3)
    assert po.status == PurchaseStatus.ORDERED and po.received_at is None
