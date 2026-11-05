from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.appointment import Appointment, AppointmentCreate, AppointmentStatus


def test_default_status():
    a = Appointment(client_id=uuid4(), vehicle_id=uuid4(), scheduled_at=datetime(2030, 1, 1, 10), reason="ТО")
    assert a.status == AppointmentStatus.CREATED and a.order_id is None


def test_reason_required():
    with pytest.raises(ValidationError):
        AppointmentCreate(client_id=uuid4(), vehicle_id=uuid4(), scheduled_at=datetime(2030, 1, 1), reason="")
