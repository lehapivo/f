from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.messaging import RabbitPublisher
from app.models.stock import PartCreate, PartOut, PurchaseOrder, PurchaseStatus
from app.repositories.db_stock_repo import PartRepo, PurchaseOrderRepo, ReservationRepo
from app.services.stock_service import StockService

router = APIRouter(tags=["Warehouse"])


def get_service(db: Session = Depends(get_db)) -> StockService:
    return StockService(PartRepo(db), ReservationRepo(db), PurchaseOrderRepo(db), RabbitPublisher())


@router.post("/parts", status_code=status.HTTP_201_CREATED)
def add_part(data: PartCreate, service: StockService = Depends(get_service)) -> PartOut:
    return service.add_part(data)


@router.get("/parts")
def list_parts(low_stock: bool = False, offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
               service: StockService = Depends(get_service)) -> list[PartOut]:
    return service.list_parts(low_stock, offset, count)


@router.get("/parts/{sku}")
def get_part(sku: str, service: StockService = Depends(get_service)) -> PartOut:
    return service.get_part(sku)


@router.get("/purchase-orders")
def list_purchase_orders(status: PurchaseStatus | None = None, offset: int = Query(0, ge=0),
                         count: int = Query(20, ge=1, le=100),
                         service: StockService = Depends(get_service)) -> list[PurchaseOrder]:
    return service.list_purchases(status.value if status else None, offset, count)


@router.post("/purchase-orders/{purchase_id}:receive")
def receive_purchase_order(purchase_id: UUID, service: StockService = Depends(get_service)) -> PurchaseOrder:
    return service.receive(purchase_id)
