from sqlalchemy import Column, DateTime, Integer, String, Uuid

from app.database import Base


class PartDB(Base):
    __tablename__ = "parts"

    sku = Column(String(40), primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    reserved = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), nullable=False)


class ReservationDB(Base):
    __tablename__ = "reservations"

    id = Column(Uuid, primary_key=True)
    order_id = Column(Uuid, nullable=False, index=True)
    sku = Column(String(40), nullable=False)
    qty = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class PurchaseOrderDB(Base):
    __tablename__ = "purchase_orders"

    id = Column(Uuid, primary_key=True)
    sku = Column(String(40), nullable=False)
    qty = Column(Integer, nullable=False)
    order_id = Column(Uuid, nullable=True)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=True)
