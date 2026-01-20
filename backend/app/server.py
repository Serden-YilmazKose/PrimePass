"""Flask API to make GET and POST requests to a MariaDB server"""

import json
import sys
import os
import mariadb
from flask import Flask, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)


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
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    cursor = conn.cursor()
    return conn, cursor


def init_db():
    """Create tables if they do not exist"""
    conn, cursor = connect_to_mariadb()

    # Create VIDEOS table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS VIDEOS (
        id VARCHAR(255) PRIMARY KEY
    )
    """)

    # Create MYTABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MYTABLE (
        id VARCHAR(255) PRIMARY KEY
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables ensured.")


@app.route("/videos", methods=["GET"])
@cross_origin()
def get_block():
    """Handle GET Requests"""
    id_param = request.args.get("id")
    if not id_param:
        return "Missing id parameter", 400
    return select(id_param)


@app.route("/videos", methods=["POST"])
@cross_origin()
def post_block():
    """Handle POST Requests"""
    if not request.json or "id" not in request.json:
        return "Missing id in request body", 400
    return insert(request)


def insert(request_data):
    """Insert a row into MYTABLE"""
    conn, cursor = connect_to_mariadb()
    id_param = request_data.json["id"]

    insert_query = "INSERT INTO VIDEOS (id) VALUES (?)"
    cursor.execute(insert_query, (id_param,))

    conn.commit()
    cursor.close()
    conn.close()
    return "DONE", 201


def select(id_param):
    """Select a row from VIDEOS"""
    conn, cursor = connect_to_mariadb()

    select_query = "SELECT id FROM VIDEOS WHERE id = ?"
    cursor.execute(select_query, (id_param,))

    result = [
        dict((cursor.description[i][0], value) for i, value in enumerate(row))
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    if not result:
        return "Not found", 404
    return json.dumps(result[0])


if __name__ == "__main__":
    # Ensure tables exist before starting Flask
    init_db()
    app.run(host="0.0.0.0", debug=True)
