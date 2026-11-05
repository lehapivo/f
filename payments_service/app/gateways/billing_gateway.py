"""Синхронный вызов сервиса «Счета»: сумма и статус счета."""
from uuid import UUID

import httpx

from app.errors import DependencyError
from app.settings import settings


class BillingGateway:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.billing_url).rstrip("/")

    def get_invoice(self, invoice_id: UUID) -> dict | None:
        try:
            response = httpx.get(f"{self.base_url}/api/invoices/{invoice_id}", timeout=3.0)
        except httpx.HTTPError as exc:
            raise DependencyError("billing_unavailable", str(exc))
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise DependencyError("billing_error", f"billing service returned {response.status_code}")
        return response.json()
