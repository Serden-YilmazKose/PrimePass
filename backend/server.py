"""Flask API to make GET and POST requests to a MariaDB server"""

import json
import sys

import mariadb
from flask import Flask, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)


@app.route("/videos", methods=["GET"])
@cross_origin()
def get_block():
    """Handle GET Requests"""
    if request.method == "GET":
        id_param = request.args["id"]
        return select(id_param)
    return "ERROR"


@app.route("/videos", methods=["POST"])
@cross_origin()
def post_block():
    """Handle POST Requests"""
    if request.method == "POST":
        return insert(request)
    return "ERROR"


# def insert(*, website, video_id, x_cord, y_cord, length, height, x_res, y_res):
def insert(request_data):
    """Insert data using SQL query to MariaDB server"""
    conn, cursor = connect_to_mariadb()
    # --- Example: Select Data ---
    print("\nInserting data...")

    id_param = request_data.json["id"]
    insert_query = """INSERT INTO MYTABLE (id) VALUE {id_param};"""

    # Note the comma for single parameter tuple
    cursor.execute(insert_query)
    conn.commit()

    cursor.connection.close()
    return "DONE"


def select(id_param):
    """Make SQL query to get needed data based video_id"""
    _, cursor = connect_to_mariadb()

    # --- Example: Select Data ---
    print("\nSelecting data...")
    select_query = f"""SELECT id FROM VIDEOS WHERE id='{id_param}'"""

    # Note the comma for single parameter tuple
    cursor.execute(select_query)

    # Jsonify the results somehow
    # Source: https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
    r = [
        dict((cursor.description[i][0], value) for i, value in enumerate(row))
        for row in cursor.fetchall()
    ]
    if r == []:
        return 400
    cursor.connection.close()
    return json.dumps(r[0] if r else None)


def connect_to_mariadb():
    """Make connection to MariaDB server, return connection and cursor"""
    # Connect to Mariadb
    # Source:https://mariadb.com/docs/connectors/connectors-quickstart-guides/connector-python-guide
    try:
        conn = mariadb.connect(
            user="root",
            password="pass",
            host="127.0.0.1",
            port=3306,
            database="caption_capper",
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cursor = conn.cursor()
    return conn, cursor


if __name__ == "__main__":
    app.run(debug=True)
