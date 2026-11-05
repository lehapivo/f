"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


@pytest.fixture(scope="module")
def vehicle():
    clients = os.getenv("CLIENTS_SERVICE_URL")
    if not clients:
        pytest.skip("CLIENTS_SERVICE_URL is not set")
    client = requests.post(f"{clients}/api/clients", json={"full_name": "Смирнов", "phone": "+79161234567"}).json()
    car = requests.post(f"{clients}/api/clients/{client['id']}/vehicles", json={
        "vin": uuid4().hex[:17].upper(), "plate": "К100КК50", "brand": "Toyota", "model": "Camry",
        "year": 2018, "mileage": 90000}).json()
    return client, car


def slot(days: int, hour: int) -> str:
    base = datetime.now(timezone.utc) + timedelta(days=days)
    return base.replace(hour=hour, minute=uuid4().int % 60, second=0, microsecond=0).isoformat()


def test_create_confirm_cancel(base_url, vehicle):
    client, car = vehicle
    response = requests.post(f"{base_url}/appointments", json={
        "client_id": client["id"], "vehicle_id": car["id"], "scheduled_at": slot(3, 9), "reason": "Замена масла"})
    assert response.status_code == 201
    appointment_id = response.json()["id"]
    assert requests.post(f"{base_url}/appointments/{appointment_id}:confirm").json()["status"] == "confirmed"
    assert requests.post(f"{base_url}/appointments/{appointment_id}:confirm").status_code == 409
    assert requests.post(f"{base_url}/appointments/{appointment_id}:cancel").json()["status"] == "cancelled"


def test_list_by_date(base_url, vehicle):
    client, car = vehicle
    when = slot(5, 11)
    requests.post(f"{base_url}/appointments", json={
        "client_id": client["id"], "vehicle_id": car["id"], "scheduled_at": when, "reason": "Диагностика"})
    day = when[:10]
    items = requests.get(f"{base_url}/appointments", params={"date": day}).json()
    assert items and all(a["scheduled_at"].startswith(day) for a in items)


def test_foreign_vehicle_and_errors(base_url, vehicle):
    _, car = vehicle
    response = requests.post(f"{base_url}/appointments", json={
        "client_id": str(uuid4()), "vehicle_id": car["id"], "scheduled_at": slot(4, 14), "reason": "ТО"})
    assert response.status_code == 400 and response.json()["error"] == "vehicle_of_other_client"
    assert requests.get(f"{base_url}/appointments/{uuid4()}").status_code == 404
