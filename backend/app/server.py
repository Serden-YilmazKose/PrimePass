"""Flask API for ticket sales using MariaDB"""
import uuid

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from init_db import connect_to_mariadb, create_tables

app = Flask(__name__)

create_tables()


@app.route("/api/events", methods=["GET"])
def get_events():
    conn, cursor = connect_to_mariadb()
    try:
        cursor.execute("""
            SELECT
                e.id,
                e.title,
                e.venue,
                e.city,
                e.starts_at,
                e.ends_at,
                e.status,
                COALESCE(SUM(t.remaining), 0) as total_remaining
            FROM EVENT e
            LEFT JOIN TICKET t ON e.id = t.event_id
            GROUP BY e.id
        """)

        rows = cursor.fetchall()
        # cursor.close()
        # conn.close()

        events = [
            {
                "id": row[0],
                "title": row[1],
                "venue": row[2],
                "city": row[3],
                # Ignore of NULL
                "starts_at": row[4].isoformat() if row[4] else None,
                "ends_at": row[5].isoformat() if row[5] else None,
                "status": row[6],
                "remaining_tickets": row[7]
            }
            for row in rows
        ]
        return jsonify(events)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/purchase", methods=["POST"])
def purchase_ticket():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    ticket_id = data.get("ticket_id")
    quantity = data.get("quantity")

    if not user_id or not ticket_id or not quantity:
        return jsonify({"error": "Missing required fields"}), 400

    if quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400
    conn, cursor = connect_to_mariadb()
    try:
        # Atomic update: only updates if there is enough stock
        cursor.execute(
            "UPDATE TICKET SET remaining = remaining - ? WHERE id = ? AND remaining >= ?",
            (quantity, ticket_id, quantity)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Tickets unavailable or sold out"}), 400

        # Bulk insert orders instead of a loop
        order_data = [(str(uuid.uuid4()), user_id, ticket_id, 'confirmed')
                      for _ in range(quantity)]
        cursor.executemany("""
            INSERT INTO `ORDER` (id, user_id, ticket_id, status, created_at)
            VALUES (?, ?, ?, ?, NOW())
        """, order_data)

        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception:
        conn.rollback()
        return jsonify({"error": "Transaction failed"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    conn, cursor = connect_to_mariadb()
    try:
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
            FROM `ORDER` o
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


@app.route("/api/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "json required"}), 400

    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "name, email, and password required"}), 400

    conn, cursor = connect_to_mariadb()

    # 1. look for the user
    cursor.execute(
        "select id, password_hash from user where email = ?", (email,))
    user = cursor.fetchone()

    if user:
        user_id, stored_hash = user
        # 2. verify the password
        if check_password_hash(stored_hash, password):
            cursor.close()
            conn.close()
            return jsonify({"status": "login_success", "user_id": user_id})
        cursor.close()
        conn.close()
        return jsonify({"error": "invalid credentials"}), 401

    # 3. if user doesn't exist, register them
    if not name:
        cursor.close()
        conn.close()
        return jsonify({"error": "user not found. name required to register"}), 400

    # hash the password before saving
    secure_hash = generate_password_hash(password)
    # create uuid
    new_id = str(uuid.uuid4())

    try:
        cursor.execute("""
            insert into user (id, name, email, password_hash, status)
            values (?, ?, ?, ?, ?)
        """, (new_id, name, email, secure_hash, 'active'))
        conn.commit()
        return jsonify({"status": "user_created", "user_id": new_id}), 201

    except exception:
        return jsonify({"error": "registration failed"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"error": "idk, something happened"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
