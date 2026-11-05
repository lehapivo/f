"""Бизнес-логика счетов: расчет итоговой стоимости и учет оплаты."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus


class InvoiceService:
    def __init__(self, repo, publisher) -> None:
        self.repo = repo
        self.publisher = publisher

    def list(self, order_id=None, client_id=None, status=None, offset=0, count=20) -> list[Invoice]:
        return self.repo.list(offset=offset, count=count, order_id=order_id, client_id=client_id, status=status)

    def get(self, invoice_id: UUID) -> Invoice:
        return self.repo.get(invoice_id)

    @staticmethod
    def build_lines(works: list[dict], parts: list[dict]) -> list[InvoiceLine]:
        lines = [InvoiceLine(kind="work", name=w["name"], qty=1, price=w["price"], amount=w["price"]) for w in works]
        lines += [InvoiceLine(kind="part", name=p.get("name") or p["sku"], qty=p["qty"], price=p["price"],
                              amount=p["qty"] * p["price"]) for p in parts]
        return lines

    # событие order.completed: рассчитать итоговую стоимость и сформировать счет
    def on_order_completed(self, event: dict) -> None:
        order_id = UUID(event["order_id"])
        if self.repo.list(count=1, order_id=order_id):
            return
        lines = self.build_lines(event.get("works", []), event.get("parts", []))
        invoice = self.repo.add(Invoice(order_id=order_id, client_id=UUID(event["client_id"]), lines=lines,
                                        total=sum(line.amount for line in lines)))
        self.publisher.publish("invoice.issued", {"invoice_id": invoice.id, "order_id": order_id,
                                                  "client_id": invoice.client_id, "total": invoice.total})

    # событие payment.succeeded: отметить оплату
    def on_payment_succeeded(self, event: dict) -> None:
        invoice = self.repo.get(UUID(event["invoice_id"]))
        if invoice.status == InvoiceStatus.PAID:
            return
        invoice.status = InvoiceStatus.PAID
        invoice.payment_id = UUID(event["payment_id"])
        invoice.paid_at = datetime.now(timezone.utc)
        self.repo.update(invoice)
        self.publisher.publish("invoice.paid", {"invoice_id": invoice.id, "order_id": invoice.order_id,
                                                "payment_id": invoice.payment_id})
