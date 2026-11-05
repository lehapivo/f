"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def test_list_invoices(base_url):
    response = requests.get(f"{base_url}/invoices", params={"status": "issued", "count": 5})
    assert response.status_code == 200 and isinstance(response.json(), list)


def test_errors(base_url):
    assert requests.get(f"{base_url}/invoices/{uuid4()}").status_code == 404
    assert requests.get(f"{base_url}/invoices/not-a-uuid").status_code == 422
    assert requests.get(f"{base_url}/invoices", params={"status": "draft"}).status_code == 422
