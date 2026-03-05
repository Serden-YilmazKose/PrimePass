import uuid
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

app = Flask(__name__)

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')   # for registration if user not found

    conn, cursor = get_db()
    cursor.execute("SELECT id, password_hash FROM USERS WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user:
        if check_password_hash(user[1], password):
            return jsonify({'status': 'login_success', 'user_id': user[0]})
        return jsonify({'error': 'invalid credentials'}), 401

    # auto‑register new user
    if not name:
        return jsonify({'error': 'user not found, name required to register'}), 400
    new_id = str(uuid.uuid4())
    pw_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO USERS (id, name, email, password_hash, status) VALUES (?, ?, ?, ?, 'active')",
        (new_id, name, email, pw_hash)
    )
    conn.commit()
    return jsonify({'status': 'user_created', 'user_id': new_id}), 201

if __name__ == '__main__':
    app.run(port=5001)