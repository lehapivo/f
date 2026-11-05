from app.models.invoice import Invoice
from app.repositories.base import DbRepository
from app.schemas.invoice import InvoiceDB


class InvoiceRepo(DbRepository[Invoice]):
    model = Invoice
    table = InvoiceDB
