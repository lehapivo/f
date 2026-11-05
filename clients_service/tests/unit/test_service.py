from uuid import uuid4

import pytest

from app.errors import ConflictError, NotFoundError
from app.messaging import MemoryPublisher
from app.models.client import ClientCreate, VehicleCreate
from app.repositories.local_client_repo import ClientRepo, VehicleRepo
from app.services.client_service import ClientService

CAR = dict(vin="xta21700000000001", plate="А123ВС77", brand="Lada", model="Vesta", year=2021, mileage=15000)


@pytest.fixture()
def service():
    return ClientService(ClientRepo(), VehicleRepo(), MemoryPublisher())


def test_register_client(service):
    client = service.register_client(ClientCreate(full_name="Сидоров", phone="+79990000000"))
    assert service.get_card(client.id).vehicles == []
    assert service.publisher.keys() == ["client.registered"]


def test_add_vehicle_normalizes_vin(service):
    client = service.register_client(ClientCreate(full_name="Сидоров", phone="+79990000000"))
    vehicle = service.add_vehicle(client.id, VehicleCreate(**CAR))
    assert vehicle.vin == CAR["vin"].upper()
    assert [v.id for v in service.get_card(client.id).vehicles] == [vehicle.id]


def test_duplicate_vin(service):
    client = service.register_client(ClientCreate(full_name="Сидоров", phone="+79990000000"))
    service.add_vehicle(client.id, VehicleCreate(**CAR))
    with pytest.raises(ConflictError):
        service.add_vehicle(client.id, VehicleCreate(**CAR))


def test_vehicle_for_unknown_client(service):
    with pytest.raises(NotFoundError):
        service.add_vehicle(uuid4(), VehicleCreate(**CAR))


def test_order_closed_updates_mileage_only_upwards(service):
    client = service.register_client(ClientCreate(full_name="Сидоров", phone="+79990000000"))
    vehicle = service.add_vehicle(client.id, VehicleCreate(**CAR))
    service.on_order_closed({"vehicle_id": str(vehicle.id), "mileage": 15500})
    service.on_order_closed({"vehicle_id": str(vehicle.id), "mileage": 100})
    assert service.get_vehicle(vehicle.id).mileage == 15500
