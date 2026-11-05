from app.models.client import Client, Vehicle
from app.repositories.base import LocalRepository


class ClientRepo(LocalRepository[Client]):
    model = Client


class VehicleRepo(LocalRepository[Vehicle]):
    model = Vehicle

    def find_by_vin(self, vin: str) -> Vehicle | None:
        return next((v for v in self._items.values() if v.vin == vin), None)
