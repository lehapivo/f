from sqlalchemy import JSON, Column, DateTime, String, Text, Uuid

from app.database import Base


class RepairDB(Base):
    __tablename__ = "repairs"

    id = Column(Uuid, primary_key=True)
    order_id = Column(Uuid, nullable=False, unique=True)
    vehicle_id = Column(Uuid, nullable=False)
    works = Column(JSON, nullable=False, default=list)
    parts = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, index=True)
    mechanic = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class PartsStateDB(Base):
    __tablename__ = "parts_states"

    order_id = Column(Uuid, primary_key=True)
    status = Column(String(20), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
