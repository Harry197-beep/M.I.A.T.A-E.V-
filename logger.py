import sqlite3
from datetime import datetime

def log_interaction(user_message, tool_used=None, tool_result=None, 
                     llm_provider=None, response=None, db_path="miata.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO logs (timestamp, user_message, tool_used, tool_result, llm_provider, response)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), user_message, tool_used, tool_result, llm_provider, response))
    conn.commit()
    conn.close()
