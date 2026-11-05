from sqlalchemy import select

from app.models.client import Client, Vehicle
from app.repositories.base import DbRepository
from app.schemas.client import ClientDB, VehicleDB


class ClientRepo(DbRepository[Client]):
    model = Client
    table = ClientDB


class VehicleRepo(DbRepository[Vehicle]):
    model = Vehicle
    table = VehicleDB

    def find_by_vin(self, vin: str) -> Vehicle | None:
        row = self.db.scalars(select(VehicleDB).where(VehicleDB.vin == vin)).first()
        return Vehicle.model_validate(row) if row else None
