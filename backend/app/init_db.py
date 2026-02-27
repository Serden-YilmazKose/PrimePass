import os
import sys

import mariadb


def connect_to_mariadb():
    """Connect to MariaDB using environment variables"""
    try:
        conn = mariadb.connect(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=3306,
            database=os.environ.get("DB_NAME", "mariadb_primary")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    cursor = conn.cursor()
    return conn, cursor


def create_tables():
    conn, cursor = connect_to_mariadb()

    # EVENT TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EVENT (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        venue VARCHAR(255) NOT NULL,
        city VARCHAR(255) NOT NULL,
        description TEXT,
        starts_at DATETIME NOT NULL,
        ends_at DATETIME NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # USER TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USER (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # TICKET TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TICKET (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        capacity INT NOT NULL,
        remaining INT NOT NULL,
        CONSTRAINT fk_ticket_event
            FOREIGN KEY (event_id)
            REFERENCES EVENT(id)
            ON DELETE CASCADE
    )
    """)

    # ORDER TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `ORDER` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        ticket_id INT NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_order_user
            FOREIGN KEY (user_id)
            REFERENCES USER(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_order_ticket
            FOREIGN KEY (ticket_id)
            REFERENCES TICKET(id)
            ON DELETE CASCADE
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables ensured.")


if __name__ == "__main__":
    create_tables()
