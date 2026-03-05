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
            database=os.environ.get("DB_NAME", "event_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def create_tables():
    conn, cursor = connect_to_mariadb()

    # EVENT table – stores event metadata (no foreign keys)
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

    conn.commit()
    cursor.close()
    conn.close()
    print("Event service tables ensured.")

if __name__ == "__main__":
    create_tables()