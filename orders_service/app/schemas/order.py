from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, Uuid

from app.database import Base


class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(Uuid, primary_key=True)
    client_id = Column(Uuid, nullable=False, index=True)
    vehicle_id = Column(Uuid, nullable=False)
    appointment_id = Column(Uuid, nullable=True)
    complaint = Column(Text, nullable=False)
    mileage = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    faults = Column(JSON, nullable=False, default=list)
    works = Column(JSON, nullable=False, default=list)
    parts = Column(JSON, nullable=False, default=list)
    estimate = Column(Integer, nullable=False, default=0)
    invoice_id = Column(Uuid, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
