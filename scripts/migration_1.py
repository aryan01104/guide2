import sqlite3
import pathlib

db_path = pathlib.Path(__file__).parent.parent / "data" / "activity.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("PRAGMA table_info(activity_sessions);")
for row in cur.fetchall():
    print(row)
conn.close()
