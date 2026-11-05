from app.models.order import Order
from app.repositories.base import DbRepository
from app.schemas.order import OrderDB


class OrderRepo(DbRepository[Order]):
    model = Order
    table = OrderDB
