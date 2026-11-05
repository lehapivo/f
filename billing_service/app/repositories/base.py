"""Базовые репозитории: в памяти (unit-тесты) и поверх PostgreSQL."""
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError

M = TypeVar("M", bound=BaseModel)


class LocalRepository(Generic[M]):
    model: type[M]
    key: str = "id"

    def __init__(self) -> None:
        self._items: dict = {}

    def get(self, key) -> M:
        if key not in self._items:
            raise NotFoundError(f"{self.model.__name__.lower()}_not_found", f"{self.model.__name__} {key} not found")
        return self._items[key].model_copy(deep=True)

    def add(self, item: M) -> M:
        self._items[getattr(item, self.key)] = item.model_copy(deep=True)
        return item

    def update(self, item: M) -> M:
        return self.add(item)

    def list(self, offset: int = 0, count: int = 20, **filters) -> list[M]:
        items = [i for i in self._items.values()
                 if all(v is None or getattr(i, k) == v for k, v in filters.items())]
        items.sort(key=lambda i: getattr(i, "created_at", getattr(i, self.key)))
        return [i.model_copy(deep=True) for i in items[offset:offset + count]]


class DbRepository(Generic[M]):
    model: type[M]
    table: type

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, key) -> M:
        row = self.db.get(self.table, key)
        if row is None:
            raise NotFoundError(f"{self.model.__name__.lower()}_not_found", f"{self.model.__name__} {key} not found")
        return self.model.model_validate(row)

    def add(self, item: M) -> M:
        self.db.add(self.table(**item.model_dump()))
        self.db.commit()
        return item

    def update(self, item: M) -> M:
        self.db.merge(self.table(**item.model_dump()))
        self.db.commit()
        return item

    def list(self, offset: int = 0, count: int = 20, **filters) -> list[M]:
        query = select(self.table)
        for name, value in filters.items():
            if value is not None:
                query = query.where(getattr(self.table, name) == value)
        order = getattr(self.table, "created_at", None)
        if order is not None:
            query = query.order_by(order)
        rows = self.db.scalars(query.offset(offset).limit(count)).all()
        return [self.model.model_validate(r) for r in rows]
