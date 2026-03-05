import os
import sys
import psycopg

def _connect(host):
    """Internal helper to connect to a specific PostgreSQL host."""
    try:
        conn = psycopg.connect(
            host=host,
            dbname=os.environ.get("DB_NAME", "primepass_db"),
            user=os.environ.get("DB_USER", "appuser"),
            password=os.environ.get("DB_PASSWORD", "SecurePassword"),
            port=5432
        )
    except psycopg.Error as e:
        print(f"Error connecting to PostgreSQL at {host}: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def connect_primary():
    """Connect to the primary database (writes)."""
    return _connect(os.environ.get("DB_HOST", "primepass-primary"))

def connect_replica():
    """Connect to the replica database (reads)."""
    return _connect(os.environ.get("DB_REPLICA_HOST", "primepass-replica"))


connect_to_postgres = connect_primary

def create_tables():
    conn, cursor = connect_primary()  
   
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        venue VARCHAR(255) NOT NULL,
        city VARCHAR(255) NOT NULL,
        description TEXT,
        starts_at TIMESTAMP NOT NULL,
        ends_at TIMESTAMP NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket (
        id SERIAL PRIMARY KEY,
        event_id INT NOT NULL REFERENCES event(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        price NUMERIC(10,2) NOT NULL,
        capacity INT NOT NULL,
        remaining INT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        ticket_id INT NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
        status VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        event_id INT NULL REFERENCES event(id) ON DELETE SET NULL,
        action VARCHAR(50) NOT NULL,
        meta JSON NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables ensured.")

if __name__ == "__main__":
    create_tables()
