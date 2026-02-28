"""Flask API for ticket sales using MariaDB"""
import uuid
import mariadb

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from init_db import connect_to_mariadb

app = Flask(__name__)

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

        return jsonify(list(events_dict.values()))

    finally:
        cursor.close()
        conn.close()

@app.route("/api/purchase", methods=["POST"])
def purchase_ticket():
    if not request.is_json:
        print("Request not JSON")
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    ticket_id = data.get("ticket_id")
    quantity = data.get("quantity")

    print(f"Purchase request received: user_id={user_id}, ticket_id={ticket_id}, quantity={quantity}")

    if not user_id or not ticket_id or not quantity:
        print("Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400

    if quantity <= 0:
        print("Invalid quantity")
        return jsonify({"error": "Invalid quantity"}), 400

    conn, cursor = connect_to_mariadb()
    try:
        # Log before running the update
        print(f"Attempting to decrease remaining tickets for ticket {ticket_id} by {quantity}")
        cursor.execute(
            "UPDATE TICKET SET remaining = remaining - ? WHERE id = ? AND remaining >= ?",
            (quantity, ticket_id, quantity)
        )
        print(f"Rows affected: {cursor.rowcount}")

        if cursor.rowcount == 0:
            print("No tickets available or insufficient remaining")
            return jsonify({"error": "Tickets unavailable or sold out"}), 400

        order_data = [(str(uuid.uuid4()), user_id, ticket_id, 'confirmed') for _ in range(quantity)]
        print(f"Inserting orders: {order_data}")

        cursor.executemany("""
            INSERT INTO `ORDERS` (user_id, ticket_id, status, created_at)
            VALUES (?, ?, ?, NOW())
        """, [(user_id, ticket_id, 'confirmed') for _ in range(quantity)])

        conn.commit()
        print("Transaction committed successfully")
        return jsonify({"status": "success"}), 200

    except mariadb.Error as e:
        conn.rollback()
        print(f"MariaDB error: {e}")
        return jsonify({"error": f"Transaction failed: {e}"}), 500
    except Exception as e:
        conn.rollback()
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Transaction failed: {e}"}), 500
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
        "select id, password_hash from USERS where email = ?", (email,))
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
            insert into USERS (id, name, email, password_hash, status)
            values (?, ?, ?, ?, ?)
        """, (new_id, name, email, secure_hash, 'active'))
        conn.commit()
        return jsonify({"status": "user_created", "user_id": new_id}), 201

    except Exception:
        return jsonify({"error": "registration failed"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"error": "idk, something happened"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
