import uuid
import psycopg
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from init_db import connect_to_postgres

app = Flask(__name__)

def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
    
def log_activity(cursor, user_id: str, event_id, action: str, meta: dict | None = None):
    """
    Insert into USER_ACTIVITY.
    Table columns assumed:
      (id VARCHAR(36), user_id VARCHAR(36), event_id INT NULL, action VARCHAR(50), meta JSON NULL, created_at ...)
    """
    activity_id = str(uuid.uuid4())
    meta_json = json.dumps(meta) if meta is not None else None

    cursor.execute(
        """
        INSERT INTO USER_ACTIVITY (id, user_id, event_id, action, meta)
        VALUES (?, ?, ?, ?, ?)
        """,
        (activity_id, user_id, event_id, action, meta_json),
    )
    return activity_id


@app.route("/api/events", methods=["GET"])
def get_events():
    conn, cursor = connect_to_postgres()
    try:
        cursor.execute("""
            SELECT e.id, e.title, e.venue, e.city, e.starts_at, e.ends_at, e.status,
                   t.id, t.name, t.price, t.remaining
            FROM event e
            LEFT JOIN ticket t ON e.id = t.event_id
            ORDER BY e.id, t.id
        """)
        rows = cursor.fetchall()
        events_dict = {}
        for row in rows:
            event_id = row[0]
            if event_id not in events_dict:
                events_dict[event_id] = {
                    "id": event_id, "title": row[1], "venue": row[2], "city": row[3],
                    "starts_at": row[4].isoformat() if row[4] else None,
                    "ends_at": row[5].isoformat() if row[5] else None,
                    "status": row[6], "tickets": []
                }
            ticket_id = row[7]
            if ticket_id:
                events_dict[event_id]["tickets"].append({
                    "id": ticket_id, "name": row[8],
                    "price": float(row[9]), "remaining": row[10]
                })
        return jsonify(list(events_dict.values()))
    finally:
        cursor.close()
        conn.close()

@app.route("/api/activity", methods=["POST"])
def track_activity():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")  
    action = data.get("action") or "view"
    meta = data.get("meta")  

    # Basic validation
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    # If event_id is provided, ensure it's an integer or can be converted to one
    if event_id is not None:
        event_id_int = _safe_int(event_id)
        if event_id_int is None:
            return jsonify({"error": "event_id must be an integer"}), 400
        event_id = event_id_int

    if not isinstance(action, str) or not action.strip():
        return jsonify({"error": "action must be a non-empty string"}), 400

    if meta is not None and not isinstance(meta, dict):
        return jsonify({"error": "meta must be an object/dict"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        activity_id = log_activity(cursor, user_id=user_id, event_id=event_id, action=action, meta=meta)
        conn.commit()
        return jsonify({"status": "ok", "activity_id": activity_id}), 201
    except mariadb.Error as e:
        conn.rollback()
        return jsonify({"error": f"Activity logging failed: {e}"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/purchase", methods=["POST"])
def purchase_ticket():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400
    data = request.get_json()
    user_id, ticket_id, quantity = data.get("user_id"), data.get("ticket_id"), data.get("quantity")
    if not user_id or not ticket_id or not quantity or quantity <= 0:
        return jsonify({"error": "Missing or invalid fields"}), 400

    conn, cursor = connect_to_postgres()
    try:
        cursor.execute(
            "UPDATE ticket SET remaining = remaining - %s WHERE id = %s AND remaining >= %s",
            (quantity, ticket_id, quantity)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Tickets unavailable or sold out"}), 400

        cursor.executemany(
            "INSERT INTO orders (user_id, ticket_id, status, created_at) VALUES (%s, %s, %s, NOW())",
            [(user_id, ticket_id, 'confirmed') for _ in range(quantity)]
        )
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Transaction failed: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    conn, cursor = connect_to_postgres()
    try:
        cursor.execute("""
            SELECT o.id, o.status, o.created_at, t.name, t.price, e.title, e.city, e.starts_at
            FROM orders o
            JOIN ticket t ON o.ticket_id = t.id
            JOIN event e ON t.event_id = e.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        orders = [{
            "order_id": row[0], "status": row[1], "created_at": row[2].isoformat(),
            "ticket_name": row[3], "price": float(row[4]), "event_title": row[5],
            "city": row[6], "event_date": row[7].isoformat()
        } for row in rows]
        return jsonify(orders)
    finally:
        cursor.close()
        conn.close()

@app.route("/api/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    conn, cursor = connect_to_postgres()
    try:
        cursor.execute("SELECT id, password_hash FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            user_id, stored_hash = user
            if check_password_hash(stored_hash, password):
                return jsonify({"status": "login_success", "user_id": user_id})
            return jsonify({"error": "invalid credentials"}), 401

        if not name:
            return jsonify({"error": "user not found. name required to register"}), 400

        secure_hash = generate_password_hash(password)
        new_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash, status) VALUES (%s, %s, %s, %s, %s)",
            (new_id, name, email, secure_hash, 'active')
        )
        conn.commit()
        return jsonify({"status": "user_created", "user_id": new_id}), 201
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)