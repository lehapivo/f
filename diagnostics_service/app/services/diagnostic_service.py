"""Бизнес-логика диагностики."""
from datetime import datetime, timezone
from uuid import UUID

from app.errors import BusinessRuleError, ConflictError
from app.models.diagnostic import Diagnostic, DiagnosticResult, DiagnosticStatus, PartLine


class DiagnosticService:
    def __init__(self, repo, publisher, warehouse) -> None:
        self.repo = repo
        self.publisher = publisher
        self.warehouse = warehouse

    def list(self, status=None, order_id=None, offset=0, count=20) -> list[Diagnostic]:
        return self.repo.list(offset=offset, count=count, status=status, order_id=order_id)

    def get(self, diagnostic_id: UUID) -> Diagnostic:
        return self.repo.get(diagnostic_id)

    def complete(self, diagnostic_id: UUID, result: DiagnosticResult) -> Diagnostic:
        diagnostic = self.repo.get(diagnostic_id)
        if diagnostic.status != DiagnosticStatus.PENDING:
            raise ConflictError("already_completed", "Diagnostics already completed")
        parts = []
        for request in result.parts:
            part = self.warehouse.get_part(request.sku)               # синхронный вызов
            if part is None:
                raise BusinessRuleError("unknown_part", f"Part {request.sku} not found in warehouse")
            parts.append(PartLine(sku=request.sku, qty=request.qty, name=part["name"], price=part["price"],
                                  in_stock=part["available"] >= request.qty))
        diagnostic.faults = result.faults
        diagnostic.works = result.works
        diagnostic.parts = parts
        diagnostic.status = DiagnosticStatus.COMPLETED
        diagnostic.completed_at = datetime.now(timezone.utc)
        self.repo.update(diagnostic)
        self.publisher.publish("diagnostics.completed", {
            "diagnostic_id": diagnostic.id, "order_id": diagnostic.order_id, "faults": diagnostic.faults,
            "works": [w.model_dump() for w in diagnostic.works],
            "parts": [p.model_dump(include={"sku", "name", "qty", "price"}) for p in diagnostic.parts]})
        return diagnostic

    # событие order.created: автомобиль передан на диагностику
    def on_order_created(self, event: dict) -> None:
        order_id = UUID(event["order_id"])
        if self.repo.list(count=1, order_id=order_id):
            return
        self.repo.add(Diagnostic(order_id=order_id, vehicle_id=UUID(event["vehicle_id"]),
                                 complaint=event["complaint"]))
