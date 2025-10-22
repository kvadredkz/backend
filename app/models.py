from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class OrderStatus(str, enum.Enum):
    WAITING = "waiting_to_process"
    PROCESSED = "processed"
    CANCELLED = "cancelled"

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    products = relationship("Product", back_populates="shop")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    shop = relationship("Shop", back_populates="products")
    orders = relationship("Order", back_populates="product")
    analytics = relationship("Analytics", back_populates="product")
    affiliate_links = relationship("AffiliateLink", back_populates="product")

class Blogger(Base):
    __tablename__ = "bloggers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    bio = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    orders = relationship("Order", back_populates="blogger")
    analytics = relationship("Analytics", back_populates="blogger")
    affiliate_links = relationship("AffiliateLink", back_populates="blogger")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    blogger_id = Column(Integer, ForeignKey("bloggers.id"))
    quantity = Column(Integer)
    price_per_item = Column(Float)
    client_phone = Column(String)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.WAITING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="orders")
    blogger = relationship("Blogger", back_populates="orders")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    blogger_id = Column(Integer, ForeignKey("bloggers.id"))
    visit_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    items_sold = Column(Integer, default=0)
    money_earned = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="analytics")
    blogger = relationship("Blogger", back_populates="analytics")

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    blogger_id = Column(Integer, ForeignKey("bloggers.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="affiliate_links")
    blogger = relationship("Blogger", back_populates="affiliate_links")