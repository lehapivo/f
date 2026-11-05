from sqlalchemy import Column, DateTime, String, Text, Uuid

from app.database import Base


class AppointmentDB(Base):
    __tablename__ = "appointments"

    id = Column(Uuid, primary_key=True)
    client_id = Column(Uuid, nullable=False, index=True)
    vehicle_id = Column(Uuid, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    order_id = Column(Uuid, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
