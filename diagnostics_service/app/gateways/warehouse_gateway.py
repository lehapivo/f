"""Синхронный вызов сервиса «Склад»: наличие и цена запчасти."""
import httpx

from app.errors import DependencyError
from app.settings import settings


class WarehouseGateway:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.warehouse_url).rstrip("/")

    def get_part(self, sku: str) -> dict | None:
        try:
            response = httpx.get(f"{self.base_url}/api/parts/{sku}", timeout=3.0)
        except httpx.HTTPError as exc:
            raise DependencyError("warehouse_unavailable", str(exc))
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise DependencyError("warehouse_error", f"warehouse service returned {response.status_code}")
        return response.json()
