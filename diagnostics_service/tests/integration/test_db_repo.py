from uuid import uuid4

import pytest

from app.models.diagnostic import Diagnostic, PartLine, Work
from app.repositories.db_diagnostic_repo import DiagnosticRepo

pytestmark = pytest.mark.integration


def test_store_results_in_json_columns(db_session):
    repo = DiagnosticRepo(db_session)
    diagnostic = repo.add(Diagnostic(order_id=uuid4(), vehicle_id=uuid4(), complaint="Вибрация"))
    diagnostic.faults = ["Дисбаланс колес"]
    diagnostic.works = [Work(code="W-10", name="Балансировка", price=1200)]
    diagnostic.parts = [PartLine(sku="WG-1", qty=4, name="Грузики", price=50, in_stock=True)]
    diagnostic.status = "completed"
    repo.update(diagnostic)
    saved = repo.get(diagnostic.id)
    assert saved.works[0].name == "Балансировка" and saved.parts[0].qty == 4


def test_filter_by_order_and_status(db_session):
    repo = DiagnosticRepo(db_session)
    order_id = uuid4()
    repo.add(Diagnostic(order_id=order_id, vehicle_id=uuid4(), complaint="Шум"))
    repo.add(Diagnostic(order_id=uuid4(), vehicle_id=uuid4(), complaint="Стук", status="completed"))
    assert len(repo.list(order_id=order_id)) == 1
    assert len(repo.list(status="pending")) == 1
