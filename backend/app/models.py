from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    category = Column(String(50), nullable=False)
    location = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False)
    ticket_price = Column(Integer, nullable=False)

    total_tickets = Column(Integer, nullable=False, default=100)
    available_tickets = Column(Integer, nullable=False, default=100)

    banner_image = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    ticket_count = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False)
    booking_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="CONFIRMED")
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    booking_id = Column(Integer, nullable=True)
    message = Column(String(500), nullable=False)
    notification_type = Column(String(50), nullable=False)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)