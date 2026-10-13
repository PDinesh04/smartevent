import sqlite3

conn = sqlite3.connect("smartevent.db")
cursor = conn.cursor()

def add_column(table, definition):
    name = definition.split()[0]
    columns = [
        row[1] for row in cursor.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]
    if name not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        print(f"Added {table}.{name}")

add_column("bookings", "coupon_id INTEGER")
add_column("bookings", "discount_amount INTEGER NOT NULL DEFAULT 0")
add_column("bookings", "final_amount INTEGER NOT NULL DEFAULT 0")

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    transaction_id VARCHAR(100) UNIQUE,
    amount INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS coupons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coupon_code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL,
    discount_value REAL NOT NULL,
    minimum_booking_amount INTEGER NOT NULL DEFAULT 0,
    expiry_date DATETIME,
    usage_limit INTEGER NOT NULL DEFAULT 100,
    usage_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    review_text VARCHAR(1000),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Preserve old confirmed bookings.
cursor.execute("""
UPDATE bookings
SET final_amount = total_amount
WHERE final_amount = 0 AND discount_amount = 0
""")

conn.commit()
conn.close()
print("Modules 12–16 database migration completed.")