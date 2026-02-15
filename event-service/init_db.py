import os
import sys
import pymysql

def get_connection(master=True):
    host = os.environ.get("DB_HOST_MASTER" if master else "DB_HOST_SLAVE", "127.0.0.1")
    try:
        conn = pymysql.connect(
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            host=host,
            port=3306,
            database=os.environ.get("DB_NAME", "primepass_db"),
            charset='utf8mb4'
            # No cursorclass → default tuple cursor
        )
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)

def create_tables():
    conn = get_connection(master=True)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        date DATE NOT NULL,
        available INT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id VARCHAR(36) PRIMARY KEY,
        event_id INT NOT NULL,
        user_id INT NOT NULL,
        quantity INT NOT NULL,
        expires_at DATETIME NOT NULL,
        status ENUM('active', 'completed', 'expired') DEFAULT 'active',
        INDEX (expires_at)
    )
    """)

    # Insert sample events if empty
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO events (name, date, available) VALUES
        ('Rock Concert', '2026-03-12', 50),
        ('Jazz Night', '2026-04-01', 30),
        ('Comedy Show', '2026-05-20', 20)
        """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Event database tables ensured.")