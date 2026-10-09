from datetime import datetime, timedelta, date
from io import BytesIO
from collections import Counter, defaultdict
import os

import qrcode
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    EventCreate,
    EventUpdate,
    EventResponse,
    BookingCreate,
    BookingResponse,
    BookingHistoryResponse,
    NotificationResponse,
)

from .database import Base, engine, get_db
from . import models, schemas
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_user,
    require_organizer,
    require_admin,
)

app = FastAPI(title="SmartEvent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def _create_notification(db: Session, user_id: int, message: str,
                         notification_type: str, booking_id: int | None = None):
    db.add(models.Notification(
        user_id=user_id,
        booking_id=booking_id,
        message=message,
        notification_type=notification_type,
        is_read=0,
    ))


def _notify_event_bookers(db: Session, event, message: str, notification_type: str):
    bookings = db.query(models.Booking).filter(
        models.Booking.event_id == event.id,
        models.Booking.status == "CONFIRMED",
    ).all()
    already_notified = set()
    for booking in bookings:
        if booking.user_id not in already_notified:
            _create_notification(db, booking.user_id, message, notification_type, booking.id)
            already_notified.add(booking.user_id)


def _refresh_event_statuses(db: Session):
    """Derive event status from event_date; preserve explicit cancellations."""
    today = date.today()
    events = db.query(models.Event).filter(models.Event.event_status != "CANCELLED").all()
    changed = False
    for event in events:
        event_day = event.event_date.date()
        if event_day < today:
            status = "COMPLETED"
        elif event_day == today:
            status = "ONGOING"
        else:
            status = "UPCOMING"
        if event.event_status != status:
            event.event_status = status
            changed = True
    if changed:
        db.commit()


def _event_or_404(db: Session, event_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def _check_event_owner(event, current_user):
    if current_user["role"] != "ADMIN" and event.organizer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only manage your own events")


@app.get("/")
def root():
    return {"message": "Welcome to SmartEvent API", "version": "2.0.0"}


# ---------------- AUTH ----------------

@app.post("/auth/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already registered")
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role="USER",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"user_id": db_user.id, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}




@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
    }


# ---------------- PUBLIC EVENT DISCOVERY ----------------

@app.get("/events", response_model=list[schemas.EventResponse])
def get_events(
    category: str | None = None,
    search: str | None = None,
    sort: str = Query(default="date", pattern="^(date|price_asc|price_desc|title)$"),
    db: Session = Depends(get_db),
):
    _refresh_event_statuses(db)
    query = db.query(models.Event).filter(models.Event.event_status != "CANCELLED")
    if category:
        query = query.filter(models.Event.category.ilike(category))
    if search:
        query = query.filter(
            (models.Event.title.ilike(f"%{search}%")) |
            (models.Event.description.ilike(f"%{search}%")) |
            (models.Event.location.ilike(f"%{search}%"))
        )
    if sort == "price_asc":
        query = query.order_by(models.Event.ticket_price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Event.ticket_price.desc())
    elif sort == "title":
        query = query.order_by(models.Event.title.asc())
    else:
        query = query.order_by(models.Event.event_date.asc())
    return query.all()


@app.get("/events/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    _refresh_event_statuses(db)
    event = _event_or_404(db, event_id)
    if event.event_status == "CANCELLED":
        raise HTTPException(status_code=410, detail="This event has been cancelled")
    return event


# ---------------- ORGANIZER EVENT MANAGEMENT ----------------

@app.post("/events", response_model=schemas.EventResponse)
def create_event(
    event: schemas.EventCreate,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
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
        banner_image=event.banner_image,
        organizer_id=current_user["user_id"],
        event_status="UPCOMING",
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event


@app.get("/organizer/events", response_model=list[schemas.EventResponse])
def get_organizer_events(
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    _refresh_event_statuses(db)
    query = db.query(models.Event)
    if current_user["role"] != "ADMIN":
        query = query.filter(models.Event.organizer_id == current_user["user_id"])
    return query.order_by(models.Event.created_at.desc()).all()


@app.put("/events/{event_id}", response_model=schemas.EventResponse)
def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, event_id)
    _check_event_owner(event, current_user)
    if event.event_status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cancelled events cannot be edited")

    updates = event_data.model_dump(exclude_unset=True)
    if "total_tickets" in updates:
        sold = event.total_tickets - event.available_tickets
        if updates["total_tickets"] < sold:
            raise HTTPException(status_code=400, detail="Total tickets cannot be less than tickets already sold")
        event.available_tickets = updates["total_tickets"] - sold

    for field, value in updates.items():
        setattr(event, field, value)
    _notify_event_bookers(db, event, f"Update: '{event.title}' has been updated. Please check the event details.", "EVENT_UPDATED")
    db.commit()
    db.refresh(event)
    return event


@app.patch("/events/{event_id}", response_model=schemas.EventResponse)
def patch_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    return update_event(event_id, event_data, current_user, db)


@app.post("/events/{event_id}/cancel")
def cancel_event(
    event_id: int,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, event_id)
    _check_event_owner(event, current_user)
    if event.event_status == "CANCELLED":
        return {"message": "Event is already cancelled"}
    event.event_status = "CANCELLED"
    _notify_event_bookers(
        db, event,
        f"Cancellation notice: '{event.title}' has been cancelled by the organizer.",
        "EVENT_CANCELLED",
    )
    db.commit()
    return {"message": "Event cancelled and booked users notified", "event_id": event.id}


@app.get("/organizer/events/{event_id}/bookings")
def get_event_bookings(
    event_id: int,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, event_id)
    _check_event_owner(event, current_user)
    rows = db.query(models.Booking).filter(models.Booking.event_id == event_id).order_by(
        models.Booking.booking_date.desc()
    ).all()
    return {
        "event_id": event.id,
        "event_title": event.title,
        "booking_count": len(rows),
        "tickets_sold": sum(b.ticket_count for b in rows if b.status == "CONFIRMED"),
        "revenue": sum(b.total_amount for b in rows if b.status == "CONFIRMED"),
        "bookings": [
            {
                "id": b.id, "user_id": b.user_id, "ticket_count": b.ticket_count,
                "total_amount": b.total_amount, "booking_date": b.booking_date,
                "status": b.status,
            } for b in rows
        ],
    }


@app.get("/organizer/analytics")
def organizer_analytics(
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    query = db.query(models.Event)
    if current_user["role"] != "ADMIN":
        query = query.filter(models.Event.organizer_id == current_user["user_id"])
    events = query.all()
    result = []
    for event in events:
        bookings = db.query(models.Booking).filter(
            models.Booking.event_id == event.id,
            models.Booking.status == "CONFIRMED",
        ).all()
        sold = sum(b.ticket_count for b in bookings)
        revenue = sum(b.total_amount for b in bookings)
        result.append({
            "event_id": event.id, "title": event.title, "event_status": event.event_status,
            "tickets_sold": sold, "tickets_remaining": event.available_tickets,
            "booking_count": len(bookings), "revenue": revenue,
        })
    return {
        "events": result,
        "totals": {
            "events": len(events),
            "tickets_sold": sum(x["tickets_sold"] for x in result),
            "revenue": sum(x["revenue"] for x in result),
            "booking_count": sum(x["booking_count"] for x in result),
        },
    }


# ---------------- BOOKINGS / QR ----------------

@app.post("/bookings", response_model=schemas.BookingResponse)
def create_booking(
    booking: schemas.BookingCreate,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, booking.event_id)
    _refresh_event_statuses(db)
    if event.event_status in {"CANCELLED", "COMPLETED"}:
        raise HTTPException(status_code=400, detail=f"Cannot book an event with status {event.event_status}")
    if booking.ticket_count > event.available_tickets:
        raise HTTPException(status_code=400, detail="Not enough tickets available")
    event.available_tickets -= booking.ticket_count
    new_booking = models.Booking(
        user_id=current_user["user_id"],
        event_id=event.id,
        ticket_count=booking.ticket_count,
        total_amount=event.ticket_price * booking.ticket_count,
        status="CONFIRMED",
    )
    db.add(new_booking)
    db.flush()
    _create_notification(
        db, current_user["user_id"],
        f"Your booking #{new_booking.id} for '{event.title}' has been confirmed.",
        "BOOKING_CONFIRMED", new_booking.id,
    )
    db.commit()
    db.refresh(new_booking)
    return new_booking


@app.get("/bookings", response_model=list[schemas.BookingHistoryResponse])
def get_my_bookings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(models.Booking).filter(
        models.Booking.user_id == current_user["user_id"]
    ).order_by(models.Booking.booking_date.desc()).all()


@app.get("/bookings/{booking_id}/qr")
def generate_booking_qr(
    booking_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user["role"] != "ADMIN" and booking.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You cannot view another user's ticket")
    qr_data = (
        f"SmartEvent Ticket\nBooking ID: {booking.id}\nEvent ID: {booking.event_id}\n"
        f"Tickets: {booking.ticket_count}\nStatus: {booking.status}"
    )
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


# ---------------- NOTIFICATIONS / REMINDERS ----------------

@app.get("/notifications", response_model=list[schemas.NotificationResponse])
def get_notifications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(
        models.Notification.user_id == current_user["user_id"]
    ).order_by(models.Notification.created_at.desc()).all()


@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user["user_id"],
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = 1
    db.commit()
    return {"message": "Notification marked as read"}


@app.get("/notifications/reminders")
def get_event_reminders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    end = now + timedelta(hours=24)
    rows = db.query(models.Booking, models.Event).join(
        models.Event, models.Booking.event_id == models.Event.id
    ).filter(
        models.Booking.user_id == current_user["user_id"],
        models.Booking.status == "CONFIRMED",
        models.Event.event_status != "CANCELLED",
        models.Event.event_date >= now,
        models.Event.event_date <= end,
    ).all()
    return [{
        "booking_id": booking.id, "event_id": event.id, "event_title": event.title,
        "event_date": event.event_date,
        "message": f"Reminder: '{event.title}' is within 24 hours.",
    } for booking, event in rows]


# ---------------- ADMIN DASHBOARD ----------------

@app.get("/admin/users", response_model=list[schemas.UserResponse])
def admin_users(current_user=Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@app.get("/admin/events", response_model=list[schemas.EventResponse])
def admin_events(
    status: str | None = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    _refresh_event_statuses(db)
    query = db.query(models.Event)
    if status:
        query = query.filter(models.Event.event_status == status.upper())
    return query.order_by(models.Event.created_at.desc()).all()


@app.get("/admin/bookings")
def admin_bookings(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.Booking)
    if start_date:
        query = query.filter(models.Booking.booking_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(models.Booking.booking_date < datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
    rows = query.order_by(models.Booking.booking_date.desc()).all()
    return [{
        "id": b.id, "user_id": b.user_id, "event_id": b.event_id,
        "ticket_count": b.ticket_count, "total_amount": b.total_amount,
        "booking_date": b.booking_date, "status": b.status,
    } for b in rows]


@app.get("/admin/analytics")
def admin_analytics(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    _refresh_event_statuses(db)
    booking_query = db.query(models.Booking)
    if start_date:
        booking_query = booking_query.filter(
            models.Booking.booking_date >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        booking_query = booking_query.filter(
            models.Booking.booking_date < datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        )
    bookings = booking_query.all()
    confirmed = [b for b in bookings if b.status == "CONFIRMED"]
    event_count = db.query(models.Event).count()
    user_count = db.query(models.User).count()
    tickets_sold = sum(b.ticket_count for b in confirmed)
    revenue = sum(b.total_amount for b in confirmed)

    daily = defaultdict(lambda: {"tickets_sold": 0, "bookings": 0, "revenue": 0})
    monthly = defaultdict(lambda: {"bookings": 0, "revenue": 0})
    event_stats = defaultdict(lambda: {"tickets_sold": 0, "bookings": 0, "revenue": 0})
    for b in confirmed:
        day_key = b.booking_date.strftime("%Y-%m-%d")
        month_key = b.booking_date.strftime("%Y-%m")
        daily[day_key]["tickets_sold"] += b.ticket_count
        daily[day_key]["bookings"] += 1
        daily[day_key]["revenue"] += b.total_amount
        monthly[month_key]["bookings"] += 1
        monthly[month_key]["revenue"] += b.total_amount
        event_stats[b.event_id]["tickets_sold"] += b.ticket_count
        event_stats[b.event_id]["bookings"] += 1
        event_stats[b.event_id]["revenue"] += b.total_amount

    event_ids = list(event_stats.keys())
    event_map = {}
    if event_ids:
        event_map = {e.id: e.title for e in db.query(models.Event).filter(models.Event.id.in_(event_ids)).all()}
    popular = sorted(
        [{"event_id": eid, "title": event_map.get(eid, "Deleted event"), **stats}
         for eid, stats in event_stats.items()],
        key=lambda x: x["tickets_sold"], reverse=True,
    )
    top_revenue = sorted(popular, key=lambda x: x["revenue"], reverse=True)
    return {
        "totals": {
            "users": user_count, "events": event_count, "bookings": len(confirmed),
            "tickets_sold": tickets_sold, "revenue": revenue,
        },
        "daily_ticket_sales": [{"date": k, **v} for k, v in sorted(daily.items())],
        "monthly_booking_trends": [{"month": k, **v} for k, v in sorted(monthly.items())],
        "popular_events": popular[:10],
        "top_revenue_events": top_revenue[:10],
        "filters": {"start_date": start_date, "end_date": end_date},
    }
