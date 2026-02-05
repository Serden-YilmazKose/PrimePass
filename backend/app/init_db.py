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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EVENTS (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        date DATE NOT NULL,
        available INT NOT NULL
    )
    """)

    # Add data only if table is empty
    cursor.execute("SELECT COUNT(*) FROM EVENTS")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO EVENTS (name, date, available) VALUES
        ('Rock Concert', '2026-03-12', 50),
        ('Jazz Night', '2026-04-01', 30),
        ('Comedy Show', '2026-05-20', 20)
        """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables ensured.")



if __name__ == "__main__":
    create_tables()
