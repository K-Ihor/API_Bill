from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import func
from typing import List, Dict, Union, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    total_amount = Column(Float)
    payment_type = Column(String)
    rest_amount = Column(Float)
    products = relationship("Product", back_populates="receipt")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"))
    name = Column(String)
    price = Column(Float)
    quantity = Column(Float)
    total = Column(Float)
    receipt = relationship("Receipt", back_populates="products")


class ReceiptCreate(BaseModel):
    products: List[Dict[str, Union[str, float]]]
    payment: Dict[str, Union[str, float]]


class ReceiptView(BaseModel):
    id: int
    products: List[Dict[str, Union[str, float]]]
    payment: Dict[str, Union[str, float]]
    total: float
    rest: float
    created_at: datetime


class ReceiptFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_total_amount: Optional[float] = None
    payment_type: Optional[str] = None


class ReceiptViewConfig(BaseModel):
    pass
