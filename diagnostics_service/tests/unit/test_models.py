import pytest
from pydantic import ValidationError

from app.models.diagnostic import DiagnosticResult


def test_result_requires_faults_and_works():
    with pytest.raises(ValidationError):
        DiagnosticResult(faults=[], works=[{"code": "W", "name": "x", "price": 1}])
    with pytest.raises(ValidationError):
        DiagnosticResult(faults=["Износ"], works=[])


def test_parts_are_optional():
    assert DiagnosticResult(faults=["Износ"], works=[{"code": "W", "name": "x", "price": 1}]).parts == []
