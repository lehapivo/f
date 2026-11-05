from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.appointment import Appointment
from app.repositories.db_appointment_repo import AppointmentRepo

pytestmark = pytest.mark.integration


def make(hour: int, day: int = 10, **kw) -> Appointment:
    return Appointment(client_id=uuid4(), vehicle_id=uuid4(), reason="ТО",
                       scheduled_at=datetime(2030, 3, day, hour, tzinfo=timezone.utc), **kw)


def test_list_by_day_sorted(db_session):
    repo = AppointmentRepo(db_session)
    for hour in (15, 9, 12):
        repo.add(make(hour))
    repo.add(make(10, day=11))
    hours = [a.scheduled_at.hour for a in repo.list_by_day(datetime(2030, 3, 10).date(), None, 0, 10)]
    assert hours == [9, 12, 15]


def test_find_active_slot(db_session):
    repo = AppointmentRepo(db_session)
    a = repo.add(make(9))
    assert repo.find_active_at(a.scheduled_at).id == a.id
    a.status = "cancelled"
    repo.update(a)
    assert repo.find_active_at(a.scheduled_at) is None
