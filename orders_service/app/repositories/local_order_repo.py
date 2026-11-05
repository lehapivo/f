from app.models.order import Order
from app.repositories.base import LocalRepository


class OrderRepo(LocalRepository[Order]):
    model = Order
