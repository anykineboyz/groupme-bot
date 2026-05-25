from flask import Flask, request
import requests
from time import time
from datetime import datetime
from zoneinfo import ZoneInfo
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
niko_message_count = {}

last_quiet_warning = 0
QUIET_WARNING_COOLDOWN = 1800

BANNED_WORDS = [
    "fuck",
    "bitch",
    "mom",
    "dad",
    "die",
    "kill",
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
    global last_quiet_warning

    data = request.json

    if not data:
        return "ok", 200

    if data.get("sender_type") == "bot":
        return "ok", 200

    message = data.get("text", "").lower().strip()
    name = data.get("name", "Unknown")
    name_lower = name.lower()
    user_id = data.get("user_id")

    now = time()

    # -------------------------
    # COMMANDS
    # -------------------------
    if message == "/rules":
        send_message(RULES)

    elif message == "hello":
        send_message(f"Hi {name}!")

    elif message == "stop":
        send_message(f"Remember Niko, STOP means STOP. So do not send another message, or you will receive a warning and eventually be kicked.")

    elif message == "/warnings":
        send_message(f"{name}, you have {warnings.get(name, 0)} warnings.")

    elif "boss" in message:
        send_message("Good boy, Niko!")

    # -------------------------
    # NIKO MESSAGE COUNTER
    # -------------------------
    if "niko" in name_lower:
        niko_message_count[name] = niko_message_count.get(name, 0) + 1

        if niko_message_count[name] % 4 == 0:
            send_message("Niko, be considerate of others and try not to chat too much.")

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
    hour = datetime.now(ZoneInfo("Pacific/Honolulu")).hour

    if (
        (hour >= 22 or hour < 5)
        and now - last_quiet_warning > QUIET_WARNING_COOLDOWN
    ):
        send_message("Reminder: Please avoid messaging between 10 PM and 5 AM.")
        last_quiet_warning = now

    return "ok", 200

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
