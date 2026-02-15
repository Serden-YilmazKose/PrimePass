import uuid
from datetime import datetime, timedelta
import threading
import time
import json
import os
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from init_db import get_connection, create_tables
import jwt

app = Flask(__name__)
CORS(app)

create_tables()

redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-change-in-production")

def get_user_id_from_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.InvalidTokenError:
        return None

# -------------------- Event listing --------------------
@app.route("/api/events", methods=["GET"], strict_slashes=False)
def get_events():
    cached = redis_client.get("all_events")
    if cached:
        return jsonify(json.loads(cached))

    conn = get_connection(master=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, date, available FROM events")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    events = [
        {
            "id": row[0],
            "name": row[1],
            "date": row[2].isoformat(),
            "available": row[3],
        }
        for row in rows
    ]

    redis_client.setex("all_events", 30, json.dumps(events))
    return jsonify(events)

# -------------------- Reservation --------------------
@app.route("/api/events/<int:event_id>/reserve", methods=["POST"])
def reserve_tickets(event_id):
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    quantity = data.get("quantity", 1)

    conn = get_connection(master=True)
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute("SELECT available FROM events WHERE id = %s FOR UPDATE", (event_id,))
        row = cursor.fetchone()
        if not row or row[0] < quantity:
            cursor.execute("ROLLBACK")
            return jsonify({"error": "Not enough tickets"}), 400

        new_avail = row[0] - quantity
        cursor.execute("UPDATE events SET available = %s WHERE id = %s", (new_avail, event_id))

        reservation_id = str(uuid.uuid4())
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO reservations (id, event_id, user_id, quantity, expires_at, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (reservation_id, event_id, user_id, quantity, expires_at, 'active')
        )
        conn.commit()
        return jsonify({"reservation_id": reservation_id, "expires_in_minutes": 10})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# -------------------- Purchase --------------------
@app.route("/api/events/purchase", methods=["POST"])
def purchase():
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    reservation_id = data.get("reservation_id")
    payment_token = data.get("payment_token")   # ignored for mock

    conn = get_connection(master=True)
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            "SELECT event_id, quantity, user_id FROM reservations WHERE id = %s AND status = 'active' AND expires_at > NOW() FOR UPDATE",
            (reservation_id,)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute("ROLLBACK")
            return jsonify({"error": "Invalid or expired reservation"}), 400

        event_id, qty, res_user_id = row
        if res_user_id != user_id:
            cursor.execute("ROLLBACK")
            return jsonify({"error": "Reservation does not belong to you"}), 403

        # Mock payment success
        cursor.execute("UPDATE reservations SET status = 'completed' WHERE id = %s", (reservation_id,))
        conn.commit()

        # Log purchase
        log_entry = f"{datetime.utcnow().isoformat()},{user_id},{event_id},{qty}\n"
        with open("/logs/purchases.log", "a") as f:
            f.write(log_entry)

        redis_client.delete("all_events")
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# -------------------- Background expiry job --------------------
def expire_reservations_job():
    while True:
        time.sleep(60)
        conn = get_connection(master=True)
        cursor = conn.cursor()
        try:
            cursor.execute("START TRANSACTION")
            cursor.execute(
                "SELECT id, event_id, quantity FROM reservations WHERE status = 'active' AND expires_at <= NOW() FOR UPDATE"
            )
            expired = cursor.fetchall()
            for res_id, event_id, qty in expired:
                cursor.execute("UPDATE events SET available = available + %s WHERE id = %s", (qty, event_id))
                cursor.execute("UPDATE reservations SET status = 'expired' WHERE id = %s", (res_id,))
            conn.commit()
            if expired:
                redis_client.delete("all_events")
        except Exception as e:
            conn.rollback()
            print(f"Expiry job error: {e}")
        finally:
            cursor.close()
            conn.close()

thread = threading.Thread(target=expire_reservations_job, daemon=True)
thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)