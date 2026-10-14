
from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Phase 2: Role-Based Access Control
    role = Column(String(20), nullable=False, default="USER")

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

    # Phase 2: Organizer ownership and event lifecycle
    organizer_id = Column(Integer, nullable=True, index=True)
    event_status = Column(
        String(20),
        nullable=False,
        default="UPCOMING"
    )

    created_at = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    ticket_count = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False)
    coupon_id = Column(Integer, nullable=True)
    discount_amount = Column(Integer, default=0, nullable=False)
    final_amount = Column(Integer, default=0, nullable=False)
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
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, nullable=False, index=True)
    payment_method = Column(String(30), nullable=False)
    payment_status = Column(String(20), default="PENDING", nullable=False)
    transaction_id = Column(String(100), unique=True, nullable=True)
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    coupon_code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), nullable=False)
    discount_value = Column(Float, nullable=False)
    minimum_booking_amount = Column(Integer, default=0, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, default=100, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventUpdate(Base):
    __tablename__ = "event_updates"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=False, index=True)
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
