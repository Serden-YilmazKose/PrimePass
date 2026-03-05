import uuid, json
from flask import Flask, request, jsonify
from db import get_db

app = Flask(__name__)

@app.route('/api/activity', methods=['POST'])
def log_activity():
    data = request.get_json()
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    action = data.get('action')
    meta = data.get('meta')

    if not user_id or not action:
        return jsonify({'error': 'user_id and action required'}), 400

    conn, cursor = get_db()
    activity_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO USER_ACTIVITY (id, user_id, event_id, action, meta, created_at) VALUES (?, ?, ?, ?, ?, NOW())",
        (activity_id, user_id, event_id, action, json.dumps(meta) if meta else None)
    )
    conn.commit()
    return jsonify({'status': 'ok', 'activity_id': activity_id}), 201

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def recommend(user_id):
    conn, cursor = get_db()
    # simple popularity‑based fallback if no user history
    cursor.execute("""
        SELECT event_id, COUNT(*) as cnt
        FROM USER_ACTIVITY
        WHERE user_id = ? AND event_id IS NOT NULL
        GROUP BY event_id
        ORDER BY cnt DESC
        LIMIT 5
    """, (user_id,))
    user_events = [row[0] for row in cursor.fetchall()]

    if user_events:
        placeholders = ','.join(['?'] * len(user_events))
        cursor.execute(f"""
            SELECT id, title, venue, city, starts_at, ends_at, status
            FROM EVENT
            WHERE id IN ({placeholders})
        """, user_events)
    else:
        # global popular events
        cursor.execute("""
            SELECT e.id, e.title, e.venue, e.city, e.starts_at, e.ends_at, e.status
            FROM EVENT e
            JOIN (
                SELECT event_id, COUNT(*) as cnt
                FROM USER_ACTIVITY
                WHERE event_id IS NOT NULL
                GROUP BY event_id
                ORDER BY cnt DESC
                LIMIT 5
            ) pop ON e.id = pop.event_id
        """)

    events = [{'id': r[0], 'title': r[1], 'venue': r[2], 'city': r[3],
               'starts_at': r[4].isoformat() if r[4] else None,
               'ends_at': r[5].isoformat() if r[5] else None,
               'status': r[6]} for r in cursor.fetchall()]
    return jsonify(events)

if __name__ == '__main__':
    app.run(port=5004)