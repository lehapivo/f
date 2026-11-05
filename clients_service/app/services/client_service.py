"""Бизнес-логика клиентов и автомобилей."""
from uuid import UUID

from app.errors import ConflictError
from app.models.client import Client, ClientCard, ClientCreate, Vehicle, VehicleCreate


class ClientService:
    def __init__(self, clients, vehicles, publisher) -> None:
        self.clients = clients
        self.vehicles = vehicles
        self.publisher = publisher

    def register_client(self, data: ClientCreate) -> Client:
        client = self.clients.add(Client(**data.model_dump()))
        self.publisher.publish("client.registered", {"client_id": client.id, "full_name": client.full_name})
        return client

    def get_card(self, client_id: UUID) -> ClientCard:
        client = self.clients.get(client_id)
        return ClientCard(**client.model_dump(), vehicles=self.vehicles.list(count=100, client_id=client_id))

    def add_vehicle(self, client_id: UUID, data: VehicleCreate) -> Vehicle:
        self.clients.get(client_id)                       # 404, если клиента нет
        vin = data.vin.upper()
        if self.vehicles.find_by_vin(vin):
            raise ConflictError("vin_exists", f"Vehicle with VIN {vin} already registered")
        vehicle = self.vehicles.add(Vehicle(client_id=client_id, **{**data.model_dump(), "vin": vin}))
        self.publisher.publish("vehicle.added", {"vehicle_id": vehicle.id, "client_id": client_id, "vin": vin})
        return vehicle

    def get_vehicle(self, vehicle_id: UUID) -> Vehicle:
        return self.vehicles.get(vehicle_id)

    # событие order.closed: фиксируется пробег автомобиля при выдаче
    def on_order_closed(self, event: dict) -> None:
        vehicle = self.vehicles.get(UUID(event["vehicle_id"]))
        if event["mileage"] > vehicle.mileage:
            vehicle.mileage = event["mileage"]
            self.vehicles.update(vehicle)
