import os
import sqlite3

from flask import Flask, jsonify, render_template

app = Flask(__name__)


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "activity.db")
print("DB_PATH:", DB_PATH)


def get_sessions_with_activities():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Get all sessions
    sessions = cur.execute("SELECT * FROM activity_sessions").fetchall()
    session_list = []
    for s in sessions:
        session_id = s["id"]
        # Fetch activities ONLY by session_id FK!
        activities = cur.execute(
            "SELECT * FROM activity_logs WHERE session_id = ? ORDER BY timestamp_start",
            (session_id,),
        ).fetchall()
        activity_list = []
        for a in activities:
            activity_list.append(
                {
                    "id": a["id"],
                    "details": a["details"],
                    "duration_sec": a["duration_sec"],
                    "productivity_score": a["productivity_score"],
                    "classification_text": a["classification_text"],
                }
            )
        session_list.append(
            {
                "id": s["id"],
                "title": s["session_name"] or f"Session {s['id']}",
                "start": s["start_time"],
                "end": s["end_time"],
                "extendedProps": {"activities": activity_list},
            }
        )
    conn.close()
    return session_list


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calendar")
def calendar():
    return render_template("calendar.html")


@app.route("/api/sessions")
def api_sessions():
    events = get_sessions_with_activities()
    return jsonify(events)


if __name__ == "__main__":
    app.run(debug=True)
