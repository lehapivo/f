from app.models.stock import Part, PurchaseOrder, Reservation
from app.repositories.base import LocalRepository


class PartRepo(LocalRepository[Part]):
    model = Part
    key = "sku"

    def exists(self, sku: str) -> bool:
        return sku in self._items


class ReservationRepo(LocalRepository[Reservation]):
    model = Reservation


class PurchaseOrderRepo(LocalRepository[PurchaseOrder]):
    model = PurchaseOrder
