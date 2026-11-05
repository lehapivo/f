"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def test_list_pending(base_url):
    response = requests.get(f"{base_url}/diagnostics", params={"status": "pending"})
    assert response.status_code == 200
    assert all(d["status"] == "pending" for d in response.json())


def test_errors(base_url):
    assert requests.get(f"{base_url}/diagnostics/{uuid4()}").status_code == 404
    assert requests.get(f"{base_url}/diagnostics", params={"status": "unknown"}).status_code == 422
    result = {"faults": ["x"], "works": [{"code": "W", "name": "x", "price": 1}]}
    assert requests.post(f"{base_url}/diagnostics/{uuid4()}:complete", json=result).status_code == 404
    assert requests.post(f"{base_url}/diagnostics/{uuid4()}:complete", json={"faults": []}).status_code == 422
