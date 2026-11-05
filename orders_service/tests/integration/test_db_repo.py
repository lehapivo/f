from uuid import uuid4

import pytest

from app.errors import NotFoundError
from app.models.order import Order, OrderStatus, Work
from app.repositories.db_order_repo import OrderRepo

pytestmark = pytest.mark.integration


def make_order(**kw) -> Order:
    return Order(client_id=uuid4(), vehicle_id=uuid4(), complaint="Шум", mileage=100, **kw)


def test_create_and_get(db_session):
    repo = OrderRepo(db_session)
    order = repo.add(make_order(works=[Work(code="W-01", name="Диагностика", price=1500)]))
    found = repo.get(order.id)
    assert found.id == order.id
    assert found.works[0].price == 1500
    assert found.status == OrderStatus.CREATED


def test_update_status(db_session):
    repo = OrderRepo(db_session)
    order = repo.add(make_order())
    order.status = OrderStatus.DIAGNOSED
    order.estimate = 7800
    repo.update(order)
    assert repo.get(order.id).estimate == 7800


def test_list_with_filters_and_pagination(db_session):
    repo = OrderRepo(db_session)
    client_id = uuid4()
    for _ in range(3):
        repo.add(Order(client_id=client_id, vehicle_id=uuid4(), complaint="ТО", mileage=1))
    repo.add(make_order(status=OrderStatus.CLOSED))
    assert len(repo.list(client_id=client_id)) == 3
    assert len(repo.list(client_id=client_id, offset=2, count=10)) == 1
    assert len(repo.list(status="closed")) == 1


def test_missing_order(db_session):
    with pytest.raises(NotFoundError):
        OrderRepo(db_session).get(uuid4())
