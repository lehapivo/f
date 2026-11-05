from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.client import ClientCreate, VehicleCreate


def test_valid_client():
    assert ClientCreate(full_name="Петров Петр", phone="+79991234567").email is None


@pytest.mark.parametrize("phone", ["12345", "+7-999-123", "phone"])
def test_invalid_phone(phone):
    with pytest.raises(ValidationError):
        ClientCreate(full_name="Петров", phone=phone)


def test_vin_must_have_17_chars():
    with pytest.raises(ValidationError):
        VehicleCreate(vin="SHORT", plate="А001АА77", brand="Lada", model="Vesta", year=2020, mileage=0)


def test_year_range():
    with pytest.raises(ValidationError):
        VehicleCreate(vin="X" * 17, plate="А001АА77", brand="Lada", model="Vesta", year=1900, mileage=0)
