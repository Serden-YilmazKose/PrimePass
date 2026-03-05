import os
import pytest
import psycopg
import requests
from threading import Lock
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="session")
def db_conn():
    """Return a connection to the PostgreSQL database (primary)."""
    conn = psycopg.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        dbname=os.environ.get("DB_NAME", "primepass_db"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "SecurePassword"),
        port=5432
    )
    yield conn
    conn.close()

@pytest.fixture
def db_cursor(db_conn):
    """Provide a cursor and automatically roll back after test."""
    cursor = db_conn.cursor()
    yield cursor
    db_conn.rollback()  
    cursor.close()


@pytest.fixture(scope="session")
def base_url():
    """Base URL of the running backend API."""
   
    return os.environ.get("API_URL", "http://localhost:5000")

@pytest.fixture
def api_client(base_url):
    """Return a requests-session prepped with base URL."""
    session = requests.Session()
    session.base_url = base_url
    yield session


@pytest.fixture
def test_user(db_cursor):
    """Create a known test user and return its ID."""
    import uuid
    user_id = str(uuid.uuid4())
    email = f"test_{user_id[:8]}@example.com"
    password = "testpass123"
    pwd_hash = generate_password_hash(password)
    db_cursor.execute(
        "INSERT INTO users (id, name, email, password_hash, status) VALUES (%s, %s, %s, %s, %s)",
        (user_id, "Test User", email, pwd_hash, "active")
    )
    db_cursor.connection.commit()
    return {"id": user_id, "email": email, "password": password}

@pytest.fixture
def test_event(db_cursor):
    """Create a test event and return its ID and ticket IDs."""
    from datetime import datetime, timedelta
    db_cursor.execute("""
        INSERT INTO event (title, venue, city, description, starts_at, ends_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, ("Test Event", "Test Venue", "Test City", "Desc",
          datetime.now(), datetime.now() + timedelta(hours=2), "active"))
    event_id = db_cursor.fetchone()[0]

    
    tickets = {}
    for name, price, cap in [("Standard", 50.0, 10), ("VIP", 100.0, 5)]:
        db_cursor.execute("""
            INSERT INTO ticket (event_id, name, price, capacity, remaining)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (event_id, name, price, cap, cap))
        tickets[name] = db_cursor.fetchone()[0]

    db_cursor.connection.commit()
    return {"event_id": event_id, "tickets": tickets}
