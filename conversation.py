import sqlite3
from datetime import datetime

MAX_HISTORY_MESSAGES = 10  # last 10 turns kept as context, keeps token usage sane


def save_message(chat_id, role, content, db_path="miata.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversation_history (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (str(chat_id), role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_history(chat_id, db_path="miata.db", limit=MAX_HISTORY_MESSAGES):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM conversation_history WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (str(chat_id), limit)
    )
    rows = cur.fetchall()
    conn.close()
    rows.reverse()  # put back in chronological order
    return [{"role": role, "content": content} for role, content in rows]
