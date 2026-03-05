#!/bin/bash
set -e

until mariadb -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &> /dev/null; do
  echo "Waiting for MariaDB..."
  sleep 2
done

echo "Initializing ticket database..."
python /app/init_db.py

echo "Starting Ticket Service..."
python /app/app.py
