import os
import sys
import uuid
import datetime
import psycopg
from werkzeug.security import generate_password_hash

def connect_to_postgres():
    try:
        conn = psycopg.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            dbname=os.environ.get("DB_NAME", "primepass_db"),
            user=os.environ.get("DB_USER", "appuser"),
            password=os.environ.get("DB_PASSWORD", "SecurePassword"),
            port=5432
        )
    except psycopg.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def insert_event(cursor, title, venue, city, description, starts_at, ends_at, status):
    cursor.execute("SELECT id FROM event WHERE title = %s", (title,))
    row = cursor.fetchone()
    if row:
        print(f"Event '{title}' already exists.")
        return row[0]

    cursor.execute("""
        INSERT INTO event (title, venue, city, description, starts_at, ends_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (title, venue, city, description, starts_at, ends_at, status))
    event_id = cursor.fetchone()[0]
    print(f"Inserted event '{title}'.")
    return event_id

def insert_ticket(cursor, event_id, name, price, capacity):
    cursor.execute("SELECT id FROM ticket WHERE event_id=%s AND name=%s", (event_id, name))
    if cursor.fetchone():
        print(f"Ticket '{name}' already exists for event {event_id}.")
        return

    cursor.execute("""
        INSERT INTO ticket (event_id, name, price, capacity, remaining)
        VALUES (%s, %s, %s, %s, %s)
    """, (event_id, name, price, capacity, capacity))
    print(f"Inserted ticket '{name}' for event {event_id}.")

def insert_user(cursor):
    email = "demo@primepass.com"
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        print("Demo user already exists.")
        return

    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    password_hash = generate_password_hash("password123")

    cursor.execute("""
        INSERT INTO users (id, name, email, password_hash, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, "demo_user", email, password_hash, "active"))
    print("Inserted demo user.")

def populate():
    conn, cursor = connect_to_postgres()

    event1_id = insert_event(cursor, "Nordic Music Festival", "Central Park Arena", "Helsinki",
                             "A full-day outdoor music festival featuring Nordic artists.",
                             datetime.datetime(2026, 6, 15, 12, 0, 0),
                             datetime.datetime(2026, 6, 15, 23, 0, 0),
                             "active")
    insert_ticket(cursor, event1_id, "Standard", 59.90, 300)
    insert_ticket(cursor, event1_id, "VIP", 129.90, 50)

    event2_id = insert_event(cursor, "Arctic Tech Summit", "Oulu Congress Center", "Oulu",
                             "A two-day technology conference focused on AI and cloud computing.",
                             datetime.datetime(2026, 9, 10, 9, 0, 0),
                             datetime.datetime(2026, 9, 11, 17, 0, 0),
                             "active")
    insert_ticket(cursor, event2_id, "Early Bird", 199.00, 100)
    insert_ticket(cursor, event2_id, "Regular", 299.00, 200)
    insert_ticket(cursor, event2_id, "Student", 99.00, 75)

    insert_user(cursor)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database population complete.")

if __name__ == "__main__":
    populate()