import os
import sys
import mariadb

def connect_to_mariadb():
    try:
        conn = mariadb.connect(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=3306,
            database=os.environ.get("DB_NAME", "ticket_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def create_tables():
    conn, cursor = connect_to_mariadb()

    # TICKET table – note: no foreign key to EVENT (enforced by application)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TICKET (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,               -- references EVENT.id in event‑service
        name VARCHAR(255) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        capacity INT NOT NULL,
        remaining INT NOT NULL
    )
    """)

    # ORDERS table – no foreign keys to USERS or TICKET (enforced by application)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ORDERS (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,        -- references USERS.id in user‑service
        ticket_id INT NOT NULL,               -- references TICKET.id
        status VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Ticket service tables ensured.")

if __name__ == "__main__":
    create_tables()