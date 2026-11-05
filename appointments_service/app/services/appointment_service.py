"""Бизнес-логика записи на обслуживание."""
from datetime import date, datetime, timezone
from uuid import UUID

from app.errors import BusinessRuleError, ConflictError
from app.models.appointment import Appointment, AppointmentCreate, AppointmentStatus


class AppointmentService:
    def __init__(self, repo, publisher, clients) -> None:
        self.repo = repo
        self.publisher = publisher
        self.clients = clients

    def create(self, data: AppointmentCreate) -> Appointment:
        scheduled_at = data.scheduled_at if data.scheduled_at.tzinfo else data.scheduled_at.replace(tzinfo=timezone.utc)
        if scheduled_at <= datetime.now(timezone.utc):
            raise BusinessRuleError("time_in_past", "Appointment time must be in the future")
        vehicle = self.clients.get_vehicle(data.vehicle_id)         # синхронный вызов
        if vehicle is None:
            raise BusinessRuleError("vehicle_not_found", f"Vehicle {data.vehicle_id} not found")
        if UUID(vehicle["client_id"]) != data.client_id:
            raise BusinessRuleError("vehicle_of_other_client", "Vehicle belongs to another client")
        if self.repo.find_active_at(scheduled_at):
            raise ConflictError("slot_taken", "This time slot is already taken")
        appointment = self.repo.add(Appointment(**{**data.model_dump(), "scheduled_at": scheduled_at}))
        self.publisher.publish("appointment.created", {
            "appointment_id": appointment.id, "client_id": appointment.client_id,
            "vehicle_id": appointment.vehicle_id, "scheduled_at": appointment.scheduled_at})
        return appointment

    def get(self, appointment_id: UUID) -> Appointment:
        return self.repo.get(appointment_id)

    def list(self, day: date | None = None, status: str | None = None, offset=0, count=20):
        return self.repo.list_by_day(day, status, offset, count)

    def confirm(self, appointment_id: UUID) -> Appointment:
        return self._change(appointment_id, AppointmentStatus.CONFIRMED, {"created"}, "appointment.confirmed")

    def cancel(self, appointment_id: UUID) -> Appointment:
        return self._change(appointment_id, AppointmentStatus.CANCELLED, {"created", "confirmed"},
                            "appointment.cancelled")

    def _change(self, appointment_id, new_status, allowed, event) -> Appointment:
        appointment = self.repo.get(appointment_id)
        if appointment.status not in allowed:
            raise ConflictError("invalid_status", f"Appointment is {appointment.status}")
        appointment.status = new_status
        self.repo.update(appointment)
        self.publisher.publish(event, {"appointment_id": appointment.id, "status": appointment.status})
        return appointment

    # событие order.created: клиент приехал по записи
    def on_order_created(self, event: dict) -> None:
        if not event.get("appointment_id"):
            return
        appointment = self.repo.get(UUID(event["appointment_id"]))
        if appointment.status in ("created", "confirmed"):
            appointment.status = AppointmentStatus.ARRIVED
            appointment.order_id = UUID(event["order_id"])
            self.repo.update(appointment)
