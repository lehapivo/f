from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.order import Order, OrderCreate, OrderStatus, PartLine


def test_new_order_has_created_status():
    order = Order(client_id=uuid4(), vehicle_id=uuid4(), complaint="Шум", mileage=1000)
    assert order.status == OrderStatus.CREATED
    assert order.estimate == 0 and order.works == []


def test_complaint_required():
    with pytest.raises(ValidationError):
        OrderCreate(client_id=uuid4(), vehicle_id=uuid4(), complaint="", mileage=10)


def test_negative_mileage_rejected():
    with pytest.raises(ValidationError):
        OrderCreate(client_id=uuid4(), vehicle_id=uuid4(), complaint="Шум", mileage=-1)


def test_part_quantity_must_be_positive():
    with pytest.raises(ValidationError):
        PartLine(sku="BP-001", qty=0)
