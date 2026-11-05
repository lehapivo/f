"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
import os
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


@pytest.fixture(scope="module")
def vehicle():
    """Клиент и автомобиль создаются через API сервиса клиентов."""
    clients = os.getenv("CLIENTS_SERVICE_URL")
    if not clients:
        pytest.skip("CLIENTS_SERVICE_URL is not set")
    client = requests.post(f"{clients}/api/clients",
                           json={"full_name": "Иванов Иван", "phone": "+79990000001"}).json()
    car = requests.post(f"{clients}/api/clients/{client['id']}/vehicles",
                        json={"vin": uuid4().hex[:17].upper(), "plate": "А001АА77", "brand": "Lada",
                              "model": "Vesta", "year": 2020, "mileage": 30000}).json()
    return client, car


def test_create_and_get_order(base_url, vehicle):
    client, car = vehicle
    response = requests.post(f"{base_url}/orders", json={
        "client_id": client["id"], "vehicle_id": car["id"], "complaint": "Скрип тормозов", "mileage": 30500})
    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "created"
    assert requests.get(f"{base_url}/orders/{order['id']}").json()["complaint"] == "Скрип тормозов"


def test_list_filtered_by_client(base_url, vehicle):
    client, _ = vehicle
    orders = requests.get(f"{base_url}/orders", params={"client_id": client["id"], "count": 5}).json()
    assert orders and all(o["client_id"] == client["id"] for o in orders)


def test_unknown_vehicle_rejected(base_url, vehicle):
    client, _ = vehicle
    response = requests.post(f"{base_url}/orders", json={
        "client_id": client["id"], "vehicle_id": str(uuid4()), "complaint": "Шум", "mileage": 1})
    assert response.status_code == 400
    assert response.json()["error"] == "vehicle_not_found"


def test_approve_before_diagnosis_conflict(base_url, vehicle):
    client, car = vehicle
    order = requests.post(f"{base_url}/orders", json={
        "client_id": client["id"], "vehicle_id": car["id"], "complaint": "ТО", "mileage": 30600}).json()
    assert requests.post(f"{base_url}/orders/{order['id']}:approve").status_code == 409


def test_validation_and_not_found(base_url):
    assert requests.post(f"{base_url}/orders", json={"complaint": ""}).status_code == 422
    assert requests.get(f"{base_url}/orders/{uuid4()}").status_code == 404
    assert requests.get(f"{base_url}/orders", params={"count": 500}).status_code == 422
