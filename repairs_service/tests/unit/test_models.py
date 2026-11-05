from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.repair import Repair, RepairStart, RepairStatus


def test_new_repair_is_planned():
    assert Repair(order_id=uuid4(), vehicle_id=uuid4()).status == RepairStatus.PLANNED


def test_mechanic_required():
    with pytest.raises(ValidationError):
        RepairStart(mechanic="")
