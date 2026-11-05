from app.models.stock import Part, PurchaseOrder, Reservation
from app.repositories.base import DbRepository
from app.schemas.stock import PartDB, PurchaseOrderDB, ReservationDB


class PartRepo(DbRepository[Part]):
    model = Part
    table = PartDB

    def exists(self, sku: str) -> bool:
        return self.db.get(PartDB, sku) is not None


class ReservationRepo(DbRepository[Reservation]):
    model = Reservation
    table = ReservationDB


class PurchaseOrderRepo(DbRepository[PurchaseOrder]):
    model = PurchaseOrder
    table = PurchaseOrderDB
