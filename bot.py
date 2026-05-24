from flask import Flask, request
import requests
from time import time
from datetime import datetime
import os

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------
BOT_ID = os.environ.get("BOT_ID")

SPAM_LIMIT = 5
SPAM_WINDOW = 5

user_activity = {}
warnings = {}

BANNED_WORDS = [
    "fuck",
    "bitch",
    "slur1",
    "slur2"
]

RULES = """
GROUPCHAT RULES

1. Use your real name/nickname.
2. No swearing or inappropriate content.
3. No NSFW content.
4. Respect everyone.
5. No spam.
6. Avoid messaging too early or too late.
7. No impersonation.
8. Stop means stop.

Failure to follow rules may result in warnings or removal.
"""

# -----------------------------
# SEND MESSAGE
# -----------------------------
def send_message(text):
    if not BOT_ID:
        print("ERROR: BOT_ID not set")
        return

    requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={
            "bot_id": BOT_ID,
            "text": text
        }
    )

# -----------------------------
# WARNINGS
# -----------------------------
def add_warning(name):
    warnings[name] = warnings.get(name, 0) + 1

    if warnings[name] == 2:
        send_message(f"{name}, this is your second warning.")

    elif warnings[name] >= 3:
        send_message(f"{name} has 3 warnings. Leadership should review this.")

# -----------------------------
# WEBHOOK
# -----------------------------
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if not data:
        return "ok", 200

    if data.get("sender_type") == "bot":
        return "ok", 200

    message = data.get("text", "").lower().strip()
    name = data.get("name", "Unknown")
    user_id = data.get("user_id")
    now = time()

    # -------------------------
    # COMMANDS
    # -------------------------
    if message == "/rules":
        send_message(RULES)

    elif message == "hello":
        send_message(f"Hi {name}!")

    elif message == "/warnings":
        send_message(f"{name}, you have {warnings.get(name, 0)} warnings.")

    # -------------------------
    # PROFANITY CHECK
    # -------------------------
    for word in BANNED_WORDS:
        if word in message:
            send_message(f"{name}, please watch your language and follow the rules.")
            add_warning(name)
            break

    # -------------------------
    # SPAM DETECTION
    # -------------------------
    if user_id:
        if user_id not in user_activity:
            user_activity[user_id] = []

        user_activity[user_id] = [
            t for t in user_activity[user_id]
            if now - t < SPAM_WINDOW
        ]

        user_activity[user_id].append(now)

        if len(user_activity[user_id]) > SPAM_LIMIT:
            send_message(f"{name}, stop spamming the chat.")
            add_warning(name)

    # -------------------------
    # QUIET HOURS WARNING
    # -------------------------
    hour = datetime.now().hour

    if hour >= 22 or hour < 5:
        send_message("Reminder: Please avoid messaging between 10 PM and 5 AM.")

    return "ok", 200

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
