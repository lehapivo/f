from sqlalchemy import JSON, Column, DateTime, Integer, String, Uuid

from app.database import Base


class InvoiceDB(Base):
    __tablename__ = "invoices"

    id = Column(Uuid, primary_key=True)
    order_id = Column(Uuid, nullable=False, unique=True)
    client_id = Column(Uuid, nullable=False, index=True)
    lines = Column(JSON, nullable=False, default=list)
    total = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    payment_id = Column(Uuid, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
