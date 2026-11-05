import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture()
def db_session():
    """Сессия к тестовой БД PostgreSQL для интеграционных тестов."""
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is not set")
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def base_url():
    """Адрес запущенного сервиса для компонентных тестов."""
    url = os.getenv("SERVICE_URL")
    if not url:
        pytest.skip("SERVICE_URL is not set")
    return url.rstrip("/") + "/api"
