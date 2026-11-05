from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.models.appointment import Appointment
from app.repositories.base import DbRepository
from app.schemas.appointment import AppointmentDB


class AppointmentRepo(DbRepository[Appointment]):
    model = Appointment
    table = AppointmentDB

    def list_by_day(self, day: date | None, status: str | None, offset: int, count: int) -> list[Appointment]:
        query = select(AppointmentDB)
        if day is not None:
            start = datetime.combine(day, time.min, tzinfo=timezone.utc)
            query = query.where(AppointmentDB.scheduled_at >= start,
                                AppointmentDB.scheduled_at < start + timedelta(days=1))
        if status is not None:
            query = query.where(AppointmentDB.status == status)
        rows = self.db.scalars(query.order_by(AppointmentDB.scheduled_at).offset(offset).limit(count)).all()
        return [Appointment.model_validate(r) for r in rows]

    def find_active_at(self, moment) -> Appointment | None:
        row = self.db.scalars(select(AppointmentDB).where(
            AppointmentDB.scheduled_at == moment,
            AppointmentDB.status.in_(["created", "confirmed"]))).first()
        return Appointment.model_validate(row) if row else None
