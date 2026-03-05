import uuid
from flask import Flask, request, jsonify
from db import get_db

app = Flask(__name__)
RECOMMEND_SERVICE_URL = 'http://recommendation-service:5004'

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    event_id = request.args.get('event_id')
    if not event_id:
        return jsonify({'error': 'event_id required'}), 400
    conn, cursor = get_db()
    cursor.execute("SELECT id, name, price, remaining FROM TICKET WHERE event_id = ?", (event_id,))
    tickets = [{'id': r[0], 'name': r[1], 'price': float(r[2]), 'remaining': r[3]} for r in cursor.fetchall()]
    return jsonify(tickets)

@app.route('/api/purchase', methods=['POST'])
def purchase():
    data = request.get_json()
    user_id = data.get('user_id')
    ticket_id = data.get('ticket_id')
    quantity = data.get('quantity', 1)

    conn, cursor = get_db()
    try:
        cursor.execute("UPDATE TICKET SET remaining = remaining - ? WHERE id = ? AND remaining >= ?",
                       (quantity, ticket_id, quantity))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tickets unavailable'}), 400

        # create orders
        for _ in range(quantity):
            order_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO ORDERS (id, user_id, ticket_id, status, created_at) VALUES (?, ?, ?, 'confirmed', NOW())",
                           (order_id, user_id, ticket_id))

        # get event_id for activity logging
        cursor.execute("SELECT event_id FROM TICKET WHERE id = ?", (ticket_id,))
        event_id = cursor.fetchone()[0]

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    # asynchronously log activity (fire and forget)
    try:
        requests.post(f"{RECOMMEND_SERVICE_URL}/api/activity", json={
            'user_id': user_id,
            'event_id': event_id,
            'action': 'purchase',
            'meta': {'ticket_id': ticket_id, 'quantity': quantity}
        })
    except:
        pass   # non‑critical

    return jsonify({'status': 'success'})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    conn, cursor = get_db()
    cursor.execute("""
        SELECT o.id, o.status, o.created_at, t.name, t.price, e.title, e.city, e.starts_at
        FROM ORDERS o
        JOIN TICKET t ON o.ticket_id = t.id
        JOIN EVENT e ON t.event_id = e.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    """, (user_id,))
    orders = [{'order_id': r[0], 'status': r[1], 'created_at': r[2].isoformat(),
               'ticket_name': r[3], 'price': float(r[4]), 'event_title': r[5],
               'city': r[6], 'event_date': r[7].isoformat()} for r in cursor.fetchall()]
    return jsonify(orders)

if __name__ == '__main__':
    app.run(port=5003)
