"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def test_add_and_get_part(base_url):
    sku = f"T-{uuid4().hex[:8]}"
    response = requests.post(f"{base_url}/parts", json={"sku": sku, "name": "Свеча", "price": 450, "quantity": 8})
    assert response.status_code == 201
    part = requests.get(f"{base_url}/parts/{sku}").json()
    assert part["available"] == 8 and part["reserved"] == 0
    assert requests.post(f"{base_url}/parts", json={"sku": sku, "name": "X", "price": 1, "quantity": 1}).status_code == 409


def test_low_stock_filter(base_url):
    sku = f"T-{uuid4().hex[:8]}"
    requests.post(f"{base_url}/parts", json={"sku": sku, "name": "Ремень", "price": 1900, "quantity": 1})
    low = requests.get(f"{base_url}/parts", params={"low_stock": "true", "count": 100}).json()
    assert sku in [p["sku"] for p in low]


def test_purchase_orders_and_errors(base_url):
    assert requests.get(f"{base_url}/purchase-orders", params={"status": "ordered"}).status_code == 200
    assert requests.get(f"{base_url}/parts/NO-SUCH-SKU").status_code == 404
    assert requests.post(f"{base_url}/purchase-orders/{uuid4()}:receive").status_code == 404
