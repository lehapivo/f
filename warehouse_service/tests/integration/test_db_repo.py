from uuid import uuid4

import pytest

from app.models.stock import Part, PurchaseOrder, Reservation
from app.repositories.db_stock_repo import PartRepo, PurchaseOrderRepo, ReservationRepo

pytestmark = pytest.mark.integration


def test_part_by_sku(db_session):
    repo = PartRepo(db_session)
    repo.add(Part(sku="OF-100", name="Фильтр масляный", price=650, quantity=12))
    assert repo.exists("OF-100") and not repo.exists("OF-999")
    part = repo.get("OF-100")
    part.reserved = 3
    repo.update(part)
    assert repo.get("OF-100").reserved == 3


def test_reservations_and_purchases_filters(db_session):
    reservations, purchases = ReservationRepo(db_session), PurchaseOrderRepo(db_session)
    order_id = uuid4()
    reservations.add(Reservation(order_id=order_id, sku="OF-100", qty=1, status="reserved"))
    reservations.add(Reservation(order_id=order_id, sku="AF-200", qty=1, status="waiting"))
    purchases.add(PurchaseOrder(sku="AF-200", qty=1, order_id=order_id))
    assert len(reservations.list(order_id=order_id, status="waiting")) == 1
    assert purchases.list(status="ordered")[0].sku == "AF-200"
