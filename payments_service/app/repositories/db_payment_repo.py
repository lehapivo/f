from app.models.payment import Payment
from app.repositories.base import DbRepository
from app.schemas.payment import PaymentDB


class PaymentRepo(DbRepository[Payment]):
    model = Payment
    table = PaymentDB
