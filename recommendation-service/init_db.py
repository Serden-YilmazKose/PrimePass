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
            database=os.environ.get("DB_NAME", "recommendation_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    return conn, conn.cursor()

def create_tables():
    conn, cursor = connect_to_mariadb()

    # USER_ACTIVITY table – no foreign keys (application ensures consistency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USER_ACTIVITY (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,         -- references USERS.id
        event_id INT NULL,                    -- references EVENT.id
        action VARCHAR(50) NOT NULL,
        meta JSON NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_activity_user_created (user_id, created_at),
        INDEX idx_activity_event_created (event_id, created_at)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Recommendation service tables ensured.")

if __name__ == "__main__":
    create_tables()