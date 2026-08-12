import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CATEGORIES = {
    "search_gmail": "asking to search, check, or look through their Gmail inbox for something",
    "get_calendar_events": "asking what's on their calendar, their schedule, or upcoming events",
    "create_calendar_event": "asking to create, add, or schedule a new calendar event or reminder",
    "web_search": "asking to search the web for current info, news, or facts",
    "none": "just chatting, greeting, or asking something that needs no tool at all",
}

EXAMPLES_PER_CATEGORY = 15


def generate_examples(category, description):
    prompt = f"""Generate {EXAMPLES_PER_CATEGORY} different, natural, realistic ways a person 
might phrase a message to a personal AI assistant when {description}.
Vary the phrasing, tone, and length a lot - some casual, some formal, some short, some longer.
Return ONLY a JSON array of strings, nothing else."""

    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )

    text = completion.choices[0].message.content.strip()
    text = text.strip("```json").strip("```").strip()
    return json.loads(text)


def save_synthetic(messages, label, db_path="miata.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for msg in messages:
        cur.execute(
            """INSERT INTO logs (timestamp, user_message, tool_used, tool_result, llm_provider, response)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), msg, label if label != "none" else None, None, "synthetic", None)
        )
    conn.commit()
    conn.close()


def main():
    for category, description in CATEGORIES.items():
        print(f"Generating examples for: {category}")
        try:
            examples = generate_examples(category, description)
            save_synthetic(examples, category)
            print(f"  Added {len(examples)} synthetic examples")
        except Exception as e:
            print(f"  Failed: {e}")


if __name__ == "__main__":
    main()
