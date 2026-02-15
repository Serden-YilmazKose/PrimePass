"""Flask API for ticket sales using MariaDB"""

from flask import Flask, request, jsonify
from init_db import connect_to_mariadb, create_tables

app = Flask(__name__)

create_tables()

@app.route("/api/events", methods=["GET"])
def get_events():
    conn, cursor = connect_to_mariadb()
    cursor.execute("SELECT id, name, date, available FROM EVENTS")
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

    return jsonify(events)


@app.route("/api/purchase", methods=["POST"])
def purchase_ticket():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    event_id = data.get("event_id")
    quantity = data.get("quantity")

    if not event_id or not quantity:
        return jsonify({"error": "Missing fields"}), 400

    conn, cursor = connect_to_mariadb()

    cursor.execute(
        "SELECT available FROM EVENTS WHERE id = ?",
        (event_id,),
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Event not found"}), 404

    if row[0] < quantity:
        cursor.close()
        conn.close()
        return jsonify({"error": "Not enough tickets"}), 400

    cursor.execute(
        "UPDATE EVENTS SET available = available - ? WHERE id = ?",
        (quantity, event_id),
    )
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
