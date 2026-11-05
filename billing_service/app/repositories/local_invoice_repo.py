from app.models.invoice import Invoice
from app.repositories.base import LocalRepository


class InvoiceRepo(LocalRepository[Invoice]):
    model = Invoice
