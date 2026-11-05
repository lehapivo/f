"""Синхронный вызов сервиса «Клиенты и автомобили»."""
from uuid import UUID

import httpx

from app.errors import DependencyError
from app.settings import settings


class ClientsGateway:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.clients_url).rstrip("/")

    def get_vehicle(self, vehicle_id: UUID) -> dict | None:
        try:
            response = httpx.get(f"{self.base_url}/api/vehicles/{vehicle_id}", timeout=3.0)
        except httpx.HTTPError as exc:
            raise DependencyError("clients_unavailable", str(exc))
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise DependencyError("clients_error", f"clients service returned {response.status_code}")
        return response.json()
