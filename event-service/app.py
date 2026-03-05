from flask import Flask, jsonify
import requests
from db import get_db

app = Flask(__name__)
TICKET_SERVICE_URL = 'http://ticket-service:5003'

@app.route('/api/events', methods=['GET'])
def get_events():
    conn, cursor = get_db()
    cursor.execute("SELECT id, title, venue, city, starts_at, ends_at, status FROM EVENT")
    rows = cursor.fetchall()
    events = []
    for row in rows:
        event = {
            'id': row[0],
            'title': row[1],
            'venue': row[2],
            'city': row[3],
            'starts_at': row[4].isoformat() if row[4] else None,
            'ends_at': row[5].isoformat() if row[5] else None,
            'status': row[6],
            'tickets': []
        }
        # fetch tickets from ticket service
        try:
            resp = requests.get(f"{TICKET_SERVICE_URL}/api/tickets?event_id={row[0]}")
            if resp.ok:
                event['tickets'] = resp.json()
        except requests.exceptions.RequestException:
            pass   # fallback to empty tickets
        events.append(event)
    return jsonify(events)

if __name__ == '__main__':
    app.run(port=5002)
