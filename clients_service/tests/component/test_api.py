"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def vin() -> str:
    return uuid4().hex[:17].upper()


def test_register_client_and_add_vehicle(base_url):
    response = requests.post(f"{base_url}/clients", json={"full_name": "Орлова Анна", "phone": "+79035550000"})
    assert response.status_code == 201
    client = response.json()
    car = requests.post(f"{base_url}/clients/{client['id']}/vehicles", json={
        "vin": vin(), "plate": "Е555КХ77", "brand": "Kia", "model": "Rio", "year": 2019, "mileage": 64000})
    assert car.status_code == 201
    card = requests.get(f"{base_url}/clients/{client['id']}").json()
    assert [v["id"] for v in card["vehicles"]] == [car.json()["id"]]
    assert requests.get(f"{base_url}/vehicles/{car.json()['id']}").json()["mileage"] == 64000


def test_duplicate_vin_conflict(base_url):
    client = requests.post(f"{base_url}/clients", json={"full_name": "Орлов", "phone": "+79035550001"}).json()
    body = {"vin": vin(), "plate": "Е556КХ77", "brand": "Kia", "model": "Rio", "year": 2019, "mileage": 1}
    assert requests.post(f"{base_url}/clients/{client['id']}/vehicles", json=body).status_code == 201
    assert requests.post(f"{base_url}/clients/{client['id']}/vehicles", json=body).status_code == 409


def test_errors(base_url):
    assert requests.post(f"{base_url}/clients", json={"full_name": "X", "phone": "abc"}).status_code == 422
    assert requests.get(f"{base_url}/clients/{uuid4()}").status_code == 404
    assert requests.get(f"{base_url}/vehicles/{uuid4()}").status_code == 404
