"""Бизнес-логика склада: остатки, резервы, заказ недостающих запчастей."""
from datetime import datetime, timezone
from uuid import UUID

from app.errors import ConflictError
from app.models.stock import (Part, PartCreate, PartOut, PurchaseOrder, PurchaseStatus, Reservation,
                              ReservationStatus)


class StockService:
    def __init__(self, parts, reservations, purchases, publisher) -> None:
        self.parts = parts
        self.reservations = reservations
        self.purchases = purchases
        self.publisher = publisher

    @staticmethod
    def view(part: Part) -> PartOut:
        return PartOut(**part.model_dump(), available=part.quantity - part.reserved)

    def add_part(self, data: PartCreate) -> PartOut:
        if self.parts.exists(data.sku):
            raise ConflictError("part_exists", f"Part {data.sku} already exists")
        return self.view(self.parts.add(Part(**data.model_dump())))

    def get_part(self, sku: str) -> PartOut:
        return self.view(self.parts.get(sku))

    def list_parts(self, low_stock: bool = False, offset=0, count=20) -> list[PartOut]:
        items = [self.view(p) for p in self.parts.list(offset=0, count=10_000)]
        if low_stock:
            items = [p for p in items if p.available <= p.min_quantity]
        return items[offset:offset + count]

    def list_purchases(self, status: str | None = None, offset=0, count=20) -> list[PurchaseOrder]:
        return self.purchases.list(offset=offset, count=count, status=status)

    def receive(self, purchase_id: UUID) -> PurchaseOrder:
        purchase = self.purchases.get(purchase_id)
        if purchase.status == PurchaseStatus.RECEIVED:
            raise ConflictError("already_received", "Purchase order already received")
        part = self.parts.get(purchase.sku)
        part.quantity += purchase.qty
        self.parts.update(part)
        purchase.status = PurchaseStatus.RECEIVED
        purchase.received_at = datetime.now(timezone.utc)
        self.purchases.update(purchase)
        self.publisher.publish("parts.received", {"sku": part.sku, "qty": purchase.qty})
        # поставка может закрыть ожидающие резервы
        for reservation in self.reservations.list(count=10_000, sku=part.sku, status="waiting"):
            if self._try_reserve(reservation.sku, reservation.qty):
                reservation.status = ReservationStatus.RESERVED
                self.reservations.update(reservation)
                self._publish_if_complete(reservation.order_id)
        return purchase

    # событие order.approved: зарезервировать запчасти по согласованному заказ-наряду
    def on_order_approved(self, event: dict) -> None:
        order_id = UUID(event["order_id"])
        if self.reservations.list(count=1, order_id=order_id):
            return                                            # повторная доставка
        missing = []
        for line in event.get("parts", []):
            sku, qty = line["sku"], line["qty"]
            if self._try_reserve(sku, qty):
                status = ReservationStatus.RESERVED
            else:
                status = ReservationStatus.WAITING
                part = self.parts.get(sku)
                shortage = qty - max(part.quantity - part.reserved, 0)
                self.purchases.add(PurchaseOrder(sku=sku, qty=shortage, order_id=order_id))
                missing.append({"sku": sku, "qty": shortage})
            self.reservations.add(Reservation(order_id=order_id, sku=sku, qty=qty, status=status))
        if missing:
            self.publisher.publish("parts.shortage", {"order_id": order_id, "missing": missing})
        else:
            self.publisher.publish("parts.reserved", {"order_id": order_id})

    # событие repair.completed: списать выданные запчасти
    def on_repair_completed(self, event: dict) -> None:
        order_id = UUID(event["order_id"])
        issued = []
        for reservation in self.reservations.list(count=10_000, order_id=order_id, status="reserved"):
            part = self.parts.get(reservation.sku)
            part.quantity -= reservation.qty
            part.reserved -= reservation.qty
            self.parts.update(part)
            reservation.status = ReservationStatus.ISSUED
            self.reservations.update(reservation)
            issued.append({"sku": reservation.sku, "qty": reservation.qty})
        if issued:
            self.publisher.publish("parts.issued", {"order_id": order_id, "parts": issued})

    def _try_reserve(self, sku: str, qty: int) -> bool:
        part = self.parts.get(sku)
        if part.quantity - part.reserved < qty:
            return False
        part.reserved += qty
        self.parts.update(part)
        return True

    def _publish_if_complete(self, order_id: UUID) -> None:
        pending = self.reservations.list(count=1, order_id=order_id, status="waiting")
        if not pending:
            self.publisher.publish("parts.reserved", {"order_id": order_id})
