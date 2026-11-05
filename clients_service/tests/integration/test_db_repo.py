from uuid import uuid4

import pytest

from app.errors import NotFoundError
from app.models.client import Client, Vehicle
from app.repositories.db_client_repo import ClientRepo, VehicleRepo

pytestmark = pytest.mark.integration


def test_client_with_vehicles(db_session):
    clients, vehicles = ClientRepo(db_session), VehicleRepo(db_session)
    client = clients.add(Client(full_name="Кузнецов", phone="+79991112233"))
    vehicles.add(Vehicle(client_id=client.id, vin="WVWZZZ1JZXW000001", plate="В777ОР99",
                         brand="VW", model="Golf", year=2015, mileage=120000))
    assert clients.get(client.id).full_name == "Кузнецов"
    assert vehicles.list(client_id=client.id)[0].vin == "WVWZZZ1JZXW000001"
    assert vehicles.find_by_vin("WVWZZZ1JZXW000001") is not None


def test_update_mileage(db_session):
    clients, vehicles = ClientRepo(db_session), VehicleRepo(db_session)
    client = clients.add(Client(full_name="Кузнецов", phone="+79991112233"))
    vehicle = vehicles.add(Vehicle(client_id=client.id, vin="WVWZZZ1JZXW000002", plate="В778ОР99",
                                   brand="VW", model="Polo", year=2018, mileage=1000))
    vehicle.mileage = 2000
    vehicles.update(vehicle)
    assert vehicles.get(vehicle.id).mileage == 2000


def test_missing_vehicle(db_session):
    with pytest.raises(NotFoundError):
        VehicleRepo(db_session).get(uuid4())
