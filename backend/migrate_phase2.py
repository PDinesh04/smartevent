
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "smartevent.db"


def migrate():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        tables = {
            row[0]
            for row in cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table'"
            ).fetchall()
        }

        if "users" not in tables or "events" not in tables:
            raise RuntimeError(
                "Expected users and events tables were not found."
            )

        user_columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        event_columns = {
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(events)"
            ).fetchall()
        }

        if "role" not in user_columns:
            cursor.execute(
                "ALTER TABLE users "
                "ADD COLUMN role TEXT NOT NULL DEFAULT 'USER'"
            )
            print("Added users.role")

        if "organizer_id" not in event_columns:
            cursor.execute(
                "ALTER TABLE events ADD COLUMN organizer_id INTEGER"
            )
            print("Added events.organizer_id")

        if "event_status" not in event_columns:
            cursor.execute(
                "ALTER TABLE events "
                "ADD COLUMN event_status TEXT "
                "NOT NULL DEFAULT 'UPCOMING'"
            )
            print("Added events.event_status")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS "
            "ix_events_organizer_id ON events (organizer_id)"
        )

        connection.commit()
        print("Phase 2 database migration completed.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate()
