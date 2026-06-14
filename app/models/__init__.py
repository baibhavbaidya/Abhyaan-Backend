from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import uuid
import enum


def generate_uuid():
    return str(uuid.uuid4())


class ChannelEnum(str, enum.Enum):
    whatsapp = "whatsapp"
    sms = "sms"
    email = "email"


class CommunicationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    clicked = "clicked"
    failed = "failed"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    completed = "completed"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    city = Column(String, nullable=False)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_purchase_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("Order", back_populates="customer")
    communications = relationship("Communication", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    items = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="orders")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    criteria = Column(JSON, nullable=False)
    customer_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    campaigns = relationship("Campaign", back_populates="segment")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    segment_id = Column(String, ForeignKey("segments.id"), nullable=False)
    message = Column(String, nullable=False)
    channel = Column(Enum(ChannelEnum), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.draft)
    total_sent = Column(Integer, default=0)
    delivered = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    opened = Column(Integer, default=0)
    clicked = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    launched_at = Column(DateTime, nullable=True)

    segment = relationship("Segment", back_populates="campaigns")
    communications = relationship("Communication", back_populates="campaign")


class Communication(Base):
    __tablename__ = "communications"

    id = Column(String, primary_key=True, default=generate_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.pending)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    campaign = relationship("Campaign", back_populates="communications")
    customer = relationship("Customer", back_populates="communications")