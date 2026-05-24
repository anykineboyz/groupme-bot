from flask import Flask, request
import requests
from time import time
from datetime import datetime
import os

app = Flask(__name__)

BOT_ID = os.environ.get("2485a350b0d7b988306a01de92")

# -----------------------------
# Tracking Data
# -----------------------------
user_activity = {}
warnings = {}

TARGET_NAME = "lone wolf niko"

# -----------------------------
# Config
# -----------------------------
SPAM_LIMIT = 5
SPAM_WINDOW = 5

BANNED_WORDS = [
    "fuck",
    "bitch",
    "dad",
    "mom",
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
# Send Message
# -----------------------------
def send_message(text):
    requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={
            "bot_id": BOT_ID,
            "text": text
        }
    )

# -----------------------------
# Warning System
# -----------------------------
def add_warning(name):
    if name not in warnings:
        warnings[name] = 0

    warnings[name] += 1

    if warnings[name] == 2:
        send_message(f"{name}, this is your second warning.")

    elif warnings[name] >= 3:
        send_message(
            f"{name} has received 3 warnings. Leadership should review them."
        )

# -----------------------------
# Webhook
# -----------------------------
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if not data:
        return "ok", 200

    # Ignore bot messages
    if data.get("sender_type") == "bot":
        return "ok", 200

    message = data.get("text", "").lower().strip()
    name = data.get("name", "Unknown")
    user_id = data.get("user_id")

    now = time()

    # -----------------------------
    # Commands
    # -----------------------------
    if message == "/rules":
        send_message(RULES)

    elif message == "hello":
        send_message("Shut up, Niko")

    elif message == "/warnings":
        count = warnings.get(name, 0)
        send_message(f"{name}, you currently have {count} warnings.")

    # -----------------------------
    # Funny Niko Response
    # -----------------------------
    if name.lower() == TARGET_NAME.lower():
        send_message("Shut up, Niko")

    # -----------------------------
    # Profanity Filter
    # -----------------------------
    for word in BANNED_WORDS:
        if word in message:
            send_message(
                f"{name}, please watch your language and follow the rules."
            )

            add_warning(name)
            break

    # -----------------------------
    # Spam Detection
    # -----------------------------
    if user_id:

        if user_id not in user_activity:
            user_activity[user_id] = []

        # Keep recent messages only
        user_activity[user_id] = [
            t for t in user_activity[user_id]
            if now - t < SPAM_WINDOW
        ]

        user_activity[user_id].append(now)

        if len(user_activity[user_id]) > SPAM_LIMIT:
            send_message(
                f"{name}, stop spamming the chat."
            )

            add_warning(name)

            return "ok", 200

    # -----------------------------
    # Quiet Hours Warning
    # -----------------------------
    hour = datetime.now().hour

    if hour >= 22 or hour < 5:
        send_message(
            "Reminder: Please avoid messaging between 10 PM and 5 AM unless important."
        )

    return "ok", 200

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
