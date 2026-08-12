from flask import Flask, request, jsonify
import sys
sys.path.insert(0, '.')

from bot import run_agent

app = Flask(__name__)

TASKER_CHAT_ID = "tasker_wake_word"  # separate conversation thread from Telegram


@app.route("/miata", methods=["POST"])
def miata_webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "missing 'message' field"}), 400

    user_message = data["message"]
    response, tool_used, tool_result = run_agent(user_message, TASKER_CHAT_ID)

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
