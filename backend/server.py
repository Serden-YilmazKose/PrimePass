"""Flask API for ticket sales using MariaDB with logging, tracing, and caching"""
import uuid
import mariadb
import time
import logging

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from init_db import connect_to_mariadb

app = Flask(__name__)

# CENTRALIZED LOGGING 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("ticket-service")

# SIMPLE IN-MEMORY CACHE 
cache = {}
CACHE_EXPIRATION = 10  

# HELPER FUNCTION 
def get_trace_id():
    trace_id = request.headers.get("X-Trace-ID")
    if not trace_id:
        trace_id = str(uuid.uuid4())
    return trace_id

#  ENDPOINTS 
@app.route("/api/events", methods=["GET"])
def get_events():
    trace_id = get_trace_id()
    logger.info(f"[TraceID: {trace_id}] Request received for all events")

    # Check cache first
    if "events" in cache:
        cached_data, timestamp = cache["events"]
        if time.time() - timestamp < CACHE_EXPIRATION:
            logger.info(f"[TraceID: {trace_id}] Returning cached events")
            return jsonify(cached_data)
        else:
            logger.info(f"[TraceID: {trace_id}] Cache expired")
            del cache["events"]

    conn, cursor = connect_to_mariadb()
    try:
        logger.info(f"[TraceID: {trace_id}] Fetching events from database")
        cursor.execute("""
            SELECT
                e.id,
                e.title,
                e.venue,
                e.city,
                e.starts_at,
                e.ends_at,
                e.status,
                t.id,
                t.name,
                t.price,
                t.remaining
            FROM EVENT e
            LEFT JOIN TICKET t ON e.id = t.event_id
            ORDER BY e.id
        """)
        rows = cursor.fetchall()

        events_dict = {}
        for row in rows:
            event_id = row[0]
            if event_id not in events_dict:
                events_dict[event_id] = {
                    "id": event_id,
                    "title": row[1],
                    "venue": row[2],
                    "city": row[3],
                    "starts_at": row[4].isoformat() if row[4] else None,
                    "ends_at": row[5].isoformat() if row[5] else None,
                    "status": row[6],
                    "tickets": []
                }
            ticket_id = row[7]
            if ticket_id:
                events_dict[event_id]["tickets"].append({
                    "id": ticket_id,
                    "name": row[8],
                    "price": float(row[9]),
                    "remaining": row[10]
                })

        result = list(events_dict.values())
        # Save to cache
        cache["events"] = (result, time.time())
        return jsonify(result)
    finally:
        cursor.close()
        conn.close()

@app.route("/api/activity", methods=["POST"])
def log_activity():
    trace_id = get_trace_id()
    
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    action = data.get("action")
    meta = data.get("meta")

    if not user_id or not action:
        logger.warning(f"[TraceID: {trace_id}] Missing activity fields")
        return jsonify({"error": "user_id and action required"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        # Generate a unique ID for the activity record
        activity_id = str(uuid.uuid4())
        
        # Insert into USER_ACTIVITY table (which you defined in init_db.py)
        cursor.execute("""
            INSERT INTO USER_ACTIVITY (id, user_id, event_id, action, meta)
            VALUES (?, ?, ?, ?, ?)
        """, (activity_id, user_id, event_id, action, str(meta)))

        conn.commit()
        logger.info(f"[TraceID: {trace_id}] Activity Logged: User {user_id} -> {action} on Event {event_id}")
        return jsonify({"status": "success", "activity_id": activity_id}), 201

    except Exception as e:
        logger.error(f"[TraceID: {trace_id}] Failed to log activity: {e}")
        return jsonify({"error": "Internal logging error"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/purchase", methods=["POST"])
def purchase_ticket():
    trace_id = get_trace_id()  

    if not request.is_json:
        logger.warning(f"[TraceID: {trace_id}] Purchase request not JSON")
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    ticket_id = data.get("ticket_id")
    quantity = data.get("quantity")

    logger.info(f"[TraceID: {trace_id}] Purchase request received: user_id={user_id}, ticket_id={ticket_id}, quantity={quantity}")

    if not user_id or not ticket_id or not quantity:
        logger.warning(f"[TraceID: {trace_id}] Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400

    if quantity <= 0:
        logger.warning(f"[TraceID: {trace_id}] Invalid quantity: {quantity}")
        return jsonify({"error": "Invalid quantity"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        logger.info(f"[TraceID: {trace_id}] Attempting to decrease remaining tickets for ticket {ticket_id} by {quantity}")
        cursor.execute(
            "UPDATE TICKET SET remaining = remaining - ? WHERE id = ? AND remaining >= ?",
            (quantity, ticket_id, quantity)
        )
        logger.info(f"[TraceID: {trace_id}] Rows affected: {cursor.rowcount}")

        if cursor.rowcount == 0:
            logger.warning(f"[TraceID: {trace_id}] Tickets unavailable or sold out")
            return jsonify({"error": "Tickets unavailable or sold out"}), 400

        # Insert each order individually and log
        for _ in range(quantity):   
            cursor.execute("""
                INSERT INTO `ORDERS` (user_id, ticket_id, status, created_at)
                VALUES (?, ?, ?, NOW())
            """, (user_id, ticket_id, 'confirmed'))
            new_order_id = cursor.lastrowid
            logger.info(f"[TraceID: {trace_id}] Order inserted: order_id={new_order_id}, user_id={user_id}, ticket_id={ticket_id}")


        conn.commit()
        logger.info(f"[TraceID: {trace_id}] Transaction committed successfully")
        return jsonify({"status": "success"}), 200

    except mariadb.Error as e:
        conn.rollback()
        logger.error(f"[TraceID: {trace_id}] MariaDB error: {e}")
        return jsonify({"error": f"Transaction failed: {e}"}), 500
    except Exception as e:
        conn.rollback()
        logger.error(f"[TraceID: {trace_id}] Unexpected error: {e}")
        return jsonify({"error": f"Transaction failed: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/orders", methods=["GET"])
def get_orders():
    trace_id = get_trace_id()
    user_id = request.args.get("user_id")
    if not user_id:
        logger.warning(f"[TraceID: {trace_id}] user_id required")
        return jsonify({"error": "user_id required"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        logger.info(f"[TraceID: {trace_id}] Fetching orders for user {user_id}")
        cursor.execute("""
            SELECT
                o.id,
                o.status,
                o.created_at,
                t.name,
                t.price,
                e.title,
                e.city,
                e.starts_at
            FROM `ORDERS` o
            JOIN TICKET t ON o.ticket_id = t.id
            JOIN EVENT e ON t.event_id = e.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        orders = [
            {
                "order_id": row[0],
                "status": row[1],
                "created_at": row[2].isoformat(),
                "ticket_name": row[3],
                "price": float(row[4]),
                "event_title": row[5],
                "city": row[6],
                "event_date": row[7].isoformat()
            }
            for row in rows
        ]
        return jsonify(orders)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/register", methods=["POST"])
def register():
    trace_id = get_trace_id()

    if not request.is_json:
        logger.warning(f"[TraceID: {trace_id}] JSON required")
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        logger.warning(f"[TraceID: {trace_id}] Missing registration fields")
        return jsonify({"error": "name, email and password required"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM USERS WHERE email = ?", (email,))
        if cursor.fetchone():
            logger.warning(f"[TraceID: {trace_id}] Email already registered")
            return jsonify({"error": "Email already registered"}), 400

        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO USERS (id, name, email, password_hash, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, email, password_hash, 'active'))

        conn.commit()

        logger.info(f"[TraceID: {trace_id}] User registered: {user_id}")
        return jsonify({"status": "registered", "user_id": user_id}), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"[TraceID: {trace_id}] Registration failed: {e}")
        return jsonify({"error": "Registration failed"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    trace_id = get_trace_id()

    if not request.is_json:
        logger.warning(f"[TraceID: {trace_id}] JSON required")
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        logger.warning(f"[TraceID: {trace_id}] Missing login fields")
        return jsonify({"error": "email and password required"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        cursor.execute("SELECT id, password_hash FROM USERS WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            logger.warning(f"[TraceID: {trace_id}] User not found")
            return jsonify({"error": "User not found"}), 404

        user_id, stored_hash = user

        if not check_password_hash(stored_hash, password):
            logger.warning(f"[TraceID: {trace_id}] Invalid password")
            return jsonify({"error": "Invalid credentials"}), 401

        logger.info(f"[TraceID: {trace_id}] Login successful: {user_id}")
        return jsonify({"status": "login_success", "user_id": user_id}), 200

    except Exception as e:
        logger.error(f"[TraceID: {trace_id}] Login failed: {e}")
        return jsonify({"error": "Login failed"}), 500

    finally:
        cursor.close()
        conn.close()


#  RUN SERVER 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)