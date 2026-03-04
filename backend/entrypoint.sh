#!/bin/bash
# entrypoint.sh

# Function to check if PostgreSQL is ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    while ! pg_isready -h $DB_HOST -p 5432 -U $DB_USER -d $DB_NAME > /dev/null 2>&1; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is ready!"
}

# Alternative method using python if pg_isready fails
wait_for_postgres_python() {
    echo "Waiting for PostgreSQL to be ready (Python method)..."
    python -c "
import psycopg
import time
import os
import sys

host = os.environ.get('DB_HOST', 'primepass-primary')
dbname = os.environ.get('DB_NAME', 'primepass_db')
user = os.environ.get('DB_USER', 'appuser')
password = os.environ.get('DB_PASSWORD', 'SecurePassword')

for i in range(30):
    try:
        conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=5432,
            connect_timeout=3
        )
        conn.close()
        print('PostgreSQL is ready!')
        sys.exit(0)
    except psycopg.Error as e:
        print(f'Attempt {i+1}/30: PostgreSQL not ready yet...')
        time.sleep(2)
print('Failed to connect to PostgreSQL')
sys.exit(1)
"
}

# Wait for PostgreSQL using pg_isready (if available) or fallback to Python
if command -v pg_isready &> /dev/null; then
    wait_for_postgres
else
    wait_for_postgres_python
fi

# Initialize database tables
echo "Initializing database tables..."
python init_db.py

# Populate database with sample data
echo "Populating database with sample data..."
python populate_db.py

# Start the Flask application
echo "Starting Flask application..."
python server.py