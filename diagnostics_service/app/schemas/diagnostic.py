from sqlalchemy import JSON, Column, DateTime, String, Text, Uuid

from app.database import Base


class DiagnosticDB(Base):
    __tablename__ = "diagnostics"

    id = Column(Uuid, primary_key=True)
    order_id = Column(Uuid, nullable=False, unique=True)
    vehicle_id = Column(Uuid, nullable=False)
    complaint = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    faults = Column(JSON, nullable=False, default=list)
    works = Column(JSON, nullable=False, default=list)
    parts = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
