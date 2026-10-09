from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    category: str = Field(min_length=1, max_length=50)
    location: str = Field(min_length=1, max_length=200)
    event_date: datetime
    ticket_price: int = Field(ge=0)
    total_tickets: int = Field(default=100, gt=0)
    banner_image: str | None = Field(default=None, max_length=500)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    location: str | None = Field(default=None, min_length=1, max_length=200)
    event_date: datetime | None = None
    ticket_price: int | None = Field(default=None, ge=0)
    total_tickets: int | None = Field(default=None, gt=0)
    banner_image: str | None = Field(default=None, max_length=500)


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
    organizer_id: int | None = None
    event_status: str = "UPCOMING"
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    event_id: int
    ticket_count: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    ticket_count: int
    total_amount: int
    booking_date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)


class BookingHistoryResponse(BaseModel):
    id: int
    event_id: int
    ticket_count: int
    total_amount: int
    booking_date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    booking_id: int | None
    message: str
    notification_type: str
    is_read: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
