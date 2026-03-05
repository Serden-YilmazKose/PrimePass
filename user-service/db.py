import os, mariadb

def get_db():
    conn = mariadb.connect(
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'pass'),
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=3306,
        database=os.environ.get('DB_NAME', 'user_db')
    )
    return conn, conn.cursor()