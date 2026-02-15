import os
import json
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

redis_client = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, decode_responses=True)

POPULAR_KEY = "popular_events"

@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    # Try personalized recommendations
    rec_key = f"rec:{user_id}"
    rec_data = redis_client.get(rec_key)
    if rec_data:
        event_ids = json.loads(rec_data)
    else:
        # Fallback to popular events
        popular = redis_client.get(POPULAR_KEY)
        event_ids = json.loads(popular) if popular else []

    # For simplicity, return only IDs. The frontend can fetch details via /api/events.
    return jsonify(event_ids)

@app.route("/api/recommendations/popular", methods=["GET"])
def get_popular():
    popular = redis_client.get(POPULAR_KEY)
    if popular:
        return jsonify(json.loads(popular))
    return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)