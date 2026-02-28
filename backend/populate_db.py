import os
import sys
import uuid
import datetime
import mariadb
from werkzeug.security import generate_password_hash


def connect_to_mariadb():
    try:
        conn = mariadb.connect(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=3306,
            database=os.environ.get("DB_NAME", "primepass_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)

    return conn, conn.cursor()


def insert_event(cursor, title, venue, city, description,
                 starts_at, ends_at, status):

    cursor.execute("SELECT id FROM EVENT WHERE title = ?", (title,))
    row = cursor.fetchone()

    if row:
        print(f"Event '{title}' already exists.")
        return row[0]

    cursor.execute("""
        INSERT INTO EVENT (
            title, venue, city, description,
            starts_at, ends_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title, venue, city, description,
        starts_at, ends_at, status
    ))

    print(f"Inserted event '{title}'.")
    return cursor.lastrowid


def insert_ticket(cursor, event_id, name, price, capacity):
    cursor.execute("""
        SELECT id FROM TICKET
        WHERE event_id = ? AND name = ?
    """, (event_id, name))

    if cursor.fetchone():
        print(f"Ticket '{name}' already exists for event {event_id}.")
        return

    cursor.execute("""
        INSERT INTO TICKET (
            event_id, name, price, capacity, remaining
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        event_id,
        name,
        price,
        capacity,
        capacity
    ))

    print(f"Inserted ticket '{name}' for event {event_id}.")


def insert_user(cursor):
    email = "demo@primepass.com"

    cursor.execute("SELECT id FROM USERS WHERE email = ?", (email,))
    if cursor.fetchone():
        print("Demo user already exists.")
        return

    user_id = "00000000-0000-0000-0000-000000000001"  # fixed UUID
    password_hash = generate_password_hash("password123")

    cursor.execute("""
        INSERT INTO USERS (
            id, name, email, password_hash, status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        "demo_user",
        email,
        password_hash,
        "active"
    ))

    print("Inserted demo user.")


def populate():
    conn, cursor = connect_to_mariadb()

    # ---------------------------
    # EVENT 1: Music Festival
    # ---------------------------
    event1_id = insert_event(
        cursor,
        title="Nordic Music Festival",
        venue="Central Park Arena",
        city="Helsinki",
        description="A full-day outdoor music festival featuring Nordic artists.",
        starts_at=datetime.datetime(2026, 6, 15, 12, 0, 0),
        ends_at=datetime.datetime(2026, 6, 15, 23, 0, 0),
        status="active"
    )

    insert_ticket(cursor, event1_id, "Standard", 59.90, 300)
    insert_ticket(cursor, event1_id, "VIP", 129.90, 50)

    # ---------------------------
    # EVENT 2: Tech Conference
    # ---------------------------
    event2_id = insert_event(
        cursor,
        title="Arctic Tech Summit",
        venue="Oulu Congress Center",
        city="Oulu",
        description="A two-day technology conference focused on AI and cloud computing.",
        starts_at=datetime.datetime(2026, 9, 10, 9, 0, 0),
        ends_at=datetime.datetime(2026, 9, 11, 17, 0, 0),
        status="active"
    )

    insert_ticket(cursor, event2_id, "Early Bird", 199.00, 100)
    insert_ticket(cursor, event2_id, "Regular", 299.00, 200)
    insert_ticket(cursor, event2_id, "Student", 99.00, 75)

    # ---------------------------
    # Demo user
    # ---------------------------
    insert_user(cursor)

    conn.commit()
    cursor.close()
    conn.close()

    print("Database population complete.")


if __name__ == "__main__":
    populate()