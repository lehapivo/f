from uuid import uuid4

import pytest

from app.models.repair import PartsState, Repair, Work
from app.repositories.db_repair_repo import PartsStateRepo, RepairRepo

pytestmark = pytest.mark.integration


def test_repair_roundtrip(db_session):
    repo = RepairRepo(db_session)
    repair = repo.add(Repair(order_id=uuid4(), vehicle_id=uuid4(), works=[Work(code="W", name="ТО", price=3000)]))
    repair.status = "in_progress"
    repair.mechanic = "Петров"
    repo.update(repair)
    saved = repo.get(repair.id)
    assert saved.mechanic == "Петров" and saved.works[0].price == 3000


def test_parts_state_upsert(db_session):
    repo = PartsStateRepo(db_session)
    order_id = uuid4()
    assert repo.find(order_id) is None
    repo.update(PartsState(order_id=order_id, status="shortage"))
    repo.update(PartsState(order_id=order_id, status="reserved"))
    assert repo.find(order_id).status == "reserved"
