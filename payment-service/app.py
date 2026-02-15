from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory store for simplicity (in production, use a database)
payments = {}

@app.route("/api/payments/charge", methods=["POST"])
def charge():
    data = request.get_json()
    user_id = data.get("user_id")
    amount = data.get("amount")
    reservation_id = data.get("reservation_id")  # optional

    if not user_id or not amount:
        return jsonify({"error": "Missing user_id or amount"}), 400

    # Mock payment processing: always successful
    payment_id = str(uuid.uuid4())
    payments[payment_id] = {
        "payment_id": payment_id,
        "user_id": user_id,
        "amount": amount,
        "reservation_id": reservation_id,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }

    return jsonify({"payment_id": payment_id, "status": "success"}), 200

@app.route("/api/payments/<payment_id>", methods=["GET"])
def get_payment(payment_id):
    payment = payments.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    return jsonify(payment)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)