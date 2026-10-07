from datetime import datetime
from pydantic import BaseModel, EmailStr


# ---------------- USER ----------------

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ---------------- EVENT ----------------

class EventCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    event_date: datetime
    ticket_price: int
    total_tickets: int = 100
    banner_image: str | None = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: str
    event_date: datetime
    ticket_price: int
    total_tickets: int
    available_tickets: int
    banner_image: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------- BOOKING ----------------

class BookingCreate(BaseModel):
    event_id: int
    ticket_count: int


class BookingResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    ticket_count: int
    total_amount: int
    booking_date: datetime
    status: str

    class Config:
        from_attributes = True


class BookingHistoryResponse(BaseModel):
    id: int
    event_id: int
    ticket_count: int
    total_amount: int
    booking_date: datetime
    status: str

    class Config:
        from_attributes = True
# ---------------- NOTIFICATION ----------------

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    booking_id: int | None
    message: str
    notification_type: str
    is_read: int
    created_at: datetime

    class Config:
        from_attributes = True