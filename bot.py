import os
import json
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from logger import log_interaction
from db_setup import init_db
from gmail_tool import search_emails
from calendar_tool import get_upcoming_events, create_event
from search_tool import web_search
from voice_tool import transcribe_audio, synthesize_speech
from conversation import save_message, get_recent_history

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are Miata, a personal AI assistant. You are direct, 
helpful, and a little witty. Keep replies concise unless asked for detail.
Use search_gmail for questions about emails or inbox.
Use get_calendar_events for questions about upcoming events, schedule, or meetings.
Use create_calendar_event when the user wants to add/create/schedule a new event or reminder.
Use web_search for current events, news, or anything requiring up-to-date info from the internet.
You have memory of the recent conversation - use it for context, don't ask the user to repeat themselves.
When creating calendar events, assume Asia/Jakarta timezone (WIB) unless told otherwise."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_gmail",
            "description": "Search the user's Gmail inbox using Gmail search syntax (e.g. 'from:stockbit newer_than:1d', 'subject:invoice')",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get the user's upcoming calendar events",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {"type": "integer", "description": "How many days ahead to look, default 7"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create a new calendar event. Ask the user for clarification if date/time is ambiguous.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_datetime": {"type": "string", "description": "ISO format start datetime, e.g. 2026-08-13T10:00:00"},
                    "end_datetime": {"type": "string", "description": "ISO format end datetime, optional, defaults to 1 hour after start"}
                },
                "required": ["summary", "start_datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or anything not in the user's personal data",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]


def call_tool(tool_name, args):
    if tool_name == "search_gmail":
        return search_emails(args.get("query", ""))
    elif tool_name == "get_calendar_events":
        return get_upcoming_events(days_ahead=args.get("days_ahead", 7))
    elif tool_name == "create_calendar_event":
        return create_event(
            summary=args.get("summary"),
            start_datetime=args.get("start_datetime"),
            end_datetime=args.get("end_datetime")
        )
    elif tool_name == "web_search":
        return web_search(args.get("query", ""))
    return "Unknown tool."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Miata online. What do you need?")


def run_agent(user_message: str, chat_id):
    """Shared pipeline: takes text in + chat_id for history, returns (response, tool_used, tool_result)."""
    history = get_recent_history(chat_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": user_message}
    ]

    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
        )
    except Exception as e:
        return f"Sorry, I hit an error trying to process that: {e}", None, None

    reply = completion.choices[0].message
    tool_used = None
    tool_result = None

    if reply.tool_calls:
        tool_call = reply.tool_calls[0]
        tool_used = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        tool_result = call_tool(tool_used, args)

        followup_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{user_message}\n\n[Tool result from {tool_used}]:\n{tool_result}\n\nAnswer the user's question using this information, in plain conversational text."}
        ]

        try:
            followup = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=followup_messages,
            )
            response = followup.choices[0].message.content
        except Exception as e:
            response = f"Found the data but hit an error summarizing it: {e}" 
       
    else:
        response = reply.content

    save_message(chat_id, "user", user_message)
    save_message(chat_id, "assistant", response)

    return response, tool_used, tool_result


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    response, tool_used, tool_result = run_agent(user_message, chat_id)

    log_interaction(
        user_message=user_message,
        tool_used=tool_used,
        tool_result=tool_result,
        llm_provider="groq",
        response=response,
    )

    await update.message.reply_text(response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_file = await update.message.voice.get_file()
    ogg_path = "temp_voice.ogg"
    await voice_file.download_to_drive(ogg_path)

    user_message = transcribe_audio(ogg_path)
    os.remove(ogg_path)

    chat_id = update.effective_chat.id
    response, tool_used, tool_result = run_agent(user_message, chat_id)

    log_interaction(
        user_message=user_message,
        tool_used=tool_used,
        tool_result=tool_result,
        llm_provider="groq",
        response=response,
    )

    wav_path = "temp_reply.wav"
    try:
        synthesize_speech(response, wav_path)
        with open(wav_path, "rb") as f:
            await update.message.reply_voice(voice=f)
        os.remove(wav_path)
    except Exception as e:
        await update.message.reply_text(f"{response}\n\n(Voice reply unavailable right now: {e})")

def main():
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Miata is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
