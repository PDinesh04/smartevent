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
SmartEvent Phase 2 backend files

Files:
- main.py: replace backend/app/main.py
- schemas.py: replace backend/app/schemas.py

Prerequisites:
- Keep your existing backend/app/models.py, backend/app/auth.py, and backend/app/database.py.
- models.py must include User.role, Event.organizer_id, Event.event_status and the existing Booking/Notification models.
- auth.py must expose get_current_user, require_user, require_organizer, require_admin, hash_password, verify_password, create_access_token.
- Your database migration should already have added role, organizer_id, event_status to the existing SQLite database.

Install if missing inside the backend virtual environment:
pip install fastapi uvicorn sqlalchemy pydantic[email] python-jose passlib[bcrypt] bcrypt==4.0.1 qrcode[pil]

Run from the backend folder:
uvicorn app.main:app --reload --port 8001

Swagger:
http://127.0.0.1:8001/docs

Important:
1. Back up smartevent.db before testing.
2. Existing user roles remain as stored. Registering new accounts always creates USER accounts.
3. Promote an account using your existing set_user_role.py script. For example, use ORGANIZER to create events, ADMIN for admin endpoints.
4. This package contains backend endpoints only; frontend organizer/admin pages still need to be connected to these APIs.
5. Status rule: past dates become COMPLETED, today's events become ONGOING, future dates become UPCOMING. CANCELLED remains cancelled. Since the schema has no event end time, ONGOING is based on the event date being today.
SmartEvent Phase 2 frontend update

Copy these files into your existing frontend:
- App.jsx -> frontend/src/App.jsx (replace)
- main.jsx -> frontend/src/main.jsx (replace)
- pages/OrganizerDashboard.jsx -> frontend/src/pages/OrganizerDashboard.jsx (new)
- pages/AdminDashboard.jsx -> frontend/src/pages/AdminDashboard.jsx (new)

CSS:
Open frontend/src/App.css and append the entire contents of phase2-dashboard.css.txt to the bottom. Do not replace your existing CSS.

This assumes your existing files remain in place:
- src/pages/Events.jsx
- src/pages/EventDetails.jsx
- src/pages/Bookings.jsx
- src/pages/Notifications.jsx
- src/pages/Profile.jsx
- src/components/ProtectedRoute.jsx

Run backend on port 8001 and frontend with npm run dev.
Login redirect:
- USER -> /events
- ORGANIZER -> /organizer/dashboard
- ADMIN -> /admin/dashboard

Important:
- A new user is registered as USER. Change a registered user's role with your existing backend/set_user_role.py script.
- Organizer dashboard provides event create/edit/cancel, event booking inspection, and organizer analytics.
- Admin dashboard shows metrics, daily/monthly sales tables, popular/top revenue events, users, events, and bookings.
- Date filters expect YYYY-MM-DD.
- Backend APIs must be running on http://127.0.0.1:8001.

