from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Uuid

from app.database import Base


class ClientDB(Base):
    __tablename__ = "clients"

    id = Column(Uuid, primary_key=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(16), nullable=False)
    email = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class VehicleDB(Base):
    __tablename__ = "vehicles"

    id = Column(Uuid, primary_key=True)
    client_id = Column(Uuid, ForeignKey("clients.id"), nullable=False, index=True)
    vin = Column(String(17), nullable=False, unique=True)
    plate = Column(String(12), nullable=False)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    mileage = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
