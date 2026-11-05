"""Бизнес-логика оплаты счета клиентом."""
from uuid import UUID

from app.errors import BusinessRuleError, ConflictError
from app.models.payment import Payment, PaymentCreate, PaymentStatus


class PaymentService:
    def __init__(self, repo, publisher, billing, provider) -> None:
        self.repo = repo
        self.publisher = publisher
        self.billing = billing
        self.provider = provider

    def pay(self, data: PaymentCreate) -> Payment:
        invoice = self.billing.get_invoice(data.invoice_id)          # синхронный вызов
        if invoice is None:
            raise BusinessRuleError("invoice_not_found", f"Invoice {data.invoice_id} not found")
        if invoice["status"] == "paid" or self.repo.list(count=1, invoice_id=data.invoice_id, status="succeeded"):
            raise ConflictError("already_paid", "Invoice is already paid")
        if data.amount != invoice["total"]:
            raise BusinessRuleError("amount_mismatch", f"Invoice total is {invoice['total']}")
        approved, reference = self.provider.charge(data.amount, data.method)
        payment = Payment(**data.model_dump(),
                          status=PaymentStatus.SUCCEEDED if approved else PaymentStatus.DECLINED,
                          external_id=reference if approved else None,
                          decline_reason=None if approved else reference)
        self.repo.add(payment)
        key = "payment.succeeded" if approved else "payment.declined"
        self.publisher.publish(key, {"payment_id": payment.id, "invoice_id": payment.invoice_id,
                                     "order_id": invoice["order_id"], "amount": payment.amount})
        return payment

    def get(self, payment_id: UUID) -> Payment:
        return self.repo.get(payment_id)

    def list(self, invoice_id: UUID | None = None, offset=0, count=20):
        return self.repo.list(offset=offset, count=count, invoice_id=invoice_id)
