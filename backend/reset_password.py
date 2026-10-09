from app.database import SessionLocal
from app import models
from app.auth import hash_password

db = SessionLocal()

email = "bobby1@gmail.com"
new_password = "Organizer@123"

user = db.query(models.User).filter(
    models.User.email == email
).first()

if user:
    user.hashed_password = hash_password(new_password)
    db.commit()
    print("Password reset successfully.")
else:
    print("User not found.")

db.close()