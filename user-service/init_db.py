import os
import sys
import mariadb

def connect_to_mariadb():
    """Connect to MariaDB using environment variables (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)."""
    try:
        conn = mariadb.connect(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=3306,
            database=os.environ.get("DB_NAME", "user_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def create_tables():
    conn, cursor = connect_to_mariadb()

    # USERS table – stores user accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("User service tables ensured.")

if __name__ == "__main__":
    create_tables()