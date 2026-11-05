from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.gateways.clients_gateway import ClientsGateway
from app.messaging import RabbitPublisher
from app.models.order import Order, OrderApprove, OrderClose, OrderCreate, OrderStatus
from app.repositories.db_order_repo import OrderRepo
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(OrderRepo(db), RabbitPublisher(), ClientsGateway())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, service: OrderService = Depends(get_service)) -> Order:
    return service.create_order(data)


@router.get("")
def list_orders(status: OrderStatus | None = None, client_id: UUID | None = None,
                offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
                service: OrderService = Depends(get_service)) -> list[Order]:
    return service.list_orders(status.value if status else None, client_id, offset, count)


@router.get("/{order_id}")
def get_order(order_id: UUID, service: OrderService = Depends(get_service)) -> Order:
    return service.get_order(order_id)


@router.post("/{order_id}:approve")
def approve_order(order_id: UUID, data: OrderApprove | None = None,
                  service: OrderService = Depends(get_service)) -> Order:
    return service.approve(order_id, data.work_codes if data else None)


@router.post("/{order_id}:close")
def close_order(order_id: UUID, data: OrderClose | None = None,
                service: OrderService = Depends(get_service)) -> Order:
    return service.close(order_id, data.mileage if data else None)
