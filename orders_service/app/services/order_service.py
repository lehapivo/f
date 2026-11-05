"""Бизнес-логика заказ-нарядов."""
from datetime import datetime, timezone
from uuid import UUID

from app.errors import BusinessRuleError, ConflictError
from app.models.order import Order, OrderCreate, OrderStatus, PartLine, Work


class OrderService:
    def __init__(self, repo, publisher, clients) -> None:
        self.repo = repo
        self.publisher = publisher
        self.clients = clients

    # ---- команды мастера-приемщика (HTTP) ----
    def create_order(self, data: OrderCreate) -> Order:
        vehicle = self.clients.get_vehicle(data.vehicle_id)          # синхронный вызов
        if vehicle is None:
            raise BusinessRuleError("vehicle_not_found", f"Vehicle {data.vehicle_id} not found")
        if UUID(vehicle["client_id"]) != data.client_id:
            raise BusinessRuleError("vehicle_of_other_client", "Vehicle belongs to another client")
        if data.mileage < vehicle["mileage"]:
            raise BusinessRuleError("mileage_decreased", f"Mileage is less than {vehicle['mileage']}")
        order = self.repo.add(Order(**data.model_dump()))
        self.publisher.publish("order.created", {
            "order_id": order.id, "client_id": order.client_id, "vehicle_id": order.vehicle_id,
            "appointment_id": order.appointment_id, "complaint": order.complaint})
        return order

    def get_order(self, order_id: UUID) -> Order:
        return self.repo.get(order_id)

    def list_orders(self, status=None, client_id=None, offset=0, count=20) -> list[Order]:
        return self.repo.list(offset=offset, count=count, status=status, client_id=client_id)

    def approve(self, order_id: UUID, work_codes: list[str] | None = None) -> Order:
        order = self.repo.get(order_id)
        if order.status != OrderStatus.DIAGNOSED:
            raise ConflictError("invalid_status", f"Order is {order.status}, expected diagnosed")
        if work_codes is not None:
            unknown = set(work_codes) - {w.code for w in order.works}
            if unknown:
                raise BusinessRuleError("unknown_work", f"Unknown works: {sorted(unknown)}")
            order.works = [w for w in order.works if w.code in work_codes]
        order.estimate = self._estimate(order.works, order.parts)
        order.status = OrderStatus.APPROVED
        self.repo.update(order)
        self.publisher.publish("order.approved", {
            "order_id": order.id, "vehicle_id": order.vehicle_id,
            "works": [w.model_dump() for w in order.works],
            "parts": [p.model_dump() for p in order.parts]})
        return order

    def close(self, order_id: UUID, mileage: int | None = None) -> Order:
        order = self.repo.get(order_id)
        if order.status != OrderStatus.PAID:
            raise ConflictError("invalid_status", f"Order is {order.status}, expected paid")
        if mileage is not None:
            if mileage < order.mileage:
                raise BusinessRuleError("mileage_decreased", "Mileage is less than at acceptance")
            order.mileage = mileage
        order.status = OrderStatus.CLOSED
        order.closed_at = datetime.now(timezone.utc)
        self.repo.update(order)
        self.publisher.publish("order.closed", {
            "order_id": order.id, "client_id": order.client_id,
            "vehicle_id": order.vehicle_id, "mileage": order.mileage})
        return order

    # ---- реакции на события других сервисов (RabbitMQ) ----
    def on_diagnostics_completed(self, event: dict) -> None:
        order = self.repo.get(UUID(event["order_id"]))
        if order.status != OrderStatus.CREATED:
            return                                       # повторная доставка
        order.faults = list(event.get("faults", []))
        order.works = [Work(**w) for w in event.get("works", [])]
        order.parts = [PartLine(**p) for p in event.get("parts", [])]
        order.estimate = self._estimate(order.works, order.parts)
        order.status = OrderStatus.DIAGNOSED
        self.repo.update(order)

    def on_repair_completed(self, event: dict) -> None:
        order = self.repo.get(UUID(event["order_id"]))
        if order.status != OrderStatus.APPROVED:
            return
        order.status = OrderStatus.READY
        self.repo.update(order)
        self.publisher.publish("order.completed", {
            "order_id": order.id, "client_id": order.client_id,
            "works": [w.model_dump() for w in order.works],
            "parts": [p.model_dump() for p in order.parts]})

    def on_invoice_issued(self, event: dict) -> None:
        order = self.repo.get(UUID(event["order_id"]))
        order.invoice_id = UUID(event["invoice_id"])
        self.repo.update(order)

    def on_invoice_paid(self, event: dict) -> None:
        order = self.repo.get(UUID(event["order_id"]))
        if order.status == OrderStatus.READY:
            order.status = OrderStatus.PAID
            self.repo.update(order)

    @staticmethod
    def _estimate(works: list[Work], parts: list[PartLine]) -> int:
        return sum(w.price for w in works) + sum(p.price * p.qty for p in parts)
