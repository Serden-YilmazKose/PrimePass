import os
import sys
import psycopg

def connect_to_postgres():
    """Connect to PostgreSQL using environment variables"""
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

def create_tables():
    conn, cursor = connect_to_postgres()

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

    # USER_ACTIVITY TABLE
    cursor.execute("""CREATE TABLE IF NOT EXISTS `USER_ACTIVITY` (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        event_id INT NULL,
        action VARCHAR(50) NOT NULL,
        meta JSON NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_activity_user_created (user_id, created_at),
        INDEX idx_activity_event_created (event_id, created_at),
        CONSTRAINT fk_user_activity_user
            FOREIGN KEY (user_id)
            REFERENCES USERS(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_user_activity_event
            FOREIGN KEY (event_id)
            REFERENCES EVENT(id)
            ON DELETE SET NULL
    )
    """) 

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables ensured.")

if __name__ == "__main__":
    create_tables()