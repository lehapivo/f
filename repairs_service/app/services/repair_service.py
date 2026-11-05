"""Бизнес-логика ремонта."""
from datetime import datetime, timezone
from uuid import UUID

from app.errors import ConflictError
from app.models.repair import PartsState, PartsStatus, Repair, RepairOut, RepairStatus


class RepairService:
    def __init__(self, repairs, parts_states, publisher) -> None:
        self.repairs = repairs
        self.parts_states = parts_states
        self.publisher = publisher

    def _view(self, repair: Repair) -> RepairOut:
        if not repair.parts:
            parts_status = PartsStatus.RESERVED
        else:
            state = self.parts_states.find(repair.order_id)
            parts_status = state.status if state else PartsStatus.PENDING
        return RepairOut(**repair.model_dump(), parts_status=parts_status)

    def list(self, status=None, order_id=None, offset=0, count=20) -> list[RepairOut]:
        return [self._view(r) for r in self.repairs.list(offset=offset, count=count, status=status, order_id=order_id)]

    def get(self, repair_id: UUID) -> RepairOut:
        return self._view(self.repairs.get(repair_id))

    def start(self, repair_id: UUID, mechanic: str) -> RepairOut:
        repair = self.get(repair_id)
        if repair.status != RepairStatus.PLANNED:
            raise ConflictError("invalid_status", f"Repair is {repair.status}")
        if repair.parts_status != PartsStatus.RESERVED:
            raise ConflictError("parts_not_ready", f"Parts are {repair.parts_status}")
        repair.status = RepairStatus.IN_PROGRESS
        repair.mechanic = mechanic
        repair.started_at = datetime.now(timezone.utc)
        self.repairs.update(Repair(**repair.model_dump(exclude={"parts_status"})))
        self.publisher.publish("repair.started", {"repair_id": repair.id, "order_id": repair.order_id,
                                                  "mechanic": mechanic})
        return repair

    def complete(self, repair_id: UUID, note: str | None = None) -> RepairOut:
        repair = self.repairs.get(repair_id)
        if repair.status == RepairStatus.COMPLETED:
            raise ConflictError("already_completed", "Repair already completed")
        if repair.status != RepairStatus.IN_PROGRESS:
            raise ConflictError("invalid_status", f"Repair is {repair.status}")
        repair.status = RepairStatus.COMPLETED
        repair.note = note
        repair.completed_at = datetime.now(timezone.utc)
        self.repairs.update(repair)
        self.publisher.publish("repair.completed", {
            "repair_id": repair.id, "order_id": repair.order_id, "vehicle_id": repair.vehicle_id,
            "works": [w.model_dump() for w in repair.works], "parts": [p.model_dump() for p in repair.parts]})
        return self._view(repair)

    # событие order.approved: работы согласованы, ремонт планируется
    def on_order_approved(self, event: dict) -> None:
        order_id = UUID(event["order_id"])
        if self.repairs.list(count=1, order_id=order_id):
            return
        self.repairs.add(Repair(order_id=order_id, vehicle_id=UUID(event["vehicle_id"]),
                                works=event.get("works", []), parts=event.get("parts", [])))

    # события склада: parts.reserved / parts.shortage
    def on_parts_reserved(self, event: dict) -> None:
        self._set_parts(event, PartsStatus.RESERVED)

    def on_parts_shortage(self, event: dict) -> None:
        state = self.parts_states.find(UUID(event["order_id"]))
        if state is None or state.status != PartsStatus.RESERVED:
            self._set_parts(event, PartsStatus.SHORTAGE)

    def _set_parts(self, event: dict, status: PartsStatus) -> None:
        self.parts_states.update(PartsState(order_id=UUID(event["order_id"]), status=status))
