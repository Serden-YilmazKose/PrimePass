#!/bin/bash
set -e

# Wait for MariaDB to be ready
until mariadb -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &> /dev/null; do
  echo "Waiting for MariaDB..."
  sleep 2
done

# Initialize database
echo "Initializing database..."
python /app/init_db.py

# Start Flask
echo "Starting Flask..."
python /app/server.py