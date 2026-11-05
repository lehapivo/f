from app.models.payment import Payment
from app.repositories.base import LocalRepository


class PaymentRepo(LocalRepository[Payment]):
    model = Payment
