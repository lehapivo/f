from sqlalchemy import Column, DateTime, Integer, String, Uuid

from app.database import Base


class PaymentDB(Base):
    __tablename__ = "payments"

    id = Column(Uuid, primary_key=True)
    invoice_id = Column(Uuid, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    method = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    external_id = Column(String(40), nullable=True)
    decline_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
