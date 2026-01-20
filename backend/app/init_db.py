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
            database=os.environ.get("DB_NAME", "primepass_db")
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        sys.exit(1)
    cursor = conn.cursor()
    return conn, cursor

def create_tables():
    conn, cursor = connect_to_mariadb()

    # Create VIDEOS table if it does not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS VIDEOS (
        id VARCHAR(255) PRIMARY KEY
    )
    """)

    # Create MYTABLE if it does not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MYTABLE (
        id VARCHAR(255) PRIMARY KEY
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables ensured.")

if __name__ == "__main__":
    create_tables()
