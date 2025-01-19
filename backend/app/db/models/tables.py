from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"
    
    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    customer_type = Column(String(50), nullable=False)
    customer_group = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    addresses = relationship("Address", back_populates="client", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="client", cascade="all, delete-orphan")

class Address(Base):
    __tablename__ = "addresses"
    
    address_id = Column(Integer, primary_key=True)
    zip = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    street = Column(String(200), nullable=False)
    house = Column(Integer, nullable=False)
    customer_id = Column(Integer, ForeignKey("clients.customer_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="addresses")
    installations = relationship("Subscription", back_populates="installation_address")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    subscription_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("clients.customer_id"), nullable=False)
    rateplan = Column(String(100), nullable=False)
    creation_date = Column(Date, nullable=False)
    installation_address_id = Column(Integer, ForeignKey("addresses.address_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="subscriptions")
    installation_address = relationship("Address", back_populates="installations")
    charges = relationship("SubscriptionCharge", back_populates="subscription", cascade="all, delete-orphan")

class SubscriptionCharge(Base):
    __tablename__ = "subscription_charges"
    
    charge_id = Column(Integer, primary_key=True)
    charge_datetime = Column(DateTime, nullable=False)
    charge_name = Column(String(200), nullable=False)
    charge_amount = Column(Numeric(10, 2), nullable=False)  # Using Numeric for precise amounts
    subscription_id = Column(Integer, ForeignKey("subscriptions.subscription_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="charges") 