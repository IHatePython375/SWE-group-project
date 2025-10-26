import os
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.get("/api/leaderboard")
def leaderboard():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT player, final_money, rounds_completed, profit, created_at
            FROM scores
            ORDER BY final_money DESC, created_at ASC
            LIMIT 10
        """)
        items = cur.fetchall()
    return jsonify({"items": items})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
