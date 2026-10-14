from datetime import datetime, timedelta, date
from io import BytesIO
from collections import Counter, defaultdict
import uuid
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
    location: str | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    start_date: date | None = None,
    end_date: date | None = None,
    sort: str = Query(
        default="date",
        pattern="^(date|price_asc|price_desc|title|popularity)$"
    ),
    db: Session = Depends(get_db),
):
    _refresh_event_statuses(db)

    query = db.query(models.Event).filter(
        models.Event.event_status != "CANCELLED"
    )

    if category:
        query = query.filter(
            models.Event.category.ilike(f"%{category.strip()}%")
        )

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (models.Event.title.ilike(term)) |
            (models.Event.description.ilike(term)) |
            (models.Event.location.ilike(term))
        )

    if location:
        query = query.filter(
            models.Event.location.ilike(f"%{location.strip()}%")
        )

    if min_price is not None:
        query = query.filter(models.Event.ticket_price >= min_price)

    if max_price is not None:
        query = query.filter(models.Event.ticket_price <= max_price)

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=400,
            detail="min_price cannot exceed max_price"
        )

    if start_date:
        query = query.filter(
            models.Event.event_date >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query = query.filter(
            models.Event.event_date < datetime.combine(
                end_date + timedelta(days=1), datetime.min.time()
            )
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    if sort == "price_asc":
        query = query.order_by(models.Event.ticket_price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Event.ticket_price.desc())
    elif sort == "title":
        query = query.order_by(models.Event.title.asc())
    elif sort == "popularity":
        booking_counts = (
            db.query(
                models.Booking.event_id,
                func.sum(models.Booking.ticket_count).label("tickets_sold")
            )
            .filter(models.Booking.status == "CONFIRMED")
            .group_by(models.Booking.event_id)
            .subquery()
        )
        query = query.outerjoin(
            booking_counts,
            models.Event.id == booking_counts.c.event_id
        ).order_by(
            func.coalesce(booking_counts.c.tickets_sold, 0).desc(),
            models.Event.event_date.asc()
        )
    else:
        query = query.order_by(models.Event.event_date.asc())

    return query.all()

@app.get("/events/recommendations")
def get_event_recommendations(
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    booked_categories = (
        db.query(models.Event.category)
        .join(models.Booking, models.Booking.event_id == models.Event.id)
        .filter(
            models.Booking.user_id == current_user["user_id"],
            models.Booking.status == "CONFIRMED",
        )
        .distinct()
        .all()
    )

    categories = [row[0] for row in booked_categories]

    query = db.query(models.Event).filter(
        models.Event.event_status == "UPCOMING",
        models.Event.available_tickets > 0,
    )

    if categories:
        query = query.filter(models.Event.category.in_(categories))

    booked_event_ids = (
        db.query(models.Booking.event_id)
        .filter(
            models.Booking.user_id == current_user["user_id"],
            models.Booking.status == "CONFIRMED",
        )
        .subquery()
    )

    return (
        query.filter(~models.Event.id.in_(booked_event_ids))
        .order_by(models.Event.event_date.asc())
        .limit(10)
        .all()
    )


# ---------------- GET SINGLE EVENT ----------------

@app.get("/events/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    _refresh_event_statuses(db)

    event = _event_or_404(db, event_id)

    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=410,
            detail="This event has been cancelled",
        )

    return event


# ---------------- ORGANIZER EVENT MANAGEMENT ----------------

@app.post("/book/events", response_model=schemas.EventResponse)
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

@app.post("/bookings/checkout")
def checkout_booking(
    data: schemas.BookingCheckout,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        _refresh_event_statuses(db)

        # Atomically reserve tickets to prevent overbooking
        result = db.query(models.Event).filter(
            models.Event.id == data.event_id,
            models.Event.available_tickets >= data.ticket_count,
            ~models.Event.event_status.in_(["CANCELLED", "COMPLETED"]),
        ).update(
            {
                models.Event.available_tickets:
                    models.Event.available_tickets - data.ticket_count
            },
            synchronize_session=False,
        )

        if result == 0:
            db.rollback()
            event = _event_or_404(db, data.event_id)

            if event.event_status in {"CANCELLED", "COMPLETED"}:
                raise HTTPException(
                    status_code=400,
                    detail="Event is not available for booking",
                )

            raise HTTPException(
                status_code=400,
                detail="Not enough tickets available",
            )

        event = _event_or_404(db, data.event_id)

        total = event.ticket_price * data.ticket_count
        discount = 0
        coupon = None

        if data.coupon_code:
            coupon = db.query(models.Coupon).filter(
                models.Coupon.coupon_code
                == data.coupon_code.strip().upper()
            ).first()

            if not coupon or not coupon.is_active:
                raise HTTPException(400, "Invalid coupon")

            if coupon.expiry_date and coupon.expiry_date < datetime.utcnow():
                raise HTTPException(400, "Coupon has expired")

            if coupon.usage_count >= coupon.usage_limit:
                raise HTTPException(400, "Coupon usage limit reached")

            if total < coupon.minimum_booking_amount:
                raise HTTPException(400, "Minimum booking amount not met")

            if coupon.discount_type == "PERCENTAGE":
                discount = int(total * coupon.discount_value / 100)
            elif coupon.discount_type == "FIXED":
                discount = int(coupon.discount_value)
            else:
                raise HTTPException(400, "Invalid coupon configuration")

            discount = min(discount, total)

        final_amount = total - discount

        booking = models.Booking(
            user_id=current_user["user_id"],
            event_id=event.id,
            ticket_count=data.ticket_count,
            total_amount=total,
            status="PENDING",
            coupon_id=coupon.id if coupon else None,
            discount_amount=discount,
            final_amount=final_amount,
        )

        db.add(booking)
        db.flush()

        payment = models.Payment(
            booking_id=booking.id,
            payment_method="SIMULATED",
            payment_status="PENDING",
            amount=final_amount,
        )
        db.add(payment)

        if coupon:
            coupon.usage_count += 1

        db.commit()
        db.refresh(booking)

        return {
            "booking_id": booking.id,
            "payment_id": payment.id,
            "event_title": event.title,
            "ticket_count": booking.ticket_count,
            "total_amount": total,
            "discount_amount": discount,
            "final_amount": final_amount,
            "booking_status": booking.status,
            "payment_status": payment.payment_status,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Booking failed. Please try again.",
        )

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
@app.post("/payments/{booking_id}")
def simulate_payment(
    booking_id: int,
    data: schemas.PaymentRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        booking = db.query(models.Booking).filter(
            models.Booking.id == booking_id,
            models.Booking.user_id == current_user["user_id"],
        ).with_for_update().first()

        if not booking:
            raise HTTPException(404, "Booking not found")

        if booking.status != "PENDING":
            raise HTTPException(400, "Booking is not pending payment")

        payment = db.query(models.Payment).filter(
            models.Payment.booking_id == booking_id,
            models.Payment.payment_status == "PENDING",
        ).first()

        if not payment:
            raise HTTPException(404, "Pending payment not found")

        event = _event_or_404(db, booking.event_id)

        payment.transaction_id = (
            "SIM-" + uuid.uuid4().hex[:16].upper()
        )

        if data.simulate_success:
            payment.payment_status = "SUCCESS"
            booking.status = "CONFIRMED"

            _create_notification(
                db,
                booking.user_id,
                f"Payment successful for booking #{booking.id}.",
                "PAYMENT_SUCCESS",
                booking.id,
            )
            message = "Payment successful"

        else:
            payment.payment_status = "FAILED"
            booking.status = "FAILED"
            event.available_tickets += booking.ticket_count

            _create_notification(
                db,
                booking.user_id,
                f"Payment failed for booking #{booking.id}.",
                "PAYMENT_FAILED",
                booking.id,
            )
            message = "Payment failed"

        db.commit()

        return {
            "message": message,
            "booking_id": booking.id,
            "booking_status": booking.status,
            "payment_status": payment.payment_status,
            "transaction_id": payment.transaction_id,
            "amount": payment.amount,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Payment processing failed. Please try again.",
        )
@app.post("/admin/coupons")
def create_coupon(
    data: schemas.CouponCreate,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    code = data.coupon_code.strip().upper()

    if data.discount_type not in {"PERCENTAGE", "FIXED"}:
        raise HTTPException(400, "Use PERCENTAGE or FIXED")

    if data.discount_type == "PERCENTAGE" and data.discount_value > 100:
        raise HTTPException(400, "Percentage cannot exceed 100")

    if db.query(models.Coupon).filter(
        models.Coupon.coupon_code == code
    ).first():
        raise HTTPException(400, "Coupon already exists")

    coupon = models.Coupon(
        coupon_code=code,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        minimum_booking_amount=data.minimum_booking_amount,
        expiry_date=data.expiry_date,
        usage_limit=data.usage_limit,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return {"message": "Coupon created", "coupon_id": coupon.id, "coupon_code": code}
@app.post("/coupons/validate")
def validate_coupon(
    data: schemas.CouponApply,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    coupon = db.query(models.Coupon).filter(
        models.Coupon.coupon_code == data.coupon_code.strip().upper()
    ).first()

    if not coupon or not coupon.is_active:
        raise HTTPException(400, "Invalid coupon code")

    if coupon.expiry_date and coupon.expiry_date < datetime.utcnow():
        raise HTTPException(400, "Coupon has expired")

    if coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(400, "Coupon usage limit reached")

    if data.amount < coupon.minimum_booking_amount:
        raise HTTPException(400, "Minimum booking amount not met")

    if coupon.discount_type.upper() == "PERCENTAGE":
        discount = int(data.amount * coupon.discount_value / 100)
    elif coupon.discount_type.upper() == "FIXED":
        discount = int(coupon.discount_value)
    else:
        raise HTTPException(400, "Invalid coupon configuration")

    discount = min(discount, data.amount)

    return {
        "coupon_code": coupon.coupon_code,
        "discount_amount": discount,
        "final_amount": data.amount - discount,
    }

# ---------------- EVENT REVIEWS & RATINGS ----------------

from sqlalchemy import func


@app.post("/events/{event_id}/reviews")
def create_review(
    event_id: int,
    data: schemas.ReviewCreate,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, event_id)

    # Only users with a confirmed booking can review an event.
    booking = db.query(models.Booking).filter(
        models.Booking.event_id == event_id,
        models.Booking.user_id == current_user["user_id"],
        models.Booking.status == "CONFIRMED",
    ).first()

    if not booking:
        raise HTTPException(
            status_code=403,
            detail="You must have a confirmed booking to review this event",
        )

    existing = db.query(models.Review).filter(
        models.Review.event_id == event_id,
        models.Review.user_id == current_user["user_id"],
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this event",
        )

    review = models.Review(
        user_id=current_user["user_id"],
        event_id=event.id,
        rating=data.rating,
        review_text=data.comment,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "message": "Review submitted successfully",
        "review_id": review.id,
        "event_id": review.event_id,
        "rating": review.rating,
        "review_text": review.review_text,
    }


@app.get("/events/{event_id}/reviews")
def get_event_reviews(
    event_id: int,
    db: Session = Depends(get_db),
):
    _event_or_404(db, event_id)

    reviews = db.query(models.Review).filter(
        models.Review.event_id == event_id
    ).order_by(models.Review.created_at.desc()).all()

    average_rating = db.query(
        func.avg(models.Review.rating)
    ).filter(
        models.Review.event_id == event_id
    ).scalar()

    return {
        "event_id": event_id,
        "average_rating": round(average_rating or 0, 2),
        "total_reviews": len(reviews),
        "reviews": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "rating": review.rating,
                "review_text": review.review_text,
                "created_at": review.created_at,
            }
            for review in reviews
        ],
    }


@app.put("/reviews/{review_id}")
def update_review(
    review_id: int,
    data: schemas.ReviewCreate,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    review = db.query(models.Review).filter(
        models.Review.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own review",
        )

    review.rating = data.rating
    review.review_text = data.comment

    db.commit()
    db.refresh(review)

    return {"message": "Review updated successfully", "review_id": review.id}


@app.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    review = db.query(models.Review).filter(
        models.Review.id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own review",
        )

    db.delete(review)
    db.commit()

    return {"message": "Review deleted successfully"}


# ---------------- WISHLIST ----------------

@app.post("/wishlist")
def add_to_wishlist(
    data: schemas.WishlistCreate,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, data.event_id)

    existing = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user["user_id"],
        models.Wishlist.event_id == data.event_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Event already in wishlist")

    item = models.Wishlist(
        user_id=current_user["user_id"],
        event_id=event.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"message": "Event added to wishlist", "wishlist_id": item.id}


@app.get("/wishlist")
def get_wishlist(
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    items = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user["user_id"]
    ).order_by(models.Wishlist.created_at.desc()).all()

    return [
        {
            "id": item.id,
            "event_id": item.event_id,
            "created_at": item.created_at,
            "event": db.query(models.Event).filter(
                models.Event.id == item.event_id
            ).first(),
        }
        for item in items
    ]


@app.delete("/wishlist/{event_id}")
def remove_from_wishlist(
    event_id: int,
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
):
    item = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user["user_id"],
        models.Wishlist.event_id == event_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    db.delete(item)
    db.commit()
    return {"message": "Event removed from wishlist"}

# ---------------- LIVE EVENT UPDATES ----------------

@app.post("/events/updates")
def create_event_update(
    data: schemas.EventUpdateCreate,
    current_user=Depends(require_organizer),
    db: Session = Depends(get_db),
):
    event = _event_or_404(db, data.event_id)
    _check_event_owner(event, current_user)

    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    update = models.EventUpdate(
        event_id=event.id,
        message=message,
    )
    db.add(update)
    db.commit()
    db.refresh(update)

    return {
        "message": "Event update posted successfully",
        "update_id": update.id,
        "event_id": update.event_id,
        "announcement": update.message,
        "created_at": update.created_at,
    }


@app.get("/events/{event_id}/updates")
def get_event_updates(
    event_id: int,
    db: Session = Depends(get_db),
):
    _event_or_404(db, event_id)

    updates = db.query(models.EventUpdate).filter(
        models.EventUpdate.event_id == event_id
    ).order_by(models.EventUpdate.created_at.desc()).all()

    return updates

# ---------------- USER PROFILE ----------------

@app.get("/profile")
def get_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(
        models.User.id == current_user["user_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    booking_count = db.query(models.Booking).filter(
        models.Booking.user_id == user.id
    ).count()

    confirmed_bookings = db.query(models.Booking).filter(
        models.Booking.user_id == user.id,
        models.Booking.status == "CONFIRMED",
    ).all()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
        "total_bookings": booking_count,
        "confirmed_bookings": len(confirmed_bookings),
        "tickets_booked": sum(b.ticket_count for b in confirmed_bookings),
    }


@app.put("/profile")
def update_profile(
    data: schemas.ProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(
        models.User.id == current_user["user_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = data.model_dump(exclude_unset=True)

    if "username" in updates:
        username = updates["username"].strip()
        if not username:
            raise HTTPException(status_code=400, detail="Username cannot be empty")
        duplicate = db.query(models.User).filter(
            models.User.username == username,
            models.User.id != user.id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = username

    if "email" in updates:
        email = updates["email"].strip().lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email cannot be empty")
        duplicate = db.query(models.User).filter(
            models.User.email == email,
            models.User.id != user.id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = email

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "username": user.username,
        "email": user.email,
    }

# ---------------- SMART EVENT CHATBOT ----------------

@app.post("/chatbot", response_model=schemas.ChatbotResponse)
def chatbot(
    data: schemas.ChatbotRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = data.message.strip().lower()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if any(word in message for word in ["booking", "bookings", "my tickets"]):
        bookings = db.query(models.Booking).filter(
            models.Booking.user_id == current_user["user_id"]
        ).order_by(models.Booking.booking_date.desc()).limit(10).all()

        if not bookings:
            reply = "You don't have any bookings yet."
        else:
            reply = "Here are your recent bookings:\n" + "\n".join(
                f"Booking #{b.id}: Event ID {b.event_id}, "
                f"{b.ticket_count} tickets, status {b.status}"
                for b in bookings
            )

        return {
            "reply": reply,
            "suggestions": ["Trending events", "Find technology events"],
        }

    if any(word in message for word in ["trending", "popular"]):
        popular = (
            db.query(
                models.Event,
                func.coalesce(func.sum(models.Booking.ticket_count), 0).label("tickets_sold"),
            )
            .outerjoin(
                models.Booking,
                (models.Booking.event_id == models.Event.id)
                & (models.Booking.status == "CONFIRMED"),
            )
            .filter(models.Event.event_status != "CANCELLED")
            .group_by(models.Event.id)
            .order_by(func.coalesce(func.sum(models.Booking.ticket_count), 0).desc())
            .limit(5)
            .all()
        )

        if not popular:
            reply = "There are no events available right now."
        else:
            reply = "Trending events:\n" + "\n".join(
                f"{event.title} — {event.location}, "
                f"₹{event.ticket_price}, {event.available_tickets} tickets left"
                for event, _ in popular
            )

        return {
            "reply": reply,
            "suggestions": ["Show my bookings", "Find music events"],
        }

    if any(word in message for word in ["near me", "nearby", "location"]):
        events = db.query(models.Event).filter(
            models.Event.event_status == "UPCOMING"
        ).order_by(models.Event.event_date.asc()).limit(5).all()

        reply = (
            "I can't access your exact location. Here are upcoming events "
            "you can browse by location:\n"
            + "\n".join(
                f"{e.title} — {e.location}, ₹{e.ticket_price}"
                for e in events
            )
        ) if events else "No upcoming events were found."

        return {
            "reply": reply,
            "suggestions": ["Trending events", "Show my bookings"],
        }

    if "music" in message or "technology" in message or "sports" in message:
        category = next(
            word for word in ["music", "technology", "sports"]
            if word in message
        )

        events = db.query(models.Event).filter(
            models.Event.category.ilike(f"%{category}%"),
            models.Event.event_status == "UPCOMING",
        ).order_by(models.Event.event_date.asc()).limit(5).all()

        reply = (
            f"Events in {category}:\n" + "\n".join(
                f"{e.title} — {e.location}, ₹{e.ticket_price}"
                for e in events
            )
        ) if events else f"No upcoming {category} events were found."

        return {
            "reply": reply,
            "suggestions": ["Trending events", "Show my bookings"],
        }

    return {
        "reply": (
            "Welcome to SmartEvent! I can help you find events, "
            "view trending events, check your bookings, or answer basic questions "
            "about tickets. What would you like to do?"
        ),
        "suggestions": [
            "Trending events",
            "Find music events",
            "Show my bookings",
            "Help with ticket issues",
        ],
    }



