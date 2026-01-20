"""Flask API to make GET and POST requests to a MariaDB server"""

import json
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from init_db import connect_to_mariadb  # reuse the existing connection function

app = Flask(__name__)
CORS(app)


@app.route("/videos", methods=["GET"])
@cross_origin()
def get_block():
    """Handle GET Requests"""
    video_id = request.args.get("id")
    if not video_id:
        return "Missing id parameter", 400
    return select_video(video_id)


@app.route("/videos", methods=["POST"])
@cross_origin()
def post_block():
    """Handle POST Requests"""
    if not request.is_json:
        return "Request body must be JSON", 400
    data = request.get_json()
    if "id" not in data:
        return "Missing 'id' in request body", 400
    return insert_video(data["id"])


def insert_video(video_id):
    """Insert a row into VIDEOS"""
    conn, cursor = connect_to_mariadb()
    try:
        cursor.execute("INSERT INTO VIDEOS (id) VALUES (?)", (video_id,))
        conn.commit()
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database error: {e}", 500
    cursor.close()
    conn.close()
    return "DONE", 201


def select_video(video_id):
    """Select a row from VIDEOS"""
    conn, cursor = connect_to_mariadb()
    cursor.execute("SELECT id FROM VIDEOS WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return "Not found", 404
    return jsonify({"id": row[0]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
