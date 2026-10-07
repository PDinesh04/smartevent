from datetime import datetime, timedelta
from io import BytesIO

import qrcode

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="SmartEvent API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to SmartEvent API"
    }


# =========================================================
# AUTHENTICATION
# =========================================================

@app.post(
    "/auth/register",
    response_model=schemas.UserResponse
)
def register_user(
    user: schemas.UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) |
        (models.User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post(
    "/auth/login",
    response_model=schemas.TokenResponse
)
def login_user(
    user: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "user_id": existing_user.id,
        "email": existing_user.email,
        "username": existing_user.username
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get(
    "/auth/me",
    response_model=schemas.UserResponse
)
def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id")

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# =========================================================
# EVENTS
# =========================================================

@app.post(
    "/events",
    response_model=schemas.EventResponse
)
def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db)
):
    new_event = models.Event(
        title=event.title,
        description=event.description,
        category=event.category,
        location=event.location,
        event_date=event.event_date,
        ticket_price=event.ticket_price,
        total_tickets=event.total_tickets,
        available_tickets=event.total_tickets,
        banner_image=event.banner_image
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


@app.get(
    "/events",
    response_model=list[schemas.EventResponse]
)
def get_events(
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Event)

    if category:
        query = query.filter(
            models.Event.category.ilike(category)
        )

    if search:
        query = query.filter(
            models.Event.title.ilike(
                f"%{search}%"
            )
        )

    return query.all()


@app.get(
    "/events/{event_id}",
    response_model=schemas.EventResponse
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(
        models.Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event


# =========================================================
# BOOKINGS
# =========================================================

@app.post(
    "/bookings",
    response_model=schemas.BookingResponse
)
def create_booking(
    booking: schemas.BookingCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(
        models.Event.id == booking.event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if booking.ticket_count <= 0:
        raise HTTPException(
            status_code=400,
            detail="Ticket count must be greater than 0"
        )

    if booking.ticket_count > event.available_tickets:
        raise HTTPException(
            status_code=400,
            detail="Not enough tickets available"
        )

    total_amount = (
        event.ticket_price *
        booking.ticket_count
    )

    event.available_tickets -= booking.ticket_count

    new_booking = models.Booking(
        user_id=current_user["user_id"],
        event_id=booking.event_id,
        ticket_count=booking.ticket_count,
        total_amount=total_amount,
        status="CONFIRMED"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Create booking confirmation notification
    notification = models.Notification(
        user_id=current_user["user_id"],
        booking_id=new_booking.id,
        message=(
            f"Your booking #{new_booking.id} "
            f"has been confirmed successfully."
        ),
        notification_type="BOOKING_CONFIRMED",
        is_read=0
    )

    db.add(notification)
    db.commit()

    return new_booking


@app.get(
    "/bookings",
    response_model=list[schemas.BookingHistoryResponse]
)
def get_my_bookings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id ==
        current_user["user_id"]
    ).order_by(
        models.Booking.booking_date.desc()
    ).all()

    return bookings


# =========================================================
# QR TICKET
# =========================================================

@app.get(
    "/bookings/{booking_id}/qr"
)
def generate_booking_qr(
    booking_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id ==
        current_user["user_id"]
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    qr_data = (
        f"SmartEvent Ticket\n"
        f"Booking ID: {booking.id}\n"
        f"Event ID: {booking.event_id}\n"
        f"Tickets: {booking.ticket_count}\n"
        f"Status: {booking.status}"
    )

    qr = qrcode.make(qr_data)

    buffer = BytesIO()

    qr.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png"
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@app.get(
    "/notifications",
    response_model=list[schemas.NotificationResponse]
)
def get_notifications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = db.query(
        models.Notification
    ).filter(
        models.Notification.user_id ==
        current_user["user_id"]
    ).order_by(
        models.Notification.created_at.desc()
    ).all()

    return notifications


@app.patch(
    "/notifications/{notification_id}/read"
)
def mark_notification_read(
    notification_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(
        models.Notification
    ).filter(
        models.Notification.id ==
        notification_id,
        models.Notification.user_id ==
        current_user["user_id"]
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = 1

    db.commit()

    return {
        "message": "Notification marked as read"
    }


# =========================================================
# EVENT REMINDERS
# =========================================================

@app.get(
    "/notifications/reminders"
)
def get_event_reminders(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    next_24_hours = (
        now + timedelta(hours=24)
    )

    results = db.query(
        models.Booking,
        models.Event
    ).join(
        models.Event,
        models.Booking.event_id ==
        models.Event.id
    ).filter(
        models.Booking.user_id ==
        current_user["user_id"],
        models.Event.event_date >= now,
        models.Event.event_date <=
        next_24_hours
    ).all()

    reminders = []

    for booking, event in results:
        reminders.append({
            "booking_id": booking.id,
            "event_id": event.id,
            "event_title": event.title,
            "event_date": event.event_date,
            "message": (
                f"Reminder: Your event "
                f"'{event.title}' is within 24 hours."
            )
        })

    return reminders