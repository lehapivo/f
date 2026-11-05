from app.models.repair import PartsState, Repair
from app.repositories.base import LocalRepository


class RepairRepo(LocalRepository[Repair]):
    model = Repair


class PartsStateRepo(LocalRepository[PartsState]):
    model = PartsState
    key = "order_id"

    def find(self, order_id) -> PartsState | None:
        return self._items.get(order_id)
