"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def test_unknown_invoice_rejected(base_url):
    response = requests.post(f"{base_url}/payments", json={"invoice_id": str(uuid4()), "amount": 100, "method": "card"})
    assert response.status_code == 400 and response.json()["error"] == "invoice_not_found"


def test_validation_errors(base_url):
    assert requests.post(f"{base_url}/payments", json={"invoice_id": str(uuid4()), "amount": -5,
                                                       "method": "card"}).status_code == 422
    assert requests.get(f"{base_url}/payments/{uuid4()}").status_code == 404
    assert requests.get(f"{base_url}/payments", params={"invoice_id": str(uuid4())}).json() == []
