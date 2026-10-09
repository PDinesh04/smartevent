
from getpass import getpass

from app.database import SessionLocal
from app.models import User


VALID_ROLES = {"USER", "ORGANIZER", "ADMIN"}


def main():
    email = input("Enter the user's registered email: ").strip()
    role = input("Enter role (USER/ORGANIZER/ADMIN): ").strip().upper()

    if role not in VALID_ROLES:
        print("Invalid role.")
        return

    if role in {"ORGANIZER", "ADMIN"}:
        confirmation = input(
            f"Type {role} to confirm this privileged change: "
        ).strip()

        if confirmation != role:
            print("Role change cancelled.")
            return

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print("User not found. Register that account first.")
            return

        user.role = role
        db.commit()

        print(f"Updated {user.email} to role {user.role}.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
