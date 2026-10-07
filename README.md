# SmartEvent – Event Discovery & Ticket Booking System

SmartEvent is a full-stack web application that allows users to discover events, search and filter events, book tickets, view booking history, receive notifications, and access QR-based tickets.

## Features

### User Authentication
- User registration
- User login
- JWT authentication
- Password hashing using bcrypt
- Protected routes
- User profile

### Event Discovery
- View available events
- Search events
- Filter by category
- Sort by date
- Sort by ticket price
- View event details
- Ticket availability status

### Ticket Booking
- Select number of tickets
- Automatic total price calculation
- Ticket availability validation
- Booking confirmation
- Booking history

### QR Ticket System
- Generate QR ticket for each booking
- QR contains booking information
- Users can view their QR ticket from My Bookings

### Notifications
- Booking confirmation notifications
- Unread notification count
- Mark notifications as read
- Upcoming event reminders

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT
- Passlib
- bcrypt
- Uvicorn
- QRCode

### Frontend
- React
- Vite
- JavaScript
- React Router
- Axios
- CSS

## Project Structure

```text
SmartEvent/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── auth.py
│   │
│   ├── smartevent.db
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Events.jsx
│   │   │   ├── EventDetails.jsx
│   │   │   ├── Bookings.jsx
│   │   │   ├── Notifications.jsx
│   │   │   └── Profile.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── index.html
│
└── README.md