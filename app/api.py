from flask import Flask, request, jsonify
from flask_cors import CORS

from database import DatabaseHelper
from auth import AuthManager

app = Flask(__name__)
CORS(app)

db = DatabaseHelper(
    host="localhost",
    port=5432,
    database="blackjack_db",
    user="postgres",
    password="1234"  # Replace with your own local DB password
)

auth = AuthManager(db)


@app.route("/api/leaderboard", methods=["GET"])
def api_get_leaderboard():
    """Return leaderboard entries."""
    limit = request.args.get("limit", default=10, type=int)
    rows = db.get_leaderboard(limit)

    result = []
    for row in rows:
        result.append({
            "leaderboard_id": row.get("leaderboard_id"),
            "username": row.get("username"),
            "final_money": float(row.get("final_money")),
            "profit": float(row.get("profit")),
            "rounds_completed": int(row.get("rounds_completed")),
            "recorded_at": row.get("recorded_at").isoformat() if row.get("recorded_at") else None,
            "rank": row.get("rank"),
        })

    return jsonify(result), 200


@app.route("/api/score", methods=["POST"])
def api_post_score():
    """
    Save a finished game result to the leaderboard.

    Body JSON:
    {
        "session_token": "...",
        "final_money": 1234.5,
        "rounds_completed": 10
    }
    """
    data = request.get_json(force=True) or {}

    session_token = data.get("session_token")
    final_money = data.get("final_money")
    rounds_completed = data.get("rounds_completed")

    if session_token is None or final_money is None or rounds_completed is None:
        return jsonify({
            "error": "session_token, final_money, and rounds_completed are required"
        }), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]

    starting_money_setting = db.get_game_setting("starting_money")

    try:
        starting_money = float(starting_money_setting) if starting_money_setting is not None else 1000.0
        final_money = float(final_money)
        rounds_completed = int(rounds_completed)
    except (TypeError, ValueError):
        return jsonify({"error": "final_money must be numeric and rounds_completed must be an integer"}), 400

    with db.get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO game_sessions
                (user_id, game_mode, starting_money, current_money, rounds_completed, status)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            RETURNING session_id
            """,
            (user_id, "web", starting_money, final_money, rounds_completed, "completed")
        )
        session_row = cursor.fetchone()
        session_id = session_row["session_id"]

    profit = final_money - starting_money
    leaderboard_id = db.add_to_leaderboard(
        user_id=user_id,
        session_id=session_id,
        final_money=final_money,
        rounds_completed=rounds_completed,
        profit=profit
    )

    db.update_user_statistics(user_id)

    return jsonify({
        "leaderboard_id": leaderboard_id,
        "session_id": session_id,
        "final_money": final_money,
        "rounds_completed": rounds_completed,
        "profit": profit
    }), 201


@app.route("/api/friends", methods=["GET"])
def api_get_friends():
    """Return the current user's friends."""
    session_token = request.args.get("session_token")

    if not session_token:
        return jsonify({"error": "session_token is required"}), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]
    rows = db.get_friends(user_id)

    friends = []
    for row in rows:
        if row["user_id"] == user_id:
            friend_id = row["friend_id"]
            friend_name = row["friend_name"]
        else:
            friend_id = row["user_id"]
            friend_name = row["user_name"]

        friends.append({
            "friendship_id": row["friendship_id"],
            "friend_id": friend_id,
            "friend_name": friend_name,
            "since": row["created_at"].isoformat() if row.get("created_at") else None,
        })

    return jsonify(friends), 200


@app.route("/api/friends/request", methods=["POST"])
def api_send_friend_request():
    """Send a friend request to another user by username."""
    data = request.get_json(force=True) or {}

    session_token = data.get("session_token")
    target_username = data.get("friend_username")

    if not session_token or not target_username:
        return jsonify({"error": "session_token and friend_username are required"}), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]

    target_user = db.get_user_by_username(target_username)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if target_user["user_id"] == user_id:
        return jsonify({"error": "You cannot add yourself as a friend"}), 400

    try:
        friendship_id = db.send_friend_request(user_id, target_user["user_id"])
    except Exception:
        return jsonify({"error": "Friend request already exists or users are already friends"}), 400

    return jsonify({
        "friendship_id": friendship_id,
        "to_user": target_user["username"]
    }), 201


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True) or {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"success": False, "message": "username, email, and password are required"}), 400

    result = auth.register_user(username, email, password)

    if not result["success"]:
        return jsonify({"success": False, "message": result["message"]}), 400

    login_result = auth.login(username, password)
    if not login_result["success"]:
        return jsonify({
            "success": True,
            "message": "Registered. Please log in separately."
        }), 201

    user = login_result["user"]

    return jsonify({
        "success": True,
        "message": "Registered and logged in",
        "session_token": login_result["session_token"],
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
    }), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"success": False, "message": "username and password are required"}), 400

    login_result = auth.login(username, password)

    if not login_result["success"]:
        return jsonify({"success": False, "message": login_result["message"]}), 401

    user = login_result["user"]

    return jsonify({
        "success": True,
        "message": login_result["message"],
        "session_token": login_result["session_token"],
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
    }), 200


@app.route("/api/friends/pending", methods=["GET"])
def api_get_pending_friend_requests():
    """Return pending friend requests for the current user."""
    session_token = request.args.get("session_token")

    if not session_token:
        return jsonify({"error": "session_token is required"}), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]
    rows = db.get_pending_friend_requests(user_id)

    pending = []
    for row in rows:
        pending.append({
            "friendship_id": row["friendship_id"],
            "from_user_id": row["user_id"],
            "from_username": row["requester_name"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        })

    return jsonify(pending), 200


@app.route("/api/friends/respond", methods=["POST"])
def api_respond_friend_request():
    """Accept or reject a pending friend request."""
    data = request.get_json(force=True) or {}

    session_token = data.get("session_token")
    friendship_id = data.get("friendship_id")
    action = data.get("action")

    if not session_token or friendship_id is None or not action:
        return jsonify({"error": "session_token, friendship_id, and action are required"}), 400

    action = action.lower()
    if action not in ["accept", "reject"]:
        return jsonify({"error": "action must be 'accept' or 'reject'"}), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]

    with db.get_cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM friendships
            WHERE friendship_id = %s
            """,
            (friendship_id,)
        )
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Friend request not found"}), 404

        if row["friend_id"] != user_id:
            return jsonify({"error": "You are not allowed to respond to this request"}), 403

        if row["status"] != "pending":
            return jsonify({"error": "Request is not pending"}), 400

        if action == "accept":
            db.accept_friend_request(friendship_id)
            new_status = "accepted"
        else:
            cursor.execute(
                """
                UPDATE friendships
                SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                WHERE friendship_id = %s
                """,
                (friendship_id,)
            )
            new_status = "rejected"

    return jsonify({
        "friendship_id": friendship_id,
        "new_status": new_status
    }), 200


@app.route("/api/friends/accept", methods=["POST"])
def api_accept_friend_request():
    data = request.get_json(force=True) or {}

    session_token = data.get("session_token")
    friendship_id = data.get("friendship_id")

    if not session_token or friendship_id is None:
        return jsonify({"error": "session_token and friendship_id are required"}), 400

    session_info = auth.validate_session(session_token)
    if not session_info["valid"]:
        return jsonify({"error": "Invalid or expired session"}), 401

    user_id = session_info["user_id"]

    pending = db.get_pending_friend_requests(user_id)
    matching = [f for f in pending if f["friendship_id"] == friendship_id]

    if not matching:
        return jsonify({"error": "No such pending friend request for this user"}), 404

    db.accept_friend_request(friendship_id)

    return jsonify({"success": True}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
