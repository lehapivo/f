"""Компонентные тесты: запросы к запущенному сервису через HTTP."""
from uuid import uuid4

import pytest
import requests

pytestmark = pytest.mark.component


def test_list_and_filters(base_url):
    response = requests.get(f"{base_url}/repairs", params={"status": "planned", "count": 10})
    assert response.status_code == 200
    assert all(r["status"] == "planned" for r in response.json())


def test_errors(base_url):
    assert requests.get(f"{base_url}/repairs/{uuid4()}").status_code == 404
    assert requests.post(f"{base_url}/repairs/{uuid4()}:start", json={"mechanic": "Петров"}).status_code == 404
    assert requests.post(f"{base_url}/repairs/{uuid4()}:start", json={"mechanic": ""}).status_code == 422
    assert requests.post(f"{base_url}/repairs/{uuid4()}:complete").status_code == 404
