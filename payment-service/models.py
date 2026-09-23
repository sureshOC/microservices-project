# models.py

from sqlalchemy import Column, Integer, String, Numeric
from database import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    idempotency_key = Column(String(255), unique=True, nullable=False)

    order_id = Column(Integer, nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(String(50), nullable=False)