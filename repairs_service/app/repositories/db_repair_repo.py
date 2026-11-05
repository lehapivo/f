from app.models.repair import PartsState, Repair
from app.repositories.base import DbRepository
from app.schemas.repair import PartsStateDB, RepairDB


class RepairRepo(DbRepository[Repair]):
    model = Repair
    table = RepairDB


class PartsStateRepo(DbRepository[PartsState]):
    model = PartsState
    table = PartsStateDB

    def find(self, order_id) -> PartsState | None:
        row = self.db.get(PartsStateDB, order_id)
        return PartsState.model_validate(row) if row else None
