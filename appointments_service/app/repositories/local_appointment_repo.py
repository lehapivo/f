from datetime import date

from app.models.appointment import Appointment
from app.repositories.base import LocalRepository


class AppointmentRepo(LocalRepository[Appointment]):
    model = Appointment

    def list_by_day(self, day: date | None, status: str | None, offset: int, count: int) -> list[Appointment]:
        items = [a for a in self._items.values()
                 if (day is None or a.scheduled_at.date() == day) and (status is None or a.status == status)]
        items.sort(key=lambda a: a.scheduled_at)
        return [a.model_copy(deep=True) for a in items[offset:offset + count]]

    def find_active_at(self, moment) -> Appointment | None:
        return next((a for a in self._items.values()
                     if a.scheduled_at == moment and a.status in ("created", "confirmed")), None)
